"""
Tests for the service layer.

Notice: no boto3, no mocking library, no AWS credentials needed anywhere
here. MockPatchSource and InMemoryRepository are real objects that
happen to satisfy the PatchDataSource/PatchRepository Protocols — that's
the entire benefit of designing services against abstractions.
"""

from patch_domain.services import PatchAuditService, ComplianceQueryService
from patch_domain.sources.mock_source import MockPatchSource
from patch_domain.repositories.in_memory_repository import InMemoryRepository


def test_run_scan_persists_all_instances():
    source = MockPatchSource(fleet_size=10, seed=1)
    repository = InMemoryRepository()
    service = PatchAuditService(source, repository)

    count = service.run_scan()

    assert count == 10
    assert len(repository.get_latest_states()) == 10


def test_run_scan_persists_patch_detail_per_instance():
    source = MockPatchSource(fleet_size=3, seed=2)
    repository = InMemoryRepository()
    service = PatchAuditService(source, repository)

    service.run_scan()

    states = repository.get_latest_states()
    first_instance_id = states[0].instance_id
    patches = repository.get_patches_for_instance(first_instance_id)

    assert len(patches) > 0
    assert all(p.instance_id == first_instance_id for p in patches)


def test_compliance_query_service_reads_through_repository():
    source = MockPatchSource(fleet_size=5, seed=3)
    repository = InMemoryRepository()
    PatchAuditService(source, repository).run_scan()

    query_service = ComplianceQueryService(repository)
    overview = query_service.get_fleet_overview()

    assert len(overview) == 5
    assert all(state.compliance_status in ("COMPLIANT", "NON_COMPLIANT", "UNSPECIFIED_DATA") for state in overview)


def test_instance_detail_returns_empty_for_unknown_instance():
    repository = InMemoryRepository()
    query_service = ComplianceQueryService(repository)

    assert query_service.get_instance_detail("i-doesnotexist") == []


class _FakeFailingSource:
    """
    A minimal test double satisfying PatchDataSource structurally —
    no inheritance from anything, just matching method signatures.
    Used to prove the service layer doesn't silently swallow errors.
    """

    def list_instance_patch_states(self):
        raise RuntimeError("simulated source failure")

    def list_instance_patches(self, instance_id: str):
        return []


def test_run_scan_propagates_source_errors():
    service = PatchAuditService(_FakeFailingSource(), InMemoryRepository())

    try:
        service.run_scan()
        assert False, "expected RuntimeError to propagate"
    except RuntimeError as e:
        assert "simulated source failure" in str(e)
