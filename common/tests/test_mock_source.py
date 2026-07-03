from patch_domain.sources.mock_source import MockPatchSource


def test_fleet_size_is_respected():
    source = MockPatchSource(fleet_size=15, seed=42)
    states = source.list_instance_patch_states()
    assert len(states) == 15


def test_same_seed_produces_deterministic_fleet():
    source_a = MockPatchSource(fleet_size=5, seed=99)
    source_b = MockPatchSource(fleet_size=5, seed=99)

    ids_a = sorted(source_a.instance_ids)
    ids_b = sorted(source_b.instance_ids)
    assert ids_a == ids_b


def test_compliant_instances_have_zero_missing_and_no_failures():
    source = MockPatchSource(fleet_size=30, seed=7)
    for state in source.list_instance_patch_states():
        if state.compliance_status == "COMPLIANT":
            assert state.missing_count == 0
            assert state.failed_count == 0


def test_non_compliant_instances_have_missing_patches():
    source = MockPatchSource(fleet_size=30, seed=7)
    for state in source.list_instance_patch_states():
        if state.compliance_status == "NON_COMPLIANT":
            assert state.missing_count > 0


def test_patches_for_unknown_instance_returns_empty():
    source = MockPatchSource(fleet_size=5, seed=1)
    assert source.list_instance_patches("i-doesnotexist") == []


def test_patches_for_known_instance_returns_data():
    source = MockPatchSource(fleet_size=5, seed=1)
    instance_id = source.instance_ids[0]
    patches = source.list_instance_patches(instance_id)

    assert len(patches) > 0
    assert all(p.instance_id == instance_id for p in patches)
    assert all(p.state in ("Installed", "Missing", "NotApplicable") for p in patches)


def test_windows_instances_get_kb_style_patch_ids():
    source = MockPatchSource(fleet_size=30, seed=7)
    windows_ids = [
        iid for iid, meta in source.instance_meta.items() if meta["platform"] == "Windows"
    ]
    assert windows_ids, "expected at least one Windows instance with seed=7, fleet_size=30"

    patches = source.list_instance_patches(windows_ids[0])
    assert all(p.patch_id.startswith("KB") for p in patches)
