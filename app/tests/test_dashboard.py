"""
Smoke test for app/dashboard.py.

Streamlit scripts execute top-to-bottom on import/run — there's no
natural seam to unit test UI rendering in isolation, and that's fine:
by design, dashboard.py stays thin (composition root + UI calls only).
All the actual business logic it depends on (PatchAuditService,
ComplianceQueryService, MockPatchSource, InMemoryRepository) is already
covered by common/tests — that's the point of pushing logic out of the
UI layer and into patch_domain.

This test just proves the composition root wires correctly end-to-end
by stubbing out streamlit's API surface, without needing streamlit
installed or a real browser session.
"""

import os
import sys
import types
from pathlib import Path

os.environ["USE_MOCK_DATA"] = "true"


def _install_streamlit_stub():
    st = types.ModuleType("streamlit")

    class _Column:
        def metric(self, *a, **k):
            pass

        def multiselect(self, *a, **k):
            return []

    def _columns(n):
        return [_Column() for _ in range(n)]

    def _cache_resource(fn):
        return fn  # no-op — just call the function directly in tests

    st.set_page_config = lambda **k: None
    st.title = lambda *a, **k: None
    st.warning = lambda *a, **k: None
    st.stop = lambda: (_ for _ in ()).throw(SystemExit)  # mimic st.stop() halting the script
    st.divider = lambda: None
    st.subheader = lambda *a, **k: None
    st.dataframe = lambda *a, **k: None
    st.bar_chart = lambda *a, **k: None
    st.selectbox = lambda *a, **k: None
    st.info = lambda *a, **k: None
    st.multiselect = lambda *a, **k: []
    st.columns = _columns
    st.cache_resource = _cache_resource

    sys.modules["streamlit"] = st


def _install_boto3_stub_if_missing():
    # This repo's CI/production environment has real boto3 installed via
    # requirements.txt. This stub only exists so the test can still prove
    # the wiring logic in offline/sandboxed environments without network
    # access to pip install it — dynamodb_repository.py is imported even
    # in USE_MOCK_DATA mode (it's just never called), so the import must
    # succeed either way.
    try:
        import boto3  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.__path__ = []
    fake_boto3.client = lambda *a, **k: None
    fake_boto3.resource = lambda *a, **k: types.SimpleNamespace(Table=lambda name: None)
    sys.modules["boto3"] = fake_boto3

    fake_dynamodb = types.ModuleType("boto3.dynamodb")
    fake_dynamodb.__path__ = []
    sys.modules["boto3.dynamodb"] = fake_dynamodb

    fake_conditions = types.ModuleType("boto3.dynamodb.conditions")
    fake_conditions.Key = lambda *a, **k: None
    sys.modules["boto3.dynamodb.conditions"] = fake_conditions


def test_dashboard_wiring_uses_mock_data_and_populates_repository():
    _install_streamlit_stub()
    _install_boto3_stub_if_missing()

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "common"))

    import dashboard  # executes the script with streamlit stubbed out

    states = dashboard.query_service.get_fleet_overview()
    assert len(states) == 25  # MockPatchSource default fleet_size
