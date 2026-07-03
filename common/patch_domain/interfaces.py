"""
Abstractions every concrete source/repository implements.

Using typing.Protocol rather than ABC: implementations don't need to
inherit from anything, which makes it trivial to hand a plain test
double to a service in unit tests without any inheritance boilerplate.
Structural typing also matches how services actually consume these —
by shape, not by identity.
"""

from typing import Protocol

from patch_domain.models import InstancePatchState, InstancePatch


class PatchDataSource(Protocol):
    """Anything that can report current patch state for a fleet of instances."""

    def list_instance_patch_states(self) -> list[InstancePatchState]:
        """One summary row per instance — fleet-wide compliance view."""
        ...

    def list_instance_patches(self, instance_id: str) -> list[InstancePatch]:
        """Per-patch detail for one instance — drill-down view."""
        ...


class PatchRepository(Protocol):
    """Anything that can persist and retrieve scan results."""

    def save_scan(
        self,
        states: list[InstancePatchState],
        patches_by_instance: dict[str, list[InstancePatch]],
    ) -> None:
        ...

    def get_latest_states(self) -> list[InstancePatchState]:
        ...

    def get_patches_for_instance(self, instance_id: str) -> list[InstancePatch]:
        ...
