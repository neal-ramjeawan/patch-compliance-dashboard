"""
Domain models shared by every implementation (mock, SSM, DynamoDB, in-memory).

Shaped to match AWS SSM Patch Manager's DescribeInstancePatchStates /
DescribeInstancePatches API responses, so a real SSMPatchSource requires
no changes here — only a new class implementing PatchDataSource.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass(frozen=True)
class InstancePatchState:
    instance_id: str
    scan_time: str
    platform: str
    patch_group: Optional[str]
    baseline_id: Optional[str]
    compliance_status: str          # COMPLIANT | NON_COMPLIANT | UNSPECIFIED_DATA
    installed_count: int
    missing_count: int
    failed_count: int
    critical_non_compliant_count: int
    security_non_compliant_count: int
    reboot_required: bool
    operation_type: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class InstancePatch:
    instance_id: str
    scan_time: str
    patch_id: str
    title: str
    classification: str
    severity: str
    state: str                       # Installed | Missing | NotApplicable | Failed
    released_date: Optional[str]

    def to_dict(self) -> dict:
        return asdict(self)
