"""
Generates mock patch compliance data shaped like AWS SSM Patch Manager's
API responses. Implements PatchDataSource structurally — no inheritance
needed, since PatchDataSource is a Protocol.
"""

import random
from datetime import datetime, timedelta, timezone

from patch_domain.models import InstancePatchState, InstancePatch

PLATFORMS = ["AmazonLinux2", "Ubuntu", "RHEL", "Windows"]
PATCH_GROUPS = ["webservers", "app-tier", "db-tier", "bastion"]

LINUX_CLASSIFICATIONS = ["Security", "Bugfix", "Enhancement", "CriticalUpdate"]
WINDOWS_CLASSIFICATIONS = ["CriticalUpdates", "SecurityUpdates", "UpdateRollups", "Updates"]
SEVERITIES = ["Critical", "Important", "Medium", "Low"]

LINUX_PACKAGES = ["openssl", "kernel", "glibc", "curl", "openssh-server", "sudo", "python3", "systemd"]
WINDOWS_KBS = ["KB5034123", "KB5033118", "KB5030310", "KB5032190", "KB5031354"]


def _random_instance_ids(n: int) -> list[str]:
    return [f"i-{random.getrandbits(48):012x}" for _ in range(n)]


class MockPatchSource:
    """Simulates a fleet of EC2 instances with varying patch compliance."""

    def __init__(self, fleet_size: int = 25, seed: int = 42):
        random.seed(seed)
        self.instance_ids = _random_instance_ids(fleet_size)
        self.instance_meta = {
            iid: {
                "platform": random.choice(PLATFORMS),
                "patch_group": random.choice(PATCH_GROUPS),
            }
            for iid in self.instance_ids
        }

    def list_instance_patch_states(self) -> list[InstancePatchState]:
        now = datetime.now(timezone.utc)
        states = []
        for iid in self.instance_ids:
            meta = self.instance_meta[iid]
            platform = meta["platform"]

            missing = random.choices(
                [0, random.randint(1, 3), random.randint(4, 15)],
                weights=[0.55, 0.30, 0.15],
            )[0]
            installed = random.randint(80, 250)
            failed = 1 if random.random() < 0.05 else 0

            critical_missing = min(missing, random.randint(0, 2)) if missing else 0
            security_missing = min(missing, random.randint(0, missing)) if missing else 0

            if missing == 0 and failed == 0:
                compliance = "COMPLIANT"
            elif missing > 0:
                compliance = "NON_COMPLIANT"
            else:
                compliance = "UNSPECIFIED_DATA"

            scan_time = now - timedelta(days=random.randint(0, 10), hours=random.randint(0, 23))

            states.append(
                InstancePatchState(
                    instance_id=iid,
                    scan_time=scan_time.isoformat(),
                    platform=platform,
                    patch_group=meta["patch_group"],
                    baseline_id=f"pb-{'windows' if platform == 'Windows' else 'linux'}-default",
                    compliance_status=compliance,
                    installed_count=installed,
                    missing_count=missing,
                    failed_count=failed,
                    critical_non_compliant_count=critical_missing,
                    security_non_compliant_count=security_missing,
                    reboot_required=missing > 0 and random.random() < 0.4,
                    operation_type="Scan",
                )
            )
        return states

    def list_instance_patches(self, instance_id: str) -> list[InstancePatch]:
        if instance_id not in self.instance_meta:
            return []

        meta = self.instance_meta[instance_id]
        platform = meta["platform"]
        is_windows = platform == "Windows"
        now = datetime.now(timezone.utc).isoformat()

        pool = WINDOWS_KBS if is_windows else LINUX_PACKAGES
        classifications = WINDOWS_CLASSIFICATIONS if is_windows else LINUX_CLASSIFICATIONS

        patches = []
        for item in pool:
            state = random.choices(
                ["Installed", "Missing", "NotApplicable"], weights=[0.6, 0.3, 0.1]
            )[0]
            patches.append(
                InstancePatch(
                    instance_id=instance_id,
                    scan_time=now,
                    patch_id=item if is_windows else f"{item}-{random.randint(1, 9)}.{random.randint(0, 20)}-el8",
                    title=f"{item} update" if not is_windows else f"Cumulative Update {item}",
                    classification=random.choice(classifications),
                    severity=random.choice(SEVERITIES),
                    state=state,
                    released_date=(
                        datetime.now(timezone.utc) - timedelta(days=random.randint(5, 400))
                    ).date().isoformat(),
                )
            )
        return patches
