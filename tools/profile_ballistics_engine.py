#!/usr/bin/env python3
"""Simple timing harness for BallisticsEngine.calculate_load.

Uses existing DB data to pick rifle/bullet/powder ids and runs a fixed number
of calculations to report timing stats.
"""

from __future__ import annotations

import argparse
import statistics
import time
from typing import Iterable, Optional

from src.modules.ballistics_engine import BallisticsEngine


def _pick_id(cur, table: str, id_value: Optional[int]) -> Optional[int]:
    if id_value is not None:
        return int(id_value)
    cur.execute(f"SELECT id FROM {table} ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if not row:
        return None
    try:
        return int(row[0])
    except Exception:
        return None


def _charges(min_charge: float, max_charge: float, count: int) -> Iterable[float]:
    if count <= 1:
        return [min_charge]
    step = (max_charge - min_charge) / (count - 1)
    return [min_charge + i * step for i in range(count)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Profile BallisticsEngine speed")
    parser.add_argument("--rifle-id", type=int, default=None)
    parser.add_argument("--bullet-id", type=int, default=None)
    parser.add_argument("--powder-id", type=int, default=None)
    parser.add_argument("--iterations", type=int, default=200)
    parser.add_argument("--warmup", type=int, default=5)
    parser.add_argument("--min-charge", type=float, default=40.0)
    parser.add_argument("--max-charge", type=float, default=45.0)
    parser.add_argument("--coal-mm", type=float, default=71.5)
    parser.add_argument("--cbto-mm", type=float, default=0.0)
    parser.add_argument("--temp-c", type=float, default=20.0)
    args = parser.parse_args()

    engine = BallisticsEngine()
    cur = engine.db.cursor

    rifle_id = _pick_id(cur, "rifles", args.rifle_id)
    bullet_id = _pick_id(cur, "bullets", args.bullet_id)
    powder_id = _pick_id(cur, "powder", args.powder_id)

    if rifle_id is None or bullet_id is None or powder_id is None:
        print("Missing data: ensure rifles, bullets, and powder tables have rows.")
        return 2

    charges = list(_charges(args.min_charge, args.max_charge, args.iterations))

    for _ in range(max(args.warmup, 0)):
        engine.calculate_load(
            rifle_id,
            bullet_id,
            powder_id,
            charges[0],
            args.coal_mm,
            args.cbto_mm if args.cbto_mm else None,
            args.temp_c,
        )

    durations = []
    errors = 0
    for charge in charges:
        start = time.perf_counter()
        result = engine.calculate_load(
            rifle_id,
            bullet_id,
            powder_id,
            float(charge),
            args.coal_mm,
            args.cbto_mm if args.cbto_mm else None,
            args.temp_c,
        )
        end = time.perf_counter()
        durations.append(end - start)
        if isinstance(result, dict) and result.get("error"):
            errors += 1

    durations.sort()
    count = len(durations)
    avg_ms = statistics.mean(durations) * 1000
    med_ms = statistics.median(durations) * 1000
    p95_ms = durations[int(0.95 * (count - 1))] * 1000 if count else 0.0
    min_ms = durations[0] * 1000 if count else 0.0
    max_ms = durations[-1] * 1000 if count else 0.0

    print("BallisticsEngine.calculate_load profile")
    print(f"  samples: {count} (errors: {errors})")
    print(f"  avg ms : {avg_ms:.3f}")
    print(f"  med ms : {med_ms:.3f}")
    print(f"  p95 ms : {p95_ms:.3f}")
    print(f"  min ms : {min_ms:.3f}")
    print(f"  max ms : {max_ms:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
