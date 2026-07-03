"""
Real patch data source backed by AWS SSM Patch Manager.

Implements PatchDataSource structurally (Protocol, no inheritance).
Only depends on boto3 — no AWS calls happen at import time, so this
module is safe to import even without credentials configured (useful
for tests that only check wiring, not live behavior).
"""

import boto3


class SSMPatchSource:
    def __init__(self, ssm_client=None):
        # Accepting an optional pre-built client is itself a small DI seam —
        # tests can inject a stubbed boto3 client instead of hitting AWS.
        self._ssm = ssm_client or boto3.client("ssm")

    def list_instance_patch_states(self):
        from patch_domain.models import InstancePatchState

        states = []
        paginator = self._ssm.get_paginator("describe_instance_patch_states")
        for page in paginator.paginate():
            for item in page.get("InstancePatchStates", []):
                states.append(
                    InstancePatchState(
                        instance_id=item["InstanceId"],
                        scan_time=item.get("OperationEndTime", "").isoformat()
                        if hasattr(item.get("OperationEndTime", ""), "isoformat")
                        else str(item.get("OperationEndTime", "")),
                        platform=item.get("OwnerInformation", "unknown"),
                        patch_group=item.get("PatchGroup"),
                        baseline_id=item.get("BaselineId"),
                        compliance_status=(
                            "COMPLIANT"
                            if item.get("MissingCount", 0) == 0 and item.get("FailedCount", 0) == 0
                            else "NON_COMPLIANT"
                        ),
                        installed_count=item.get("InstalledCount", 0),
                        missing_count=item.get("MissingCount", 0),
                        failed_count=item.get("FailedCount", 0),
                        critical_non_compliant_count=item.get("InstalledOtherCount", 0),
                        security_non_compliant_count=item.get("InstalledPendingRebootCount", 0),
                        reboot_required=item.get("RebootOption") == "RebootIfNeeded",
                        operation_type=item.get("Operation", "Scan"),
                    )
                )
        return states

    def list_instance_patches(self, instance_id: str):
        from patch_domain.models import InstancePatch

        patches = []
        paginator = self._ssm.get_paginator("describe_instance_patches")
        for page in paginator.paginate(InstanceId=instance_id):
            for item in page.get("Patches", []):
                patches.append(
                    InstancePatch(
                        instance_id=instance_id,
                        scan_time=str(item.get("InstalledTime", "")),
                        patch_id=item.get("KBId") or item.get("Title", "unknown"),
                        title=item.get("Title", ""),
                        classification=item.get("Classification", ""),
                        severity=item.get("Severity", ""),
                        state=item.get("State", ""),
                        released_date=str(item.get("ReleaseDate", "")) or None,
                    )
                )
        return patches
