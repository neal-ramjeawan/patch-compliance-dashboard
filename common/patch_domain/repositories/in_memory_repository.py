"""
In-memory PatchRepository — no AWS dependency at all.

Used for: local development against mock data, and unit tests where we
want to assert on service behavior without touching DynamoDB or even
mocking boto3. This is the payoff of designing to PatchRepository as a
Protocol — this class doesn't inherit from anything, it just has the
right shape.
"""

from patch_domain.models import InstancePatchState, InstancePatch


class InMemoryRepository:
    def __init__(self):
        self._latest_states: dict[str, InstancePatchState] = {}
        self._patches: dict[str, list[InstancePatch]] = {}

    def save_scan(
        self,
        states: list[InstancePatchState],
        patches_by_instance: dict[str, list[InstancePatch]],
    ) -> None:
        for state in states:
            self._latest_states[state.instance_id] = state
        for instance_id, patches in patches_by_instance.items():
            self._patches[instance_id] = patches

    def get_latest_states(self) -> list[InstancePatchState]:
        return list(self._latest_states.values())

    def get_patches_for_instance(self, instance_id: str) -> list[InstancePatch]:
        return self._patches.get(instance_id, [])
