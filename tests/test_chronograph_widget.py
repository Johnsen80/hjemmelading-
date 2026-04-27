"""Tests for ChronographWidget._stats and related pure logic."""

from __future__ import annotations

import math


def test_stats_empty():
    from src.ui.chronograph_widget import _stats

    avg, sd, es, mn, mx = _stats([])
    assert avg == 0.0
    assert sd == 0.0
    assert es == 0.0


def test_stats_single():
    from src.ui.chronograph_widget import _stats

    avg, sd, es, mn, mx = _stats([2750.0])
    assert avg == 2750.0
    assert sd == 0.0
    assert es == 0.0
    assert mn == 2750.0
    assert mx == 2750.0


def test_stats_sample_sd():
    from src.ui.chronograph_widget import _stats

    # Known values: avg=10, sample sd = sqrt(sum((x-10)^2) / (n-1))
    vs = [8.0, 10.0, 12.0]
    avg, sd, es, mn, mx = _stats(vs)
    assert abs(avg - 10.0) < 0.001
    # sample sd = sqrt((4+0+4)/2) = sqrt(4) = 2.0
    assert abs(sd - 2.0) < 0.001
    assert abs(es - 4.0) < 0.001
    assert mn == 8.0
    assert mx == 12.0


def test_stats_two_values():
    from src.ui.chronograph_widget import _stats

    vs = [2700.0, 2800.0]
    avg, sd, es, mn, mx = _stats(vs)
    assert abs(avg - 2750.0) < 0.001
    # sample sd of two values = |a-b| / sqrt(2)
    assert abs(sd - 100.0 / math.sqrt(2)) < 0.01
    assert abs(es - 100.0) < 0.001


def test_stats_es_and_extremes():
    from src.ui.chronograph_widget import _stats

    vs = [2650.0, 2700.0, 2750.0, 2800.0, 2850.0]
    avg, sd, es, mn, mx = _stats(vs)
    assert abs(avg - 2750.0) < 0.001
    assert abs(es - 200.0) < 0.001
    assert mn == 2650.0
    assert mx == 2850.0
    assert sd > 0.0


def test_stats_uses_sample_not_population_sd():
    """Verify denominator is n-1, not n."""
    from src.ui.chronograph_widget import _stats

    # 5 values: avg=0, deviations: -2,-1,0,1,2
    vs = [-2.0, -1.0, 0.0, 1.0, 2.0]
    avg, sd, *_ = _stats(vs)
    assert abs(avg - 0.0) < 0.001
    # population sd = sqrt(10/5) = sqrt(2) ≈ 1.414
    # sample sd    = sqrt(10/4) = sqrt(2.5) ≈ 1.581
    assert abs(sd - math.sqrt(2.5)) < 0.001
    assert abs(sd - math.sqrt(2.0)) > 0.01  # NOT population sd


def test_stats_real_chrono_data():
    from src.ui.chronograph_widget import _stats

    vs = [2743.0, 2751.0, 2748.0, 2755.0, 2746.0]
    avg, sd, es, mn, mx = _stats(vs)
    assert abs(avg - sum(vs) / len(vs)) < 0.01
    assert mn == 2743.0
    assert mx == 2755.0
    assert abs(es - 12.0) < 0.001
    assert 3.0 < sd < 6.0  # typical ES/4 range
