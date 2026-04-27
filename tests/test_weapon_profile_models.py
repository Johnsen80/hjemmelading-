import pytest

from src.modules.weapon_profile import Barrel, CaseMeasurements, WeaponProfile


@pytest.mark.core
def test_weapon_profile_roundtrip_preserves_barrel_specific_data():
    profile = WeaponProfile(
        id="wp-1",
        name="Tikka platform",
        weapon_type="rifle",
        preferred_units="imperial",
        caliber=".308 Win",
        active_barrel_id="b-2",
        barrels=[
            Barrel(
                id="b-1",
                name="Training barrel",
                caliber=".308 Win",
                barrel_attachment_type="threaded",
                barrel_profile="medium",
                usage_type="training",
                barrel_torque_nm=8.5,
                barrel_return_to_zero="stable",
                muzzle_device_type="suppressor",
                muzzle_device_model="Ase Utra",
                muzzle_device_weight_g=520.0,
                muzzle_device_length_mm=182.0,
                case_measurements=CaseMeasurements(
                    standard="SAAMI",
                    trim_length_mm=51.05,
                    h2o_capacity_grains=56.2,
                    h2o_measurements=[
                        {
                            "dry_weight_gr": 171.4,
                            "wet_weight_gr": 227.6,
                            "h2o_capacity_grains": 56.2,
                        },
                        {
                            "dry_weight_gr": 171.3,
                            "wet_weight_gr": 227.4,
                            "h2o_capacity_grains": 56.1,
                        },
                    ],
                ),
            ),
            Barrel(
                id="b-2",
                name="Match barrel",
                caliber="6.5 Creedmoor",
                barrel_attachment_type="quick_change",
                barrel_profile="heavy",
                usage_type="competition",
                status="active",
                twist="1:8",
                action_stiffness="rigid",
                barrel_return_to_zero="verify after swap",
                case_measurements=CaseMeasurements(
                    standard="CIP",
                    shoulder_bump_in=0.002,
                    neck_diameter_mm=7.62,
                ),
            ),
        ],
    )

    raw = profile.to_dict()
    restored = WeaponProfile.from_dict(raw)

    assert restored.weapon_type == "rifle"
    assert restored.preferred_units == "imperial"
    assert restored.get_active_barrel() is not None
    assert restored.get_active_barrel().id == "b-2"
    assert restored.barrels[0].muzzle_device_model == "Ase Utra"
    assert restored.barrels[0].barrel_attachment_type == "threaded"
    assert restored.barrels[0].barrel_profile == "medium"
    assert restored.barrels[0].barrel_torque_nm == 8.5
    assert restored.barrels[0].case_measurements.h2o_capacity_grains == 56.2
    assert len(restored.barrels[0].case_measurements.h2o_measurements) == 2
    assert (
        restored.barrels[0].case_measurements.h2o_measurements[0]["dry_weight_gr"]
        == 171.4
    )
    assert restored.barrels[1].barrel_attachment_type == "quick_change"
    assert restored.barrels[1].barrel_profile == "heavy"
    assert restored.barrels[1].barrel_return_to_zero == "verify after swap"
    assert restored.barrels[1].case_measurements.shoulder_bump_in == 0.002


@pytest.mark.core
def test_weapon_profile_from_dict_is_backward_compatible():
    restored = WeaponProfile.from_dict(
        {
            "id": "legacy",
            "name": "Legacy profile",
            "caliber": "9x19",
            "barrels": [{"id": "b-1", "name": "Factory barrel"}],
        }
    )

    assert restored.weapon_type == "rifle"
    assert restored.preferred_units == "metric"
    assert restored.barrels[0].usage_type == "general"
    assert restored.barrels[0].case_measurements.h2o_capacity_grains is None


@pytest.mark.core
def test_weapon_profile_barrel_attachment_fields_are_backward_compatible():
    restored = WeaponProfile.from_dict(
        {
            "id": "legacy-2",
            "name": "Legacy attachment profile",
            "barrels": [
                {"id": "b-1", "name": "Factory barrel", "mount_type": "threaded"}
            ],
        }
    )

    assert restored.barrels[0].barrel_attachment_type is None
    assert restored.barrels[0].barrel_torque_nm is None
    assert restored.barrels[0].barrel_return_to_zero is None
