"""
Business logic layer. Depends only on PatchDataSource and PatchRepository
(both Protocols) — never on a concrete source or repository class. Which
concrete implementations get used is decided entirely by the composition
root (lambda/handler.py or app/dashboard.py), not by this class.
"""

from patch_domain.interfaces import PatchDataSource, PatchRepository


class PatchAuditService:
    def __init__(self, source: PatchDataSource, repository: PatchRepository):
        self._source = source
        self._repository = repository

    def run_scan(self) -> int:
        """Pull current fleet state from the source and persist it. Returns instance count."""
        states = self._source.list_instance_patch_states()
        patches_by_instance = {
            state.instance_id: self._source.list_instance_patches(state.instance_id)
            for state in states
        }
        self._repository.save_scan(states, patches_by_instance)
        return len(states)


class ComplianceQueryService:
    """Read-side service used by the dashboard. Depends only on PatchRepository."""

    def __init__(self, repository: PatchRepository):
        self._repository = repository

    def get_fleet_overview(self) -> list:
        return self._repository.get_latest_states()

    def get_instance_detail(self, instance_id: str) -> list:
        return self._repository.get_patches_for_instance(instance_id)
