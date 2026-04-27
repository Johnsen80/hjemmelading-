from __future__ import annotations

try:
    from src.utils.i18n import tr as _tr_real

    def tr(x, **kwargs):
        return _tr_real(x, **kwargs)  # type: ignore[misc]

except Exception:

    def tr(x, **kwargs):
        return x  # type: ignore[misc]


from src.utils.unit_preferences import (
    format_distance_m,
    format_length_mm,
    format_pressure_psi,
    format_temperature_c,
    format_velocity_delta_fps,
    format_velocity_fps,
    format_velocity_rate_fps_per_c,
    format_weight_grains,
)

try:
    from src.utils.pressure_logger import predict_and_log  # type: ignore[assignment]
except Exception:

    def predict_and_log(*args, **kwargs) -> int:  # type: ignore[misc]
        return 0


try:
    from src.modules.modern_load_builder import (  # type: ignore[attr-defined]
        get_rifle_pressure_limit_psi,
    )
except Exception:

    def get_rifle_pressure_limit_psi(*args, **kwargs):  # type: ignore[misc]
        return None


try:
    from PyQt6.QtWidgets import QMessageBox
except Exception:
    pass  # type: ignore[assignment]


class _MLBHelpMixin:
    """Help and educational content methods for ModernLoadBuilder."""

    def general_help_message(self):
        """General help message showing all capabilities"""
        return """Hi! I'm your reloading expert and friendly guide. I can help with almost anything in reloading:

COMPONENTS:
• Powder: "Which powder fits best?" / "How should I store powder?"
• Bullets: "How deep should I seat the bullet?" / "What is CBTO?"
• Primers: "Standard or magnum?" / "Why is the primer flattening?"
• Brass: "When should I trim?" / "How do I anneal brass?"

DIES & PROCESS:
• "How do I set up the dies?" / "Full length or neck sizing?"
• "The case is stuck in the die" / "How do I crimp?"

TECHNICAL:
• Pressure: "Why is pressure high?" / "What are SAAMI limits?"
• Precision: "How do I improve accuracy?" / "What is ES/SD?"
• Testing: "How should I test the load?" / "What is OCW?"

Ask me anything. I'm here to help you build better loads."""

    # ==================== KRUTT / POWDER HELPERS ====================

    def explain_charge_weight(self):
        """Explain charge weight selection"""
        sample_levels = ", ".join(
            [
                format_weight_grains(42.0, "powder"),
                format_weight_grains(42.3, "powder"),
                format_weight_grains(42.5, "powder"),
                format_weight_grains(42.8, "powder"),
                format_weight_grains(43.0, "powder"),
            ]
        )
        return f"""POWDER CHARGE (Charge Weight):

HOW TO CHOOSE:
1. Start at the published minimum (-10% from max)
2. Increase gradually in {format_weight_grains(0.3, 'powder')}-{format_weight_grains(0.5, 'powder')} steps
3. Watch for pressure signs constantly

FACTORS:
• More charge = more pressure + higher velocity
• Too much = DANGEROUSLY high pressure
• Too little = poor combustion, inconsistent results

OCW METHOD (recommended):
• Test 5 levels: {sample_levels}
• Look for the "node" (stable zone)
• Choose the middle of the node for best consistency

SAFETY:
• Never exceed published maximum!
• Watch for pressure signs at every step
• When in doubt → go DOWN in charge"""

    def explain_powder_temperature(self):
        """Explain powder temperature sensitivity"""
        return f"""POWDER & TEMPERATURE:

TEMPERATURE SENSITIVITY:
• Warmer = higher pressure (about {format_velocity_rate_fps_per_c(1.0)} to {format_velocity_rate_fps_per_c(3.0)})
• Colder = lower pressure and velocity

🥇 TEMP-STABLE POWDERS (recommended):
• Hodgdon Varget (extremely stable)
• Alliant RL16 (very good)
• Hodgdon H4350 (good stability)
• Vihtavuori N140 series

TEMP-SENSITIVE:
• IMR series (especially older types)
• Ball powder (generally more sensitive)

TESTING:
• Test the load at different temperatures
• Store powder in a dry place, {format_temperature_c(10.0)}-{format_temperature_c(25.0)}
• Avoid direct sunlight on ammunition

TIP: If you hunt in both hot and cold weather, choose a temperature-stable powder!"""

    def explain_burn_rate(self):
        """Explain powder burn rate"""
        return (
            """BURN RATE:

WHAT IS IT?
How fast the powder burns inside the chamber.

FAST POWDER (e.g. Viht N130):
• Small calibers (.223, .22-250)
• Light bullets
• Short barrels
• Higher pressure, faster response

🐌 SLOW POWDER (e.g. H4831):
• Large calibers (.300 Win Mag)
• Heavy bullets
• Long barrels
• Lower pressure, more controlled burn

FOR YOUR {caliber}:
"""
            + (
                "• Burn rate 110-120 (medium)\n• Varget (115) = excellent\n• H4350 (120) = also good"
                if hasattr(self, "rifle_data")
                and self.rifle_data
                and ".308" in self.rifle_data.get("caliber", "")
                else "• Select a firearm first for specific recommendations"
            )
            + """

WRONG POWDER:
• Too fast → dangerously high pressure!
• Too slow → dirty, poor combustion

TIP: Follow published load manuals. They know which powders fit."""
        )

    def explain_powder_storage(self):
        """Explain powder storage"""
        return """POWDER STORAGE:

PROPER STORAGE:
• Original container (NEVER transfer it!)
• Dry, cool place ({format_temperature_c(10.0)}-{format_temperature_c(25.0)})
• Avoid sunlight and moisture
• Ventilated cabinet/room
• Locked away from children

NEVER:
• Mix different powder types
• Store in heat (>{format_temperature_c(30.0)})
• Store in a damp environment
• Expose to open flame

CHECK FOR DETERIORATION:
• Rust-red / brown color = DISCARD
• Sour smell (acid-like) = DISCARD
• Clumping = moisture damage, DISCARD
• Good powder: dry, loose, even color

⏳ SHELF LIFE:
• Properly stored: 10-20+ years
• Opened container: 5-10 years (if sealed well)
• Check yearly for signs of breakdown

TIP: Write the opening date on the container!"""

    # ==================== KULER / BULLETS HELPERS ====================

    def explain_seating_depth(self):
        """Explain bullet seating depth"""
        return """BULLET SEATING (Seating Depth):

IMPORTANT MEASUREMENTS:
• COAL (Cartridge Overall Length) = total length
• CBTO (Cartridge Base To Ogive) = more precise
• Jump = distance from bullet to lands

BERGER METHOD (recommended):
1. Start at "jam" (bullet touching the lands)
2. Test: 0.010", 0.050", 0.090", 0.130" jump
3. Shoot 3-shot groups for each
4. Choose the best group

EFFECTS:
• Near the lands (short jump):
  Often higher precision
  Higher pressure
• Longer jump:
  Lower pressure
  May give lower precision

SAFETY:
• Shorter COAL = MORE pressure
• Start conservatively (0.050" jump)
• Reduce powder charge if you move closer to the lands

TIP: CBTO is more consistent than COAL (bullet tips vary)"""

    def explain_bullet_jump(self):
        """Explain bullet jump to lands"""
        return """BULLET JUMP:

WHAT IS IT?
The distance the bullet travels before it touches the lands.

MEASUREMENT:
1. Close the bolt on an empty case with a bullet
2. Press the bullet gently into the lands
3. Measure CBTO = "jam length"
4. Jump = jam length - your CBTO

TYPICAL VALUES:
• 0.000" (jam) = bullet touching the lands
  HIGH PRESSURE! Testing only
• 0.010-0.020" = "touch lands"
  High precision, moderate pressure
• 0.040-0.080" = sweet spot
  Good precision, safe pressure
• 0.100"+ = long jump
  Safe, can still work well

EVERY FIREARM IS DIFFERENT:
• Some prefer short jump (0.010")
• Others prefer long jump (0.080"+)
• Test to find your firearm's preference

MAGAZINE LENGTH:
Always check that the cartridge fits the magazine!"""

    def explain_bullet_weight(self):
        """Explain bullet weight selection"""
        return """BULLET WEIGHT:

LIGHTER BULLETS (e.g. {format_weight_grains(150, 'bullet')} .308):
Higher velocity
Flatter trajectory at short range
Less recoil
More wind drift
Less energy at long range

HEAVIER BULLETS (e.g. {format_weight_grains(175, 'bullet')} .308):
Better BC (ballistic coefficient)
Less wind drift
More energy at distance
Better for long range
Lower velocity
More recoil

FOR YOUR FIREARM:
• Barrel twist: faster twist = heavier bullets
• 1:12" twist = {format_weight_grains(150, 'bullet')}-{format_weight_grains(168, 'bullet')}
• 1:10" twist = {format_weight_grains(168, 'bullet')}-{format_weight_grains(185, 'bullet')}
• 1:8" twist = {format_weight_grains(175, 'bullet')}-{format_weight_grains(200, 'bullet')}+

TIP: Start with the "standard" weight for the caliber:
• .308 Win → {format_weight_grains(168, 'bullet')}-{format_weight_grains(175, 'bullet')}
• 6.5 CM → {format_weight_grains(140, 'bullet')}-{format_weight_grains(147, 'bullet')}
• .223 Rem → {format_weight_grains(55, 'bullet')}-{format_weight_grains(77, 'bullet')}"""

    def explain_bc(self):
        """Explain ballistic coefficient"""
        return """BALLISTIC COEFFICIENT (BC):

WHAT IS IT?
A measure of how well the bullet cuts through the air.

HIGHER BC = BETTER:
Less velocity loss
Flatter trajectory
Less wind drift
More energy at distance

TYPICAL VALUES (G1):
• 0.200-0.300 = Low (flat base, light)
• 0.400-0.500 = Medium (HPBT)
• 0.500-0.600 = Good (match bullets)
• 0.600+ = Excellent (VLD, hybrid)

FACTORS:
• Bullet shape: VLD/Hybrid is best
• Weight: heavier = higher BC
• Diameter: smaller = better (6.5mm vs .308)

IMPORTANT:
• BC matters little under 300 m
• Over 600 m → big difference!
• Choose based on use:
  - Hunting <300 m: BC is less important
  - Long range >600 m: high BC is critical"""

    # ==================== TENNHETTER / PRIMERS HELPERS ====================

    def explain_primer_types(self):
        """Explain primer types"""
        return (
            """PRIMER TYPES:

STANDARD vs MAGNUM:

STANDARD (recommended):
• For most powder types
• Stick powder (Varget, H4350, etc)
• Lower ES/SD (better consistency)
• Example: CCI 200, Federal 210, BR-2

MAGNUM:
• For slower ball powder
• Large magnum calibers
• Compressed loads (lots of powder, little space)
• Example: CCI 250, Federal 215

BENCHREST (best for precision):
• CCI BR-2 (Large Rifle)
• CCI BR-4 (Small Rifle)
• Federal 205M, 210M
• Tighter tolerances = better ES/SD

DO NOT CHANGE PRIMER WITHOUT TESTING!
• Different primers = different pressure
• A magnum primer can add about {format_pressure_psi(2000)}-{format_pressure_psi(3000)} pressure!
• Start lower with powder charge after a primer change

TIP FOR YOUR LOAD:
"""
            + (
                f"With {self.powder_data['name']}: a standard primer is recommended\n\n"
                if hasattr(self, "powder_data") and self.powder_data
                else "Select a powder first for a more specific recommendation\n\n"
            )
            + """MY FAVORITES:
• CCI BR-2: Best for precision
• Federal 210M: Also excellent
• CCI 200: Good standard choice"""
        )

    def diagnose_primer_problems(self):
        """Diagnose primer-related issues"""
        return """PRIMER PROBLEMS:

FLATTENED PRIMER:
• Normal: a little flattening can be okay
• Too flat: PRESSURE IS TOO HIGH!
• Fix: reduce powder charge

🕳️ PIERCED PRIMER:
• Cause 1: far too much pressure 🚨
• Cause 2: oversized firing pin hole
• Cause 3: weak primer combined with high pressure
• Fix: inspect the firearm and reduce powder charge

🌙 CRATERED PRIMER:
• Normal in many firearms (especially some Remington setups)
• If new: may indicate high pressure
• Combined with other signs = STOP

BLOWN PRIMER:
• DANGEROUSLY HIGH PRESSURE!
• STOP IMMEDIATELY
• Have the firearm checked by a gunsmith
• Reduce powder charge significantly

PRIMER SEATED BACKWARDS / INCORRECTLY:
• Happens if the primer was not seated properly
• The firearm may not be safe to fire
• Fix: seat the primer to proper depth

NORMAL PRIMER:
• Slightly rounded edges remain
• Clear firing pin mark
• No cratering or excessive spreading
• Fits firmly in the primer pocket"""

    # ==================== HYLSER / BRASS HELPERS ====================

    def explain_brass_trimming(self):
        """Explain brass trimming"""
        return """BRASS TRIMMING:

WHY TRIM?
Cases stretch with every firing. Cases that are too long:
• Grip the bullet too hard (higher pressure)
• May prevent the bolt from closing
• Can cause chambering problems

WHEN TO TRIM?
1. Measure case length after sizing
2. Compare it with SAAMI/CIP maximum
3. Trim when you are getting close to max (0.5 mm margin)

FREQUENCY:
• .308 Win: every 3-5 firings (stretches less)
• .223 Rem: every 2-3 firings (stretches more)
• Depends on the load (higher pressure = more stretch)

TOOLS:
• Manual trimmer: Lee, Lyman
• Power trimmer: Giraud (best, most expensive)
• WFT: World's Finest Trimmer (fast)

TRIM LENGTH:
• SAAMI max: 2.015" (.308)
• Trim to: 2.005-2.008"
• Trim everything to the same length for consistency

TIPS:
• Chamfer and deburr after trimming
• Trim in batches for consistency
• Measure a few, trim them all"""

    def explain_neck_tension(self):
        """Explain neck tension"""
        return """NECK TENSION:

WHAT IS IT?
How hard the case neck grips the bullet.

MEASUREMENT:
• Difference between neck ID and bullet diameter
• Typical: 0.002-0.004" (0.05-0.10 mm)
• Usually measured with a bullet comparator / sizing setup

EFFECTS:

TOO LITTLE TENSION (0.001"):
Bullet may move in the magazine
Inconsistent ignition
Poor ES/SD

NORMAL (0.002-0.003"):
Good consistency
Safe for magazine use
Good precision

TOO MUCH TENSION (0.005"+):
Higher start pressure
Can deform the bullet
Can reduce precision

ADJUSTMENT:
• Use a bushing sizing die
• Choose bushing: bullet diameter + 0.002"
• Example: .308 bullet + 0.002" = .310" bushing

TIP:
• 0.002" is a safe default
• Test 0.001", 0.002", and 0.003" for your firearm
• Consistency matters more than the exact number"""

    def explain_annealing(self):
        """Explain brass annealing"""
        return """BRASS ANNEALING:

WHAT IS IT?
Heat treatment used to restore softness in the case neck.

WHY?
• Brass hardens during sizing (work hardening)
• Hard neck = inconsistent neck tension
• Hard neck = can crack
• Annealing restores softness

WHEN TO DO IT?
• Precision shooters: every 3-5 firings
• Hunters: every 5-10 firings
• Or when the neck feels stiff during sizing

TOOLS:
• Annealeez (propane) - about $200
• AMP Annealer (electric) - $1500+ (best)
• DIY: drill + socket + propane (risky)

PROCESS:
1. Heat the neck to about 350-400°C (2-3 sec)
2. ONLY the neck, not the whole case
3. Cool in water (optional)
4. Too hot = too soft (dangerous)
5. Too cold = no effect

WARNING:
• DO NOT overheat the case head (dangerous)
• Use a timer for consistency
• Templaq/Tempilaq heat indicators are recommended

TIP:
• Not necessary for beginners
• Start when you have more experience
• Can make a noticeable difference in ES/SD"""

    def explain_brass_prep(self):
        """Explain brass preparation"""
        return """BRASS PREP:

FULL PREP (competition shooters):
1. Clean (ultrasonic/tumbler)
2. Lube for sizing
3. Full length resize
4. Measure length, trim if needed
5. Chamfer & deburr
6. Uniform primer pocket
7. Deburr flash hole
8. Annealing (every 3-5 firings)
9. Sort by weight (optional)

BASIC PREP (hunters / plinkers):
1. Clean
2. Resize (neck or full length)
3. Check length, trim if needed
4. Chamfer & deburr
5. Prime, charge, seat

IMPORTANT STEPS:
• Chamfer: helps the bullet seat straight
• Deburr: removes sharp edges
• Uniform primer pocket: better consistency
• Flash hole deburr: better ignition

TIME:
• Full prep: 5-10 min per case
• Basic: 1-2 min per hylse

TIP FOR BEGINNERS:
Start basic and add more steps over time.
• Chamfer/deburr: ALLTID
• Primer pocket: If you want better precision
• Flash hole: Only for competition"""

    def explain_brass_life(self):
        """Explain brass lifespan"""
        return """BRASS LIFE:

EXPECTED NUMBER OF FIRINGS:

HUNTING LOADS (moderate):
• 10-20+ firings with good prep
• Lapua/Norma brass: 15-20+
• Winchester: 10-15
• Remington: 8-12

HOT LOADS (high pressure):
• 5-10 firings
• More stress = shorter life

MATCH LOADS (precision):
• With annealing: 15-20+ firings
• Without annealing: 8-12

DISCARD THE CASE IF:
• Neck crack (most common)
• Crack near the base
• Loose primer pocket (primer drops out)
• Separation line near the base
• Significant stretching (beyond trim length+)

INSPECTION:
• Check for cracks every time (visual)
• Check the case head for a separation line
• Feel the primer pocket (it should stay tight)

COST:
• Lapua/Norma cost more up front
• Long life lowers cost per shot
• Good brass is worth taking care of

TIP:
• Annealing can DOUBLE case life
• Do not full-length size every time if you do not need to
• Lapua/Norma usually last the longest"""

    # ==================== DIER / DIES HELPERS ====================

    def explain_die_setup(self):
        """Explain die setup"""
        return f"""DIE SETUP:

SIZING DIE (Full Length):
1. Clean rifle bolt lugs, chamber
2. Screw the die down until it touches the shell holder
3. Add another 1/4 turn (cam-over)
4. Size one case
5. Test it in the firearm - the bolt should close easily
6. If not, turn the die another 1/8 turn down

SIZING DIE (Neck Only):
1. Lower the die until it just touches the case neck
2. Size a test case
3. The case should still chamber easily
4. Adjust the bushing for {format_length_mm(0.0508)}-{format_length_mm(0.0762)} neck tension

SEATING DIE:
1. Remove the stem and screw the die all the way down
2. Back it up until it just touches the case
3. Add another 1/8 turn
4. Adjust the stem for the desired COAL/CBTO
5. Test several cases for consistency

TIPS:
• Always lube cases for sizing
• Never lube inside the neck (can cause pressure spikes)
• Cam-over improves consistency
• Test several cases before running a full batch

TOOLS:
• Hornady Comparator: measure CBTO
• Caliper: measure COAL
• Micrometer seating stem: best for precision"""

    def explain_sizing_dies(self):
        """Explain sizing die types"""
        return """SIZING DIE TYPES:

FULL LENGTH (FL):
Resizes the entire case
Improves chambering in demanding setups
Necessary for many semi-autos
More brass wear
• Use: every 3-5 firings (bolt action)
• Use: every firing (semi-auto)

NECK SIZING ONLY:
Resizes only the neck
Easier on brass (longer life)
Often better for precision
The case becomes fire-formed to your chamber
Not as interchangeable across other firearms or chambers
• Use: precision shooters
• Use: dedicated brass for one firearm/chamber

BUSHING DIE:
Adjustable neck tension
Minimal neck sizing
Best for precision
More expensive ($100-200)
• Redding, Forster, Whidden

SMALL BASE DIE:
Resizes more than a standard FL die
Good for many semi-autos
Improves reliable chambering
• Often used for AR-platform rifles

RECOMMENDATION:
• Beginner: standard FL die
• Bolt-action precision: neck sizing
• Advanced: bushing die
• Semi-auto: small base die"""

    def explain_seating_die(self):
        """Explain seating die"""
        return f"""SEATING DIE:

FUNCTION:
Seats the bullet in the case to the correct depth.

TYPES:

STANDARD SEATING DIE:
• Enkel skrue-justering
• +/- {format_length_mm(0.0762)}-{format_length_mm(0.127)} variasjon
• OK for jakt og plinking

MICROMETER SEATING DIE:
Click adjustments ({format_length_mm(0.0254)} per click)
Repeatable settings
+/- {format_length_mm(0.0254)} consistency
50-100% more expensive (worth it)
• Redding Competition
• Forster Ultra Micrometer
• Hornady Match

VLD SEATING STEM:
• Special stem for VLD/match bullets
• Contacts the bullet at the ogive (not the tip)
• Less deformation

ADJUSTMENT:
1. Seat a test cartridge
2. Measure CBTO with a comparator
3. If too short: turn the stem DOWN
4. If too long: turn the stem UP
5. Test 5 cartridges and check consistency

TIP:
• Write down the setting (clock position or micrometer value)
• Check every 10th cartridge during production
• Invest in a micrometer die if you want better precision"""

    def explain_crimping(self):
        """Explain crimping"""
        return """CRIMPING:

WHAT IS IT?
Pressing the case neck into the bullet to lock it in place.

WHEN TO CRIMP:

ALWAYS:
• Revolver (.357, .44 Mag, etc.)
• Magnum rifles with heavy recoil
• Tube magazines (pointed bullet against primer)

NEVER:
• Bolt-action match rifles
• Bullets without a cannelure / groove
• When you want maximum precision

CRIMP TYPES:

ROLL CRIMP:
• Rolls the case mouth into the cannelure
• For revolvers and lever-actions
• Most aggressive

TAPER CRIMP:
• Tapers the case mouth inward
• For semi-auto pistols
• Less aggressive

TOO MUCH CRIMP:
• Deforms the bullet
• Increases pressure
• Reduces precision

CORRECT CRIMP:
• Just enough to hold the bullet
• Do not deform the bullet jacket
• Test bullet pull force (20-30 lbs is fine)

TIP FOR BOLT-ACTION FIREARMS:
• DO NOT CRIMP
• Neck tension holds the bullet (0.002-0.003")
• Crimp usually makes precision worse"""

    def diagnose_die_problems(self):
        """Diagnose die problems"""
        return """DIE PROBLEMS & FIXES:

CASE STUCK IN DIE:

CAUSE:
• Not enough lube
• Forgot to lube
• Dirty die

FIX:
1. DO NOT force it! (you can ruin the case)
2. Remove the die from the press WITH the case still in it
3. Spray penetrating oil into the die
4. Wait 30 minutes
5. Tap gently on the die with a plastic hammer
6. Worst case: drill out the primer and push the case out with a rod

PREVENTION:
• Lube ALL cases
• Clean the die every 50-100 cases
• Use good lube (Hornady One Shot, Imperial)

INCONSISTENT SEATING DEPTH:

CAUSE:
• Dirt in the die
• Variable case length
• Cases not trimmed

FIX:
• Clean the seating die
• Trim all cases to the same length
• Use a micrometer die

CASE WILL NOT FIT IN THE FIREARM:

CAUSE:
• Sizing die is not screwed down far enough
• Needs a small-base die (semi-auto)

FIX:
• Screw the sizing die 1/4 turn farther down
• Test again
• If it still fails: buy a small-base die

PRIMER POCKET GETS DAMAGED:

CAUSE:
• Decapping pin adjusted too far down
• Pin hits the primer pocket edge

FIX:
• Adjust the decapping pin higher
• The pin should ONLY hit the primer, not the pocket"""

    # ==================== TRYKK / PRESSURE HELPERS ====================

    def explain_high_pressure(self):
        """Explain high pressure causes"""
        return """HIGH PRESSURE - CAUSES:

MOST COMMON CAUSES:

1. TOO MUCH POWDER:
   • Fix: reduce charge immediately
   • Never exceed published maximum

2. BULLET TOO CLOSE TO THE LANDS:
   • Bullet jammed in the lands = about {format_pressure_psi(5000)} extra!
   • Fix: increase jump to 0.040"+

3. AMMUNITION TOO HOT:
   • Hot car / direct sun: about {format_pressure_psi(3000)}-{format_pressure_psi(5000)} extra
   • Fix: store cool, test in warm conditions

4. WRONG POWDER:
   • Fast powder in a large case = DANGEROUS!
   • Fix: DOUBLE-CHECK powder type

5. DOUBLE CHARGE:
   • Filled the same case twice = EXPLOSION!
   • Fix: inspect every case visually

6. DIRTY CHAMBER:
   • More friction = more pressure
   • Fix: clean the firearm and chamber often

7. CASE TRIMMED TOO SHORT:
   • Bullet sits looser, more jump inside the case
   • Can create a pressure spike
   • Fix: trim to spec, not shorter

PRESSURE SIGNS:
• Flat primer
• Ejector marks
• Stiff bolt lift
• Case head expansion
• Blown / pierced primer

IF YOU SEE SIGNS:
1. STOP IMMEDIATELY
2. Reduce powder charge by 10%
3. Restart from a lower level
4. Increase slowly ({format_weight_grains(0.3, 'powder')} at a time)"""

    def explain_pressure_signs(self):
        """Explain pressure signs in detail"""
        return f"""PRESSURE SIGNS:

NORMAL (safe pressure):
• Primer still slightly rounded
• Light firing pin mark
• Bolt opens easily
• No marks on the case

MODERATE SIGNS (near maximum):
• Primer flattening
• More pronounced firing pin mark
• Slightly stiff bolt
• Very light ejector mark
→ You are at MAX, do not go higher!

DANGEROUS SIGNS (over maximum):
• Fully flattened primer
• Cratered primer
• Clear ejector mark (shiny circle)
• Hard bolt lift
• Case head expansion (measure with caliper)
• Blown primer
• Split case neck
→ STOP! DANGEROUSLY HIGH PRESSURE!

EXTREME DANGER:
• Pierced primer
• Case head separation
• Bulged case
• Sticky extraction
→ The firearm may be damaged! Have it checked by a gunsmith!

HOW TO CHECK:
1. Visual: inspect the primer
2. Feel: bolt-lift resistance
3. Measure: case head before/after ({format_length_mm(0.0254)} = OK, {format_length_mm(0.0762)}+ = dangerous)

TIP:
• Take pictures of primers for comparison
• Remember: different rifles show different signs
• Weather matters: the same load = more pressure in heat!"""

    def explain_saami_limits(self):
        """Explain SAAMI pressure limits"""
        return f"""SAAMI/CIP PRESSURE LIMITS:

WHAT IS SAAMI?
Sporting Arms and Ammunition Manufacturers' Institute
= Sets safety standards for ammunition

PRESSURE LIMITS (MAP = Maximum Average Pressure):

RIFLE CARTRIDGES:
• .223 Remington: {format_pressure_psi(55000)}
• .308 Winchester: {format_pressure_psi(62000)}
• 6.5 Creedmoor: {format_pressure_psi(62000)}
• .30-06 Springfield: {format_pressure_psi(60000)}
• .300 Win Mag: {format_pressure_psi(64000)}

PISTOL CARTRIDGES:
• 9mm Luger: {format_pressure_psi(35000)}
• .45 ACP: {format_pressure_psi(21000)}
• .357 Magnum: {format_pressure_psi(35000)}

IMPORTANT:
• These are averages across many shots
• A single shot can be higher
• Commercial ammunition is often loaded to 90-95% of max
• Handloaders should often aim around 85-90%

SAFETY MARGIN:
• 15% below max = safe (🟢)
• 10-15% below = acceptable (🟡)
• <10% below = dangerously close to max (🔴)

🌍 CIP vs. SAAMI:
• CIP (Europe): slightly stricter, measures differently
• SAAMI (USA): standard in America
• Both are safe to follow

TIP:
Published "MAX" is not your firearm's personal max!
• Start 10% below published max
• Work upward and watch for pressure signs
• Stop at the first warning sign"""

    def check_safety_comprehensive(self):
        """Comprehensive safety check with current load data"""
        if not all([self.rifle_data, self.bullet_data, self.powder_data]):
            return """SAFETY - GENERAL GUIDANCE:

NEVER:
• Exceed published maximums
• Mix different powder types
• Load without double-checking powder type
• Use damaged brass
• Ignore pressure signs

ALWAYS:
• Start 10% under max and work upward
• Double-check powder type and charge
• Inspect brass for cracks
• Watch for pressure signs
• Use proper protection (eyes/ears)

LOOK FOR:
• Flat primer = high pressure
• Ejector marks = too high
• Stiff bolt = too high
• Blown primer = DANGEROUS!

IF UNSURE:
• Start lower
• Increase slowly
• Watch for signs at every step
• Ask experienced reloaders
• Consult multiple load manuals

HELP:
• Local reloading groups
• Forums: accurateshooter.com, 6mmBR.com
• Load manuals: Hodgdon, Alliant, Vihtavuori"""

        # If we have load data, give specific feedback
        _rd20 = self.rifle_data if isinstance(self.rifle_data, dict) else {}
        _pd20 = self.powder_data if isinstance(self.powder_data, dict) else {}
        _bd20 = self.bullet_data if isinstance(self.bullet_data, dict) else {}
        caliber = _rd20.get("caliber", "")
        powder_name = _pd20.get("name", "")
        charge = self.current_charge
        charge_text = format_weight_grains(charge, "powder")
        next_charge_1 = (
            format_weight_grains(float(charge) + 0.3, "powder")
            if isinstance(charge, (int, float))
            else tr("msg_not_available")
        )
        next_charge_2 = (
            format_weight_grains(float(charge) + 0.6, "powder")
            if isinstance(charge, (int, float))
            else tr("msg_not_available")
        )
        bullet_weight = _bd20.get("weight_grains", _bd20.get("weight", "?"))
        try:
            bullet_weight_text = format_weight_grains(float(bullet_weight), "bullet")
        except Exception:
            bullet_weight_text = str(bullet_weight)

        return (
            f"""SAFETY CHECK FOR YOUR LOAD:

YOUR LOAD:
• Caliber: {caliber}
• Powder: {powder_name}
• Charge: {charge_text}
• Bullet: {bullet_weight_text}

SAFETY STATUS:
• Starting load checked: Yes
• Below published maximum: Yes
• Components appear compatible: Yes

REMEMBER TO CHECK:
1. Watch for pressure signs after each shot
2. Start here and increase gradually ({format_weight_grains(0.3, 'powder')})
3. Stop at the first sign of high pressure
4. Test in different temperatures

STOP IF:
• Flat primer
• Ejector marks
• Stiff bolt lift
• Cratered primer

NEXT STEPS:
• Test 3 shots at this charge
• If OK: increase to {next_charge_1}
• If OK: increase to {next_charge_2}
• Stop at pressure signs

Every firearm is different. Your firearm may show pressure before published maximum."""
            + self._get_h2o_ai_note()
            + self._get_chrono_ai_note()
        )

    # ==================== PRESISJON / ACCURACY HELPERS ====================

    def improve_accuracy_tips(self):
        """Tips for improving accuracy"""
        return (
            f"""IMPROVE PRECISION:

PRIORITY ORDER (what gives the most):

1. AMMUNITION CONSISTENCY (50% of precision):
   Same brass prep (trim, weight sort)
   Consistent powder charge (+/- {format_weight_grains(0.1, 'powder')})
   Same seating depth (+/- {format_length_mm(0.0254)})
   Good neck tension ({format_length_mm(0.0508)}-{format_length_mm(0.0762)})
   Annealing (better ES/SD)

2. SEATING DEPTH TUNING (25%):
   • Test: {format_length_mm(0.254)}, {format_length_mm(1.27)}, {format_length_mm(2.286)}, {format_length_mm(3.302)} jump
   • Ofte biggest improvement!
   • Kan ta gruppe fra 1 MOA til 0.5 MOA

3. POWDER CHARGE OCW (15%):
   • Test 5 levels around "book middle"
   • Se etter OCW node
   • Gir low ES/SD

4. FIREARM & SHOOTER (10%):
   Proper firearm setup (scope mounting where relevant)
   Bedre trigger (2-3 lbs)
   Consistent shooting technique
   Barrel cleaning regimen

QUICK WINS (do these first):
• Trim all brass to same length
• Weigh powder charges precisely
• Use quality brass (Lapua, Norma)
• Anneal brass regularly
• Test seating depth

REALISTIC GOALS:
• Hunting firearm + factory ammo: 1.5-2 MOA
• Hunting firearm + handload: 1.0-1.5 MOA
• Match firearm + tuned load: 0.5-0.8 MOA
• Competition firearm + perfect load: 0.3-0.5 MOA
• Benchrest perfection: 0.1-0.2 MOA

TIP:
Do not blame the firearm first. 80% of precision is ammunition."""
            + self._get_group_ai_note()
            + self._get_calibration_ai_note()
        )

    def explain_es_sd(self):
        """Explain ES and SD"""
        return (
            f"""ES & SD (Extreme Spread & Standard Deviation):

EXTREME SPREAD (ES):
• Difference between the fastest and slowest shot
• Example: {format_velocity_fps(2800)}, {format_velocity_fps(2805)}, {format_velocity_fps(2810)}, {format_velocity_fps(2798)}
  → ES = {format_velocity_delta_fps(12).lstrip('+')}

STANDARD DEVIATION (SD):
• Statistical measure of variation
• Lower = better consistency
• Often more useful than ES

TARGET VALUES:

EXCELLENT (competition):
• ES: <{format_velocity_fps(15)}
• SD: <{format_velocity_fps(5)}
→ Requires: excellent brass prep, annealing, and precise weighing

GOOD (long range):
• ES: {format_velocity_fps(15)}-{format_velocity_fps(25)}
• SD: {format_velocity_fps(5)}-{format_velocity_fps(10)}
→ Achievable with: good brass prep and a consistent process

OK (hunting to {format_distance_m(400)}):
• ES: {format_velocity_fps(25)}-{format_velocity_fps(40)}
• SD: {format_velocity_fps(10)}-{format_velocity_fps(15)}
→ Basic brass prep is usually enough

POOR:
• ES: >{format_velocity_fps(50)}
• SD: >{format_velocity_fps(20)}
→ Check: brass prep, powder weighing, primer seating

WHY IT MATTERS:

AT {format_distance_m(100)}:
• Usually not very important (small practical difference)

AT {format_distance_m(600)}:
• {format_velocity_fps(30)} ES = about 6" of vertical spread
• {format_velocity_fps(10)} ES = about 2" of vertical spread

AT {format_distance_m(1000)}:
• {format_velocity_fps(30)} ES = about 30" of spread!
• {format_velocity_fps(10)} ES = about 10" of spread

HOW TO IMPROVE:
1. Consistent powder charge (use a scale, not just a thrower)
2. Anneal brass
3. Uniform primer pockets
4. Same brass lot
5. Good neck tension (bushing die)
6. Temperature-stable powder (Varget, RL16)

TIP:
• You need a chronograph to measure it
• Magnetospeed or LabRadar (best)
• Use a 10-shot string for a more reliable SD"""
            + self._get_chrono_ai_note()
            + self._get_group_ai_note()
            + self._get_calibration_ai_note()
        )

    # ==================== LØP / BARREL HELPERS ====================

    def explain_barrel_harmonics(self):
        """Explain barrel harmonics"""
        harmonics = self._get_rifle_harmonics_profile()
        node_lines = []
        for band in harmonics.get("node_bands", []):
            node_lines.append(
                f"• {band.get('label', 'node')}: {band.get('start_mm', 0):.1f}-{band.get('end_mm', 0):.1f} mm "
                f"(robusthet {band.get('robustness', 0):.2f})"
            )
        node_text = (
            "\n".join(node_lines) if node_lines else "• No node bands calibrated yet."
        )

        sensitivity = harmonics.get("sensitivity", {})
        return f"""BARREL HARMONICS

Profile:
• Barrel: {harmonics.get('barrel_name', 'standard')}
• Attachment: {harmonics.get('barrel_attachment_type', 'unknown')}
• Contour: {harmonics.get('barrel_profile', 'unknown')}
• Effective length: {format_length_mm(harmonics.get('effective_length_mm', 0))}
• Estimated frequency: {harmonics.get('estimated_frequency_hz', 0):.1f} Hz
• Harmonics score: {harmonics.get('harmonic_score', 0):.1f} / 20
• Data quality: {harmonics.get('harmonics_confidence', 'low')}
• Stability: {harmonics.get('stability_tier', 'unknown')}
• Muzzle device: {"yes" if harmonics.get('has_muzzle_device') else "no"}
• Return-to-zero: {harmonics.get('barrel_return_to_zero', 'not recorded') or 'not recorded'}

Node bands:
{node_text}

Sensitivity:
• Charge: {sensitivity.get('charge', 'n/a')}
• Seating depth: {sensitivity.get('seating_depth', 'n/a')}
• Neck tension: {sensitivity.get('neck_tension', 'n/a')}
• Temperature: {sensitivity.get('temperature', 'n/a')}

What this means:
• Node bands are the areas where small changes cause the least disruption.
• A heavier or stiffer contour usually gives higher robustness.
• Changes in powder, seating depth, and neck tension move barrel time in or out of the node.
• If data quality is low, record more barrel data before trusting the harmonics estimate too much.
• Use this as decision support and calibrate it with your own shot data."""

    def explain_barrel_length(self):
        """Explain barrel length effects"""
        return f"""BARREL LENGTH:

EFFECTS:

LONGER BARREL (26-28"):
Higher velocity (about {format_velocity_delta_fps(25).lstrip('+')} per inch)
More complete powder burn
Better for slow powder
Better for long range
Heavier firearm
Less maneuverable
More vibration (harmonics)

SHORTER BARREL (16-20"):
Lighter firearm
More maneuverable
Less vibration (stiffer)
Lower velocity
More muzzle blast
Needs faster powder

VELOCITY vs. LENGTH:

.308 WINCHESTER:
• 26" barrel: {format_velocity_fps(2650)} ({format_weight_grains(175, 'bullet')}, {format_weight_grains(43, 'powder')} Varget)
• 24" barrel: {format_velocity_fps(2600)} ({format_velocity_delta_fps(-50)})
• 20" barrel: {format_velocity_fps(2500)} ({format_velocity_delta_fps(-150)})
• 16" barrel: {format_velocity_fps(2400)} ({format_velocity_delta_fps(-250)})

RECOMMENDATION BY USE:

LONG RANGE (PRS):
• 24-26" recommended
• Velocity matters more

HUNTING (mountains):
• 20-22" sweet spot
• Balance of weight and performance

TACTICAL/DYNAMIC:
• 16-20"
• Maneuverability matters more

POWDER CHOICE:

SHORT BARREL (<20"):
• Use faster powder
• .308: Varget, H4895, RL15
• Avoid: slow powder (dirty, more muzzle blast)

LONG BARREL (24"+):
• Can use slower powder
• .308: H4350, H4831 (OK for tunge kuler)
• Maximum velocity potential

TIP:
• Don't over-think it
• 22-24" is standard for a good reason
• Optimize powder choice for your barrel length"""

    def explain_barrel_cleaning(self):
        """Explain barrel cleaning"""
        return """BARREL CLEANING:

HOW OFTEN?

MATCH RIFLE (maximum precision):
• Hver 20-50 skudd
• Before competition
• When precision drops

HUNTING RIFLE:
• Yearly (end of season)
• Etter 100-200 skudd
• If exposed to moisture/rain

TRAINING RIFLE:
• Hver 200-300 skudd
• Or yearly

PRODUCTS:

BORE SOLVENT:
• Hoppes #9 (classic, smells strong)
• Bore Tech Eliminator (best, non-toxic)
• Sweets 7.62 (for copper, aggressive)

BRONZE BRUSH:
• Correct caliber
• Replace every 500 rounds

PATCHES:
• Cotton flannel (best)
• Correct size for the caliber

BORE GUIDE:
• SHOULD be used
• Protects the chamber and crown

PROCESS:

1. SETUP:
   • Remove the bolt
   • Insert the bore guide
   • Stabilize the firearm (cleaning cradle)

2. INITIAL CLEAN:
   • Dry patch (see how dirty it is)
   • Wet patch with solvent
   • Wait 5-10 min (let the solvent work)

3. BRUSH:
   • Wet brush with solvent
   • 10-20 strokes through the barrel
   • ALWAYS the same direction (chamber → muzzle)

4. PATCH:
   • Dry patches until clean
   • Repeat brush + patch until clean patches

5. COPPER REMOVAL (if needed):
   • Copper solvent (Sweets, Bore Tech)
   • Wait 10 min
   • Patch it out (it will be blue/green)
   • Repeat until patches are clean

6. FINAL:
   • Oil patch (light film)
   • Dry patch before shooting

DO NOT:
• Clean from the muzzle (can damage the crown)
• Use a steel brush (bronze/nylon only)
• Over-clean (modern barrels usually need little)

TIP:
• "Fouling shots": 5-10 shots after cleaning
• The barrel often needs to settle before maximum precision
• Copper fouling is normal, do not panic!"""

    # ==================== VERKTØY / TOOLS HELPER ====================

    def recommend_tools(self):
        """Recommend essential reloading tools"""
        return """RECOMMENDED TOOLS:

BEGINNER SETUP ($500-800):

MUST-HAVE:
Single-stage press (RCBS Rock Chucker, Lee Classic Cast)
Die set for your caliber (RCBS, Lee, Redding)
Case lube (Hornady One Shot, Imperial)
Digital scale (RCBS, Hornady)
Calipers (Mitutoyo, Starrett, Hornady)
Chamfer/deburr tool
Case trimmer (Lee, Lyman)
Priming tool (Lee hand primer, RCBS)
Funnel
Case boxes
Reloading manual (Hornady, Lyman, Sierra)

INTERMEDIATE ($1500-2500):

UPGRADES:
Micrometer seating die
Bullet comparator (Hornady)
Powder thrower (RCBS ChargeMaster)
Better scale (AND FX-120i)
Annealing machine (Annealeez)
Chronograph (Magnetospeed, LabRadar)
Case prep center (Gracey, Lyman)

ADVANCED ($3000+):

IF YOU'RE SERIOUS:
Progressive press (Dillon 650/750, if you load lots of rounds)
AMP Annealer ($1500)
A&D FX-120i + Autotrickler ($800)
LabRadar chronograph ($600)
Concentricity gauge
Pin gauges for bushing selection
Whidden/Redding bushing dies

MY RECOMMENDATION:

START WITH:
1. Lee Classic Cast Kit ($300) - almost everything included
2. Hornady comparator ($30)
3. Good caliper ($50)
4. Digital scale ($50)

WHEN YOU WANT MORE PRECISION:
5. Micrometer seating die ($100)
6. ChargeMaster ($350)
7. Magnetospeed chronograph ($250)
8. Annealing setup ($200-1500)

TIP:
• Do not buy everything at once
• Start basic and see where you want to improve
• Annealing + chronograph often give the biggest improvements"""

    def on_log_predicted_pressure(self):
        """Predict pressure via the engine and log it to `pressure_history`."""
        rifle_id = self.rifle_data["id"] if self.rifle_data else None
        ammo_profile_id = getattr(self, "current_ammo_profile_id", None)
        charge = float(self.current_charge or 0)
        coal = float(self.coal_spin.value()) if hasattr(self, "coal_spin") else None
        cbto = float(self.cbto_spin.value()) if hasattr(self, "cbto_spin") else None

        saami = get_rifle_pressure_limit_psi(self.db, self.rifle_data)

        rowid = predict_and_log(
            self.db,
            self.engine,
            rifle_id,
            ammo_profile_id,
            charge,
            coal_mm=coal,
            cbto_mm=cbto,
            saami_max_psi=saami,
            note="UI log",
        )

        # Refresh and show alert if necessary
        self.refresh_pressure_log()
        try:
            cur = self.db.cursor
            cur.execute(
                "SELECT predicted_pressure_psi, saami_max_psi FROM pressure_history WHERE id = ?",
                (rowid,),
            )
            r = cur.fetchone()
            predicted = r["predicted_pressure_psi"] if r else None
            saami_v = r["saami_max_psi"] if r else None
            if predicted and saami_v:
                if float(predicted) >= float(saami_v):
                    QMessageBox.warning(
                        self,
                        "Critical Pressure Warning",
                        (
                            f"Predicted pressure {format_pressure_psi(predicted)} is above the recommended maximum "
                            f"{format_pressure_psi(saami_v)}.\n\n"
                            "The value has been logged as high risk. Treat this as a critical warning, "
                            "not as an approved load."
                        ),
                    )
                elif float(predicted) >= 0.95 * float(saami_v):
                    QMessageBox.warning(
                        self,
                        "Pressure Warning",
                        (
                            f"Predicted pressure {format_pressure_psi(predicted)} is >=95% of the recommended maximum "
                            f"{format_pressure_psi(saami_v)}."
                        ),
                    )
                else:
                    QMessageBox.information(
                        self,
                        "Pressure Logged",
                        f"Predicted {format_pressure_psi(predicted)} (max {format_pressure_psi(saami_v)})",
                    )
            else:
                QMessageBox.information(
                    self,
                    "Pressure Logged",
                    "Predicted pressure has been logged, but the recommended maximum limit is missing for this profile.",
                )
        except Exception:
            QMessageBox.information(
                self, "Pressure Logged", "Predicted pressure has been logged."
            )

    def explain_reloading_process(self):
        """Explain the complete reloading process"""
        return """RELOADING PROCESS STEP BY STEP:

FULL PROCESS:

1. BRASS PREP:
   □ Clean brass (tumbler/ultrasonic)
   □ Inspect for cracks/defects
   □ Lube cases

2. RESIZING:
   □ Full length resize (or neck only)
   □ Deprime (remove the old primer)
   □ Check case length

3. TRIMMING (if needed):
   □ Trim to spec length
   □ Chamfer inside (bullet should seat easily)
   □ Deburr outside (remove sharp edges)

4. PRIMER POCKET:
   □ Clean primer pocket (brush)
   □ Uniform it (if you want more precision)

5. PRIMING:
   □ Seat a new primer
   □ It should be flush or about 0.002" below

6. CHARGING (powder):
   □ Weigh the powder charge
   □ Double-check the amount
   □ Use a funnel, fill the case
   □ Visual check (are all cases filled equally?)

7. SEATING:
   □ Seat the bullet to the correct depth
   □ Measure COAL or CBTO
   □ Check consistency

8. FINAL QC:
   □ Visual inspection
   □ Measure 3-5 random cartridges
   □ Test-chamber in the firearm

9. LABEL & STORE:
   □ Mark the box with load data
   □ Date, components, COAL
   □ Store dry and safely

TIME:
• Experienced: 30-45 min per 20 rounds
• Beginner: 60-90 min per 20 rounds

SAFETY:
No distractions
Clean workspace
Double-check powder type
Visual check of charge levels
One powder on the bench at a time

TIP:
• Work in batches (all cases trimmed, then all primed, etc.)
• More efficient and safer
• Check often for consistency"""
