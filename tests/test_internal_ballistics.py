from src.utils.internal_ballistics import (
    build_internal_ballistics_summary,
    estimate_burn_completeness,
    format_internal_ballistics_text,
)


def test_build_internal_ballistics_summary_flags_low_fill():
    summary = build_internal_ballistics_summary(
        charge_weight_gr=38.0,
        powder_name="H4350",
        case_capacity_gr_h2o=65.0,
        barrel_length_in=18.0,
    )

    assert summary["level"] == "warning"
    assert any(metric["name"] == "Fyllrate" for metric in summary["metrics"])
    assert any("Lav fyllrate" in check for check in summary["checks"])


def test_build_internal_ballistics_summary_flags_compressed_load():
    summary = build_internal_ballistics_summary(
        load_density_percent=109.5,
        case_capacity_ml=3.50,
        powder_density_g_ml=0.92,
        barrel_length_in=24.0,
        burn_rate_position="slow",
    )

    assert summary["level"] == "critical"
    assert summary["compression_ratio"] is not None
    assert any("komprimert" in check.lower() for check in summary["checks"])
    assert any(metric["name"] == "Krutttetthet" for metric in summary["metrics"])


def test_estimate_burn_completeness_rewards_longer_balanced_setup():
    short_slow = estimate_burn_completeness(
        barrel_length_in=18.0,
        load_density_percent=82.0,
        burn_rate_position="slow",
    )
    long_balanced = estimate_burn_completeness(
        barrel_length_in=24.0,
        load_density_percent=96.0,
        burn_rate_position="medium",
    )

    assert short_slow is not None
    assert long_balanced is not None
    assert long_balanced > short_slow


def test_format_internal_ballistics_text_includes_metrics():
    summary = build_internal_ballistics_summary(
        load_density_percent=97.5,
        case_capacity_ml=3.4,
        powder_density_g_ml=0.91,
        barrel_length_in=24.0,
        burn_rate_position="medium",
    )

    lines = format_internal_ballistics_text(summary)

    assert lines
    assert lines[0] == "Internballistikk"
    assert any("Fyllrate:" in line for line in lines)
