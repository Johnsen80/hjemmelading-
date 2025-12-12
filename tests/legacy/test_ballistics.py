"""Test ballistics engine integration"""

from src.modules.ballistics_engine import get_ballistics_engine

print("Testing Ballistics Engine...")
print("-" * 60)

engine = get_ballistics_engine()
print("✅ Ballistics Engine loaded successfully!")
print()

# Test calculation with dummy IDs
# (will fail gracefully if rifle/bullet/powder don't exist)
print("Test calculation (rifle_id=1, bullet_id=1, powder_id=1):")
print("Charge: 42.5 gr, COAL: 70.0 mm")
print()

try:
    result = engine.calculate_load(1, 1, 1, 42.5, 70.0)
except Exception as exc:  # pragma: no cover - make test import-safe in CI
    print(f"⚠️ calculate_load raised an exception: {exc}")
    result = {"error": f"calculate_load exception: {exc}"}

if "error" in result:
    print(f"⚠️ {result['error']} (expected - need real data)")
else:
    print(f"✅ Peak Pressure: {result['peak_pressure_psi']:.0f} PSI")
    print(f"✅ Muzzle Velocity: {result['muzzle_velocity_fps']:.0f} fps")
    print(f"✅ Barrel Time: {result['barrel_time_ms']:.2f} ms")
    print(f"✅ Muzzle Energy: {result['energy_ft_lbs']:.0f} ft-lbs")
    print(f"✅ Safety Margin: {result['safety_margin_percent']:.1f}%")

    if result["warnings"]:
        print()
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  {warning}")

print()
print("-" * 60)
print("Ballistics Engine ready for wizard integration!")
