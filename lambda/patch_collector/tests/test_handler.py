"""
Tests for the Lambda composition root.

Two different techniques are used here, deliberately:
1. Testing _build_service() picks the right concrete source class based
   on env vars — this checks the WIRING logic itself.
2. Testing lambda_handler()'s behavior by monkeypatching the module-level
   _service with a fake — this checks the HANDLER logic without needing
   _build_service to have wired anything real.

Note: 'lambda' is a Python keyword, so this directory can't be imported
as a dotted package (`import lambda.patch_collector.handler` is invalid
syntax). That mirrors how AWS actually invokes it too — the deployment
zip's root is added to sys.path and `handler.lambda_handler` is called
directly, not through a package path. Tests replicate that by adding
patch_collector/ to sys.path and importing `handler` as a top-level module.
"""

import os
import sys
from pathlib import Path

# Ensure required env vars exist BEFORE handler.py is imported, since its
# composition root wiring runs once at module import time (cold start).
os.environ.setdefault("TABLE_NAME", "test-table")
os.environ.setdefault("USE_MOCK_DATA", "true")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import handler  # noqa: E402
from patch_domain.sources.mock_source import MockPatchSource  # noqa: E402


def test_build_service_uses_mock_source_when_env_var_set():
    os.environ["USE_MOCK_DATA"] = "true"
    service = handler._build_service()
    assert isinstance(service._source, MockPatchSource)


class _FakeService:
    def __init__(self, count):
        self._count = count
        self.called = False

    def run_scan(self):
        self.called = True
        return self._count


def test_lambda_handler_returns_200_and_count(monkeypatch):
    fake_service = _FakeService(count=12)
    monkeypatch.setattr(handler, "_service", fake_service)

    response = handler.lambda_handler({}, None)

    assert fake_service.called is True
    assert response["statusCode"] == 200
    assert "12" in response["body"]


def test_lambda_handler_propagates_exceptions(monkeypatch):
    class _FailingService:
        def run_scan(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(handler, "_service", _FailingService())

    try:
        handler.lambda_handler({}, None)
        assert False, "expected exception to propagate"
    except RuntimeError as e:
        assert "boom" in str(e)
