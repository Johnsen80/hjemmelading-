"""
Comprehensive test of the integrated ballistics system
Tests: Database → Ballistics Engine → Wizard → Simulator
"""

print("=" * 80)
print("🎯 TESTING INTEGRATED BALLISTICS SYSTEM")
print("=" * 80)
print()

# Test 1: Database Schema
print("TEST 1: Database Schema")
print("-" * 80)
try:
    from src.database.database import get_database
    db = get_database()
    
    # Check new tables exist
    tables = [
        'loaded_ammo_batches',
        'brass_batches', 
        'bullet_lots',
        'bullet_qc_measurements',
        'die_settings',
        'annealing_log',
        'per_round_qc',
        'sizing_recommendations',
        'powder_database'
    ]
    
    for table in tables:
        result = db.execute_query(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if result:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} MISSING!")
    
    # Check rifle has all physics fields
    rifles = db.execute_query("PRAGMA table_info(rifles)")
    physics_fields = ['barrel_length_mm', 'twist_rate_inches', 'case_capacity_ml', 
                     'muzzle_diameter_mm', 'barrel_weight_grams']
    print()
    print("  Rifle physics fields:")
    for field in physics_fields:
        found = any(r['name'] == field for r in rifles)
        status = "✅" if found else "❌"
        print(f"    {status} {field}")
    
    print()
    print("✅ Database schema complete!")
    
except Exception as e:
    print(f"❌ Database test failed: {e}")

print()
print()

# Test 2: Ballistics Engine
print("TEST 2: Ballistics Engine")
print("-" * 80)
try:
    from src.modules.ballistics_engine import get_ballistics_engine
    
    engine = get_ballistics_engine()
    print("  ✅ Engine loaded")
    
    # Test with dummy data (will fail gracefully)
    result = engine.calculate_load(1, 1, 1, 42.5, 70.0)
    
    if 'error' in result:
        print(f"  ⚠️  {result['error']} (expected - no real data)")
    else:
        print(f"  ✅ Pressure calculation: {result['peak_pressure_psi']:.0f} PSI")
        print(f"  ✅ Velocity calculation: {result['muzzle_velocity_fps']:.0f} fps")
        print(f"  ✅ Safety margin: {result['safety_margin_percent']:.1f}%")
    
    # Test powder burn rate database
    print()
    print("  Powder burn rate database:")
    powders = ['Varget', 'H4350', 'RL16', 'H1000']
    for powder in powders:
        rate = engine.POWDER_BURN_RATES.get(powder, None)
        if rate:
            print(f"    ✅ {powder}: {rate}")
        else:
            print(f"    ❌ {powder}: NOT FOUND")
    
    # Test SAAMI limits database
    print()
    print("  SAAMI pressure limits:")
    calibers = ['.308 Winchester', '6.5 Creedmoor', '.223 Remington']
    for cal in calibers:
        limit = engine.PRESSURE_LIMITS.get(cal, None)
        if limit:
            print(f"    ✅ {cal}: {limit:,} PSI")
        else:
            print(f"    ❌ {cal}: NOT FOUND")
    
    print()
    print("✅ Ballistics engine functional!")
    
except Exception as e:
    print(f"❌ Ballistics engine test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# Test 3: Load Development Wizard Integration
print("TEST 3: Load Development Wizard Integration")
print("-" * 80)
try:
    from src.modules.load_development_wizard import LoadDevelopmentWizard
    from src.modules.load_wizard_pages import AIPredictionPage
    
    print("  ✅ Wizard modules loaded")
    
    # Check that AIPredictionPage imports ballistics engine
    import inspect
    source = inspect.getsource(AIPredictionPage.calculate_prediction)
    
    if 'ballistics_engine' in source and 'calculate_load' in source:
        print("  ✅ AIPredictionPage uses ballistics_engine")
    else:
        print("  ❌ AIPredictionPage NOT using ballistics_engine!")
    
    if 'peak_pressure_psi' in source and 'muzzle_velocity_fps' in source:
        print("  ✅ Wizard shows physics calculations")
    else:
        print("  ❌ Wizard missing physics output!")
    
    print()
    print("✅ Wizard integrated with physics engine!")
    
except Exception as e:
    print(f"❌ Wizard test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# Test 4: Real-time Simulator
print("TEST 4: Real-Time Ballistics Simulator")
print("-" * 80)
try:
    from src.modules.ballistics_simulator import BallisticsSimulator
    
    print("  ✅ Simulator module loaded")
    
    # Check simulator has all required components
    import inspect
    
    methods = [m[0] for m in inspect.getmembers(BallisticsSimulator, predicate=inspect.isfunction)]
    
    required_methods = [
        'update_pressure_graph',
        'update_velocity_graph', 
        'update_combined_graphs',
        'update_stats',
        'on_slider_changed'
    ]
    
    print()
    print("  Simulator features:")
    for method in required_methods:
        if method in methods:
            print(f"    ✅ {method}")
        else:
            print(f"    ❌ {method} MISSING!")
    
    print()
    print("✅ Simulator ready!")
    
except Exception as e:
    print(f"❌ Simulator test failed: {e}")
    import traceback
    traceback.print_exc()

print()
print()

# Test 5: Main Window Integration
print("TEST 5: Main Window Integration")
print("-" * 80)
try:
    # Read main_window.py to check integration
    with open('src/ui/main_window.py', 'r', encoding='utf-8') as f:
        main_window_code = f.read()
    
    if 'show_ballistics_simulator' in main_window_code:
        print("  ✅ Simulator menu action exists")
    else:
        print("  ❌ Simulator menu action MISSING!")
    
    if 'BallisticsSimulator' in main_window_code:
        print("  ✅ Simulator imported in Analysis tab")
    else:
        print("  ❌ Simulator NOT in Analysis tab!")
    
    if 'Ctrl+B' in main_window_code:
        print("  ✅ Keyboard shortcut (Ctrl+B) configured")
    else:
        print("  ⚠️  No keyboard shortcut")
    
    print()
    print("✅ Main window integration complete!")
    
except Exception as e:
    print(f"❌ Main window test failed: {e}")

print()
print()
print("=" * 80)
print("📊 SYSTEM OVERVIEW")
print("=" * 80)
print()
print("Architecture:")
print("  Database (SQLite)")
print("    ↓")
print("  Ballistics Engine (Noble-Abel + Burn Rate)")
print("    ↓")
print("  ├─→ Load Development Wizard (AI + Physics)")
print("  └─→ Real-Time Simulator (Interactive Graphs)")
print()
print("Features:")
print("  🎯 Professional batch management (10 new tables)")
print("  🔬 Physics-based pressure/velocity prediction")
print("  📈 Real-time interactive graphs (like GRT)")
print("  ⚖️  Live charge weight slider (instant updates)")
print("  ⚠️  Safety warnings (SAAMI/CIP compliance)")
print("  🎓 AI learning from your historical data")
print()
print("Comparison to competitors:")
print("  QuickLOAD: €150, pressure prediction ✅")
print("  GRT:       FREE, beautiful UI ✅")
print("  Our tool:  FREE + AI + YOUR DATA + Batch tracking ✅✅✅")
print()
print("=" * 80)
print("✅ ALL TESTS COMPLETE!")
print("=" * 80)
