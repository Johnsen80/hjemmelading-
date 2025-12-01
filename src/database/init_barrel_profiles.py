"""
Initialiserer predefinerte barrel profiles (løpsprofiler) i databasen.
Disse brukes for harmonisk beregning og løpskarakteristikk.
"""

from .database import get_database

def initialize_barrel_profiles():
    """
    Legger til predefinerte barrel profiles basert på industristandarder.
    Disse er vanlige profiler fra produsenter som Bartlein, Krieger, Shilen, etc.
    """
    
    db = get_database()
    
    profiles = [
        {
            'name': 'Light Sporter',
            'description': 'Lettvekt jaktprofil, god balanse mellom vekt og stivhet',
            'category': 'hunting',
            'muzzle_diameter_mm': 15.24,  # 0.600"
            'muzzle_diameter_inches': 0.600,
            'breech_diameter_mm': 28.58,  # 1.125"
            'breech_diameter_inches': 1.125,
            'taper_type': 'tapered',
            'taper_rate_per_inch': 0.020,  # 0.020" per tomme
            'typical_length_inches': 22.0,
            'weight_per_inch_grams': 85.0,
            'typical_total_weight_grams': 1870.0,  # ~4.1 lbs
            'stiffness_rating': 'light',
            'harmonic_characteristics': 'Raskere harmonisk frekvens, mer følsom for ladning. God for jakt opp til 300m.',
            'recommended_for': 'hunting',
            'typical_calibers': '.243 Win, .270 Win, 7mm-08, .308 Win',
            'notes': 'Standard lettvekt jaktprofil. Balanserer bra. Ikke for langdistanse presisjon.'
        },
        {
            'name': 'Medium Sporter',
            'description': 'Allsidig profil for jakt og target shooting',
            'category': 'hunting',
            'muzzle_diameter_mm': 17.78,  # 0.700"
            'muzzle_diameter_inches': 0.700,
            'breech_diameter_mm': 29.21,  # 1.150"
            'breech_diameter_inches': 1.150,
            'taper_type': 'tapered',
            'taper_rate_per_inch': 0.018,
            'typical_length_inches': 24.0,
            'weight_per_inch_grams': 110.0,
            'typical_total_weight_grams': 2640.0,  # ~5.8 lbs
            'stiffness_rating': 'medium',
            'harmonic_characteristics': 'Moderat harmonisk frekvens. God balance mellom vekt og presisjon.',
            'recommended_for': 'hunting, precision',
            'typical_calibers': '.243 Win, 6.5 Creedmoor, .270 Win, .308 Win, .30-06',
            'notes': 'Veldig allsidig profil. Fungerer for både jakt og presisjon.'
        },
        {
            'name': 'Heavy Sporter',
            'description': 'Tung sporter for bedre presisjon',
            'category': 'hunting',
            'muzzle_diameter_mm': 19.05,  # 0.750"
            'muzzle_diameter_inches': 0.750,
            'breech_diameter_mm': 30.48,  # 1.200"
            'breech_diameter_inches': 1.200,
            'taper_type': 'tapered',
            'taper_rate_per_inch': 0.016,
            'typical_length_inches': 26.0,
            'weight_per_inch_grams': 135.0,
            'typical_total_weight_grams': 3510.0,  # ~7.7 lbs
            'stiffness_rating': 'medium',
            'harmonic_characteristics': 'Lavere harmonisk frekvens, mer stabil. God presisjon.',
            'recommended_for': 'precision, hunting',
            'typical_calibers': '6mm Creedmoor, 6.5 Creedmoor, .260 Rem, 7mm Rem Mag, .300 Win Mag',
            'notes': 'Tyngre profil for bedre presisjon. Fortsatt håndterbar vekt.'
        },
        {
            'name': 'Light Varmint',
            'description': 'Lett varmint-profil for skadedjur',
            'category': 'varmint',
            'muzzle_diameter_mm': 20.32,  # 0.800"
            'muzzle_diameter_inches': 0.800,
            'breech_diameter_mm': 30.48,  # 1.200"
            'breech_diameter_inches': 1.200,
            'taper_type': 'tapered',
            'taper_rate_per_inch': 0.014,
            'typical_length_inches': 24.0,
            'weight_per_inch_grams': 145.0,
            'typical_total_weight_grams': 3480.0,  # ~7.7 lbs
            'stiffness_rating': 'medium',
            'harmonic_characteristics': 'God stivhet for raskt repeterende skyting. Moderat vekt.',
            'recommended_for': 'varmint, precision',
            'typical_calibers': '.223 Rem, .204 Ruger, .22-250, 6mm Creedmoor',
            'notes': 'God for varmint hunting med mange skudd. Ikke for tung.'
        },
        {
            'name': 'Heavy Varmint',
            'description': 'Tung varmint-profil for maksimal presisjon',
            'category': 'varmint',
            'muzzle_diameter_mm': 22.86,  # 0.900"
            'muzzle_diameter_inches': 0.900,
            'breech_diameter_mm': 31.75,  # 1.250"
            'breech_diameter_inches': 1.250,
            'taper_type': 'straight-taper',
            'taper_rate_per_inch': 0.012,
            'typical_length_inches': 26.0,
            'weight_per_inch_grams': 175.0,
            'typical_total_weight_grams': 4550.0,  # ~10 lbs
            'stiffness_rating': 'heavy',
            'harmonic_characteristics': 'Lav harmonisk frekvens, veldig stabil. Utmerket presisjon.',
            'recommended_for': 'varmint, benchrest, precision',
            'typical_calibers': '.223 Rem, .204 Ruger, .22-250, 6mm BR, 6mm Dasher',
            'notes': 'Klassisk heavy varmint. Veldig stiv, utmerket presisjon. Tung.'
        },
        {
            'name': 'Sendero',
            'description': 'Remington Sendero-stil kontur, populær for langdistanse',
            'category': 'target',
            'muzzle_diameter_mm': 21.59,  # 0.850"
            'muzzle_diameter_inches': 0.850,
            'breech_diameter_mm': 30.48,  # 1.200"
            'breech_diameter_inches': 1.200,
            'taper_type': 'tapered',
            'taper_rate_per_inch': 0.013,
            'typical_length_inches': 26.0,
            'weight_per_inch_grams': 160.0,
            'typical_total_weight_grams': 4160.0,  # ~9.2 lbs
            'stiffness_rating': 'heavy',
            'harmonic_characteristics': 'Populær kontur for langdistanse. God stivhet og presisjon.',
            'recommended_for': 'precision, competition',
            'typical_calibers': '6mm Creedmoor, 6.5 Creedmoor, 6.5 PRC, .308 Win, 7mm Rem Mag, .300 Win Mag',
            'notes': 'Meget populær profil for presisjonsskyting. God balanse vekt/presisjon.'
        },
        {
            'name': 'Palma',
            'description': 'Palma-profil for konkurranser på 800-1000 yards',
            'category': 'target',
            'muzzle_diameter_mm': 19.05,  # 0.750"
            'muzzle_diameter_inches': 0.750,
            'breech_diameter_mm': 29.21,  # 1.150"
            'breech_diameter_inches': 1.150,
            'taper_type': 'straight-taper',
            'taper_rate_per_inch': 0.015,
            'typical_length_inches': 30.0,
            'weight_per_inch_grams': 125.0,
            'typical_total_weight_grams': 3750.0,  # ~8.3 lbs
            'stiffness_rating': 'medium',
            'harmonic_characteristics': 'Designet for .308 Win Palma-konkurranser. Lang og stabil.',
            'recommended_for': 'competition',
            'typical_calibers': '.308 Win, 6.5x55 Swedish',
            'notes': 'Spesifikt for Palma-skyting. Lang pipe (30-32"). Middels vekt.'
        },
        {
            'name': 'Medium Palma',
            'description': 'Tyngre Palma-variant',
            'category': 'target',
            'muzzle_diameter_mm': 20.32,  # 0.800"
            'muzzle_diameter_inches': 0.800,
            'breech_diameter_mm': 30.48,  # 1.200"
            'breech_diameter_inches': 1.200,
            'taper_type': 'straight-taper',
            'taper_rate_per_inch': 0.013,
            'typical_length_inches': 30.0,
            'weight_per_inch_grams': 145.0,
            'typical_total_weight_grams': 4350.0,  # ~9.6 lbs
            'stiffness_rating': 'heavy',
            'harmonic_characteristics': 'Tyngre Palma-variant for bedre stabilitet.',
            'recommended_for': 'competition',
            'typical_calibers': '.308 Win, 6.5 Creedmoor',
            'notes': 'Tyngre enn standard Palma. Mer stabil for langdistanse.'
        },
        {
            'name': 'MTU (M24)',
            'description': 'Military Target/Utility profil fra M24 sniper system',
            'category': 'tactical',
            'muzzle_diameter_mm': 31.75,  # 1.250"
            'muzzle_diameter_inches': 1.250,
            'breech_diameter_mm': 31.75,  # 1.250"
            'breech_diameter_inches': 1.250,
            'taper_type': 'straight',
            'taper_rate_per_inch': 0.000,  # Rett (ingen taper)
            'typical_length_inches': 24.0,
            'weight_per_inch_grams': 210.0,
            'typical_total_weight_grams': 5040.0,  # ~11.1 lbs
            'stiffness_rating': 'very-heavy',
            'harmonic_characteristics': 'Ekstremt stiv straight-cylinder. Veldig lav harmonisk frekvens. Maksimal presisjon.',
            'recommended_for': 'tactical, benchrest, precision',
            'typical_calibers': '.308 Win, .300 Win Mag, 6.5 Creedmoor, 6mm Creedmoor',
            'notes': 'Meget tung og stiv. Brukt i militære snikskyttersystemer. Utmerket presisjon.'
        },
        {
            'name': 'Bull Barrel',
            'description': 'Tung straight-cylinder for benchrest',
            'category': 'benchrest',
            'muzzle_diameter_mm': 33.02,  # 1.300"
            'muzzle_diameter_inches': 1.300,
            'breech_diameter_mm': 33.02,  # 1.300"
            'breech_diameter_inches': 1.300,
            'taper_type': 'straight',
            'taper_rate_per_inch': 0.000,
            'typical_length_inches': 24.0,
            'weight_per_inch_grams': 225.0,
            'typical_total_weight_grams': 5400.0,  # ~11.9 lbs
            'stiffness_rating': 'very-heavy',
            'harmonic_characteristics': 'Maksimal stivhet. Minimal harmonisk bevegelse. For benchrest og F-Class.',
            'recommended_for': 'benchrest, competition',
            'typical_calibers': '6mm BR, 6mm Dasher, 6.5x47 Lapua, .308 Win',
            'notes': 'Ekstremt tung. Kun for benchrest eller rifle-mount bruk. Maksimal presisjon.'
        },
        {
            'name': 'Heavy Bull',
            'description': 'Ekstra tung bull barrel for maksimal presisjon',
            'category': 'benchrest',
            'muzzle_diameter_mm': 38.10,  # 1.500"
            'muzzle_diameter_inches': 1.500,
            'breech_diameter_mm': 38.10,  # 1.500"
            'breech_diameter_inches': 1.500,
            'taper_type': 'straight',
            'taper_rate_per_inch': 0.000,
            'typical_length_inches': 26.0,
            'weight_per_inch_grams': 285.0,
            'typical_total_weight_grams': 7410.0,  # ~16.3 lbs
            'stiffness_rating': 'bull',
            'harmonic_characteristics': 'Maksimal masse og stivhet. Absolutt minimal harmonisk bevegelse. Benchrest-klasse.',
            'recommended_for': 'benchrest',
            'typical_calibers': '6mm BR, 6mm Dasher, .30 BR',
            'notes': 'Kun for benchrest. Ekstremt tung. Sub-0.1 MOA presisjon mulig.'
        },
        {
            'name': 'Fluted Sporter',
            'description': 'Fluted medium sporter - lettere men stiv',
            'category': 'hunting',
            'muzzle_diameter_mm': 19.05,  # 0.750"
            'muzzle_diameter_inches': 0.750,
            'breech_diameter_mm': 30.48,  # 1.200"
            'breech_diameter_inches': 1.200,
            'taper_type': 'fluted',
            'taper_rate_per_inch': 0.016,
            'typical_length_inches': 24.0,
            'weight_per_inch_grams': 115.0,  # 15% lighter than non-fluted
            'typical_total_weight_grams': 2760.0,  # ~6.1 lbs
            'stiffness_rating': 'medium',
            'harmonic_characteristics': 'Fluting reduserer vekt uten stor tap av stivhet. God kjøling.',
            'recommended_for': 'hunting, precision',
            'typical_calibers': '6.5 Creedmoor, .270 Win, .308 Win, 7mm Rem Mag',
            'notes': 'Fluting sparer ~15% vekt. God balanse. Raskere kjøling.'
        },
        {
            'name': 'Fluted Heavy Varmint',
            'description': 'Fluted heavy varmint - tung presisjon med mindre vekt',
            'category': 'varmint',
            'muzzle_diameter_mm': 22.86,  # 0.900"
            'muzzle_diameter_inches': 0.900,
            'breech_diameter_mm': 31.75,  # 1.250"
            'breech_diameter_inches': 1.250,
            'taper_type': 'fluted',
            'taper_rate_per_inch': 0.012,
            'typical_length_inches': 26.0,
            'weight_per_inch_grams': 150.0,  # 15% lighter
            'typical_total_weight_grams': 3900.0,  # ~8.6 lbs
            'stiffness_rating': 'heavy',
            'harmonic_characteristics': 'Beholder mye av stivheten til heavy varmint, men lettere.',
            'recommended_for': 'varmint, precision',
            'typical_calibers': '.223 Rem, 6mm Creedmoor, 6.5 Creedmoor',
            'notes': 'Populær fluted variant. God presisjon uten ekstrem vekt.'
        },
        {
            'name': 'Carbon Fiber Wrapped',
            'description': 'Carbon fiber wrapped barrel - lett og stiv',
            'category': 'hunting',
            'muzzle_diameter_mm': 22.86,  # 0.900" outer diameter
            'muzzle_diameter_inches': 0.900,
            'breech_diameter_mm': 30.48,  # 1.200"
            'breech_diameter_inches': 1.200,
            'taper_type': 'carbon-wrapped',
            'taper_rate_per_inch': 0.010,
            'typical_length_inches': 24.0,
            'weight_per_inch_grams': 95.0,  # Much lighter than steel
            'typical_total_weight_grams': 2280.0,  # ~5 lbs
            'stiffness_rating': 'heavy',
            'harmonic_characteristics': 'Carbon fiber gir ekstra stivhet med minimal vekt. Rask kjøling. Dyr.',
            'recommended_for': 'hunting, precision',
            'typical_calibers': '6mm Creedmoor, 6.5 Creedmoor, 6.5 PRC, 7mm Rem Mag, .300 Win Mag',
            'notes': 'Proof Research, Christensen Arms, etc. Dyr men utmerket ytelse/vekt-ratio.'
        }
    ]
    
    # Sjekk om det allerede finnes profiles
    existing = db.execute_query("SELECT COUNT(*) as count FROM barrel_profiles")
    if existing[0]['count'] > 0:
        print(f"Barrel profiles allerede initialisert ({existing[0]['count']} profiler funnet)")
        return
    
    # Legg til alle profiles
    for profile in profiles:
        db.insert('barrel_profiles', profile)
    
    print(f"✅ Initialisert {len(profiles)} barrel profiles")
    
    # Vis oversikt
    print("\n📊 Barrel Profiles:")
    print("=" * 80)
    for profile in profiles:
        print(f"  • {profile['name']:30s} - {profile['stiffness_rating']:12s} - {profile['category']}")
    print("=" * 80)


if __name__ == "__main__":
    initialize_barrel_profiles()
