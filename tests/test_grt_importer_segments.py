from src.modules import grt_importer as importer_module


def test_map_projectile_to_bullet_preserves_segmented_bc():
    bullet = importer_module._map_projectile_to_bullet(
        {
            "manufacturer": "Hornady",
            "name": "ELD-M",
            "caliber": ".308",
            "weight_grains": 175,
            "bc_g1": 0.62,
            "bc_g7": 0.315,
            "bc_segments_json": '[{"velocity_fps_min":2600,"velocity_fps_max":3000,"bc_g7":0.245}]',
        }
    )

    assert bullet["bc_segments_json"] == (
        '[{"model": "AUTO", "velocity_fps_min": 2600.0, "velocity_fps_max": 3000.0, '
        '"bc_g1": null, "bc_g7": 0.245, "bc": null}]'
    )


def test_map_gordon_projectile_preserves_segmented_bc():
    bullet = importer_module._map_gordon_projectile(
        {
            "manufacturer": "Hornady",
            "name": "ELD-M",
            "caliber": ".308",
            "weight": "175",
            "bc": "0.620",
            "bc7": "0.315",
            "drag_segments": '[{"velocity_fps_min":2000,"velocity_fps_max":2599,"bc_g7":0.228}]',
        }
    )

    assert bullet["bc_segments_json"] == (
        '[{"model": "AUTO", "velocity_fps_min": 2000.0, "velocity_fps_max": 2599.0, '
        '"bc_g1": null, "bc_g7": 0.228, "bc": null}]'
    )
