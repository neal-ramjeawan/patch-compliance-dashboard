"""
Streamlit dashboard — the composition root for the read/serving side.

Streamlit re-runs this entire script on every user interaction, so the
composition root is wrapped in @st.cache_resource: the wiring (which
repository implementation to use) happens once per session, not once
per click.
"""

import os

import pandas as pd
import streamlit as st

from patch_domain.services import ComplianceQueryService
from patch_domain.repositories.dynamodb_repository import DynamoDBRepository
from patch_domain.repositories.in_memory_repository import InMemoryRepository
from patch_domain.sources.mock_source import MockPatchSource
from patch_domain.services import PatchAuditService
from patch_domain.aws_clients import build_dynamodb_resource

st.set_page_config(page_title="Patch Compliance Dashboard", layout="wide")


@st.cache_resource
def get_query_service() -> ComplianceQueryService:
    use_mock = os.environ.get("USE_MOCK_DATA", "false").lower() == "true"

    if use_mock:
        # Fully offline demo mode: seed an in-memory repository from mock
        # data once, so the dashboard has something to show with zero
        # external calls of any kind.
        repository = InMemoryRepository()
        PatchAuditService(MockPatchSource(fleet_size=25), repository).run_scan()
        return ComplianceQueryService(repository)

    # Not mock — could be LocalStack, your own AWS credentials (local
    # testing), or Streamlit Community Cloud in production. Streamlit
    # secrets are optional: if they're not configured (e.g. running
    # locally against LocalStack or your own AWS profile), we fall
    # through to build_dynamodb_resource()'s other cases instead of
    # crashing on a missing secret.
    access_key_id, secret_access_key = None, None
    try:
        access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
        secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
    except Exception:
        # No secrets.toml at all, or the keys aren't set — either way, fall
        # through to build_dynamodb_resource()'s LocalStack/default-chain
        # cases below rather than crashing local/LocalStack runs.
        pass

    table_name = os.environ.get("TABLE_NAME") or (st.secrets.get("TABLE_NAME", "") if hasattr(st, "secrets") else "")
    dynamodb = build_dynamodb_resource(access_key_id, secret_access_key)
    repository = DynamoDBRepository(table_name=table_name, dynamodb_resource=dynamodb)

    return ComplianceQueryService(repository)


query_service = get_query_service()

st.title("Patch Compliance Dashboard")

states = query_service.get_fleet_overview()

if not states:
    st.warning("No scan data available yet. The collector Lambda may not have run yet.")
    st.stop()

df = pd.DataFrame([s.to_dict() for s in states])

col1, col2, col3, col4 = st.columns(4)
total = len(df)
compliant = (df["compliance_status"] == "COMPLIANT").sum()
non_compliant = (df["compliance_status"] == "NON_COMPLIANT").sum()
reboot_needed = df["reboot_required"].sum()

col1.metric("Total Instances", total)
col2.metric("Compliant", int(compliant), f"{compliant/total:.0%}")
col3.metric("Non-Compliant", int(non_compliant), f"{non_compliant/total:.0%}", delta_color="inverse")
col4.metric("Reboot Required", int(reboot_needed))

st.divider()

fcol1, fcol2, fcol3 = st.columns(3)
platform_filter = fcol1.multiselect("Platform", sorted(df["platform"].unique()))
group_filter = fcol2.multiselect("Patch Group", sorted(df["patch_group"].dropna().unique()))
status_filter = fcol3.multiselect("Compliance Status", sorted(df["compliance_status"].unique()))

filtered = df.copy()
if platform_filter:
    filtered = filtered[filtered["platform"].isin(platform_filter)]
if group_filter:
    filtered = filtered[filtered["patch_group"].isin(group_filter)]
if status_filter:
    filtered = filtered[filtered["compliance_status"].isin(status_filter)]

st.subheader("Compliance by Platform")
chart_data = filtered.groupby(["platform", "compliance_status"]).size().unstack(fill_value=0)
st.bar_chart(chart_data)

st.subheader("Instance Fleet")
display_cols = [
    "instance_id", "platform", "patch_group", "compliance_status",
    "missing_count", "critical_non_compliant_count",
    "security_non_compliant_count", "reboot_required", "scan_time",
]
st.dataframe(
    filtered[display_cols].sort_values("missing_count", ascending=False),
    width='stretch',
    hide_index=True,
)

st.subheader("Instance Detail")
selected = st.selectbox("Select an instance to see patch-level detail", filtered["instance_id"])
if selected:
    patches = query_service.get_instance_detail(selected)
    if patches:
        st.dataframe(pd.DataFrame([p.to_dict() for p in patches]), width='stretch', hide_index=True)
    else:
        st.info("No patch detail available for this instance.")
