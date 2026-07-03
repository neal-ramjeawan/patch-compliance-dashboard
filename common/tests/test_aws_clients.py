"""
Tests the branching logic in build_dynamodb_resource without ever making
a real network call — boto3.resource() just constructs a client object,
it doesn't connect until you actually call a method on it, so these
tests can inspect the constructed client's config safely.
"""

import os
import sys
import types


def _stub_boto3():
    calls = []

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.__path__ = []

    def _resource(service, **kwargs):
        calls.append(kwargs)
        return object()

    fake_boto3.resource = _resource
    sys.modules["boto3"] = fake_boto3
    return calls


def test_uses_localstack_endpoint_when_env_var_set():
    calls = _stub_boto3()
    os.environ["USE_LOCALSTACK"] = "true"
    os.environ.pop("AWS_DEFAULT_REGION", None)

    # Reimport to pick up the stubbed boto3
    sys.modules.pop("patch_domain.aws_clients", None)
    from patch_domain.aws_clients import build_dynamodb_resource

    build_dynamodb_resource()

    assert calls[-1]["endpoint_url"] == "http://localhost:4566"
    assert calls[-1]["aws_access_key_id"] == "test"

    os.environ.pop("USE_LOCALSTACK", None)


def test_uses_explicit_credentials_when_provided_and_not_localstack():
    calls = _stub_boto3()
    os.environ.pop("USE_LOCALSTACK", None)

    sys.modules.pop("patch_domain.aws_clients", None)
    from patch_domain.aws_clients import build_dynamodb_resource

    build_dynamodb_resource(access_key_id="AKIA_EXPLICIT", secret_access_key="secret")

    assert "endpoint_url" not in calls[-1]
    assert calls[-1]["aws_access_key_id"] == "AKIA_EXPLICIT"


def test_falls_back_to_default_credential_chain():
    calls = _stub_boto3()
    os.environ.pop("USE_LOCALSTACK", None)

    sys.modules.pop("patch_domain.aws_clients", None)
    from patch_domain.aws_clients import build_dynamodb_resource

    build_dynamodb_resource()

    assert "endpoint_url" not in calls[-1]
    assert "aws_access_key_id" not in calls[-1]
