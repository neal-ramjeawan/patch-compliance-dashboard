"""
Lambda entry point — the composition root for the patch collector.

This is the ONLY place in the collector that decides which concrete
PatchDataSource / PatchRepository implementations to use. Everything
downstream (PatchAuditService) only ever sees the Protocol interfaces.

Wiring happens once at module import time (Lambda cold start), then
_service is reused across warm invocations — avoids rebuilding boto3
clients on every request.
"""

import os
import logging

from patch_domain.services import PatchAuditService
from patch_domain.sources.mock_source import MockPatchSource
from patch_domain.sources.ssm_source import SSMPatchSource
from patch_domain.repositories.dynamodb_repository import DynamoDBRepository
from patch_domain.aws_clients import build_dynamodb_resource

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _build_service() -> PatchAuditService:
    use_mock = os.environ.get("USE_MOCK_DATA", "false").lower() == "true"
    table_name = os.environ["TABLE_NAME"]

    source = MockPatchSource() if use_mock else SSMPatchSource()
    repository = DynamoDBRepository(table_name=table_name, dynamodb_resource=build_dynamodb_resource())

    logger.info(
        "Wired PatchAuditService with source=%s repository=DynamoDBRepository(table=%s)",
        type(source).__name__,
        table_name,
    )
    return PatchAuditService(source, repository)


# Built once per cold start, not once per invocation.
_service = _build_service()


def lambda_handler(event, context):
    try:
        count = _service.run_scan()
        logger.info("Scan complete: %d instances processed", count)
        return {"statusCode": 200, "body": f"Scanned {count} instances"}
    except Exception:
        logger.exception("Patch scan failed")
        raise
