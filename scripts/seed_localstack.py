"""
Seeds LocalStack's DynamoDB with mock patch data — using the SAME
PatchAuditService and DynamoDBRepository code that runs in production,
just pointed at LocalStack instead of real AWS via USE_LOCALSTACK=true.

This is the actual value of LocalStack over InMemoryRepository: it
exercises the real boto3 calls, the single-table writes, and the GSI1
query in DynamoDBRepository — code paths that pure in-memory tests
never touch at all.

Usage:
    ./scripts/setup_localstack.sh   # starts LocalStack, creates the table
    python scripts/seed_localstack.py
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("USE_LOCALSTACK", "true")
os.environ.setdefault("TABLE_NAME", "patch-dashboard-patch-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "common"))

from patch_domain.services import PatchAuditService  # noqa: E402
from patch_domain.sources.mock_source import MockPatchSource  # noqa: E402
from patch_domain.repositories.dynamodb_repository import DynamoDBRepository  # noqa: E402
from patch_domain.aws_clients import build_dynamodb_resource  # noqa: E402


def main():
    table_name = os.environ["TABLE_NAME"]
    repository = DynamoDBRepository(
        table_name=table_name,
        dynamodb_resource=build_dynamodb_resource(),
    )
    service = PatchAuditService(MockPatchSource(fleet_size=25), repository)

    count = service.run_scan()
    print(f"Seeded {count} instances into LocalStack table '{table_name}'.")
    print("Run the dashboard against it with:")
    print("  USE_MOCK_DATA=false USE_LOCALSTACK=true streamlit run app/dashboard.py")


if __name__ == "__main__":
    main()
