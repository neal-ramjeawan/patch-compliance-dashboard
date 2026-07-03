"""
Centralizes how every composition root builds a boto3 DynamoDB resource,
so the LocalStack-endpoint-override logic exists in exactly one place
rather than being copy-pasted into handler.py, dashboard.py, and any
local scripts.

Three cases, in priority order:
1. USE_LOCALSTACK=true -> point at LocalStack with dummy credentials
   (LocalStack accepts any non-empty access key/secret)
2. Explicit access_key_id/secret_access_key passed in -> used directly
   (this is the Streamlit Community Cloud case, reading from st.secrets)
3. Neither -> fall back to boto3's default credential chain (AWS_PROFILE,
   ~/.aws/credentials, or an IAM role if running on AWS compute)
"""

import os
import boto3


def build_dynamodb_resource(access_key_id: str = None, secret_access_key: str = None):
    region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    if os.environ.get("USE_LOCALSTACK", "false").lower() == "true":
        return boto3.resource(
            "dynamodb",
            endpoint_url=os.environ.get("LOCALSTACK_ENDPOINT", "http://localhost:4566"),
            region_name=region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

    if access_key_id and secret_access_key:
        return boto3.resource(
            "dynamodb",
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
        )

    return boto3.resource("dynamodb", region_name=region)
