"""
Test script for AI Rifle Lookup
Demonstrerer hvordan AI-funksjonen henter rifle-data
"""

from src.utils.rifle_ai_lookup import get_rifle_lookup_service


def test_rifle_lookup():
    """Tester AI rifle lookup med forskjellige eksempler"""
    
    service = get_rifle_lookup_service()
    
    print("🤖 AI Rifle Lookup - Test\n")
    print("=" * 70)
    
    # Test cases
    test_rifles = [
        ("Tikka T3X Hunter .308 Win", None),
        ("Sako 85 Finnlight 6.5 Creedmoor", None),
        ("Bergara B-14 HMR .308", "Bergara"),
        ("Remington 700 SPS Tactical", "Remington"),
        ("Custom rifle 6.5x55", None),
    ]
    
    for rifle_name, manufacturer in test_rifles:
        print(f"\n📍 Testing: {rifle_name}")
        print("-" * 70)
        
        result = service.lookup_rifle(rifle_name, manufacturer)
        
        print(f"  Navn:          {result['name']}")
        print(f"  Produsent:     {result['manufacturer'] or 'Ikke funnet'}")
        print(f"  Kaliber:       {result['caliber'] or 'Ikke funnet'}")
        print(f"  Løpslengde:    {result['barrel_length'] or 'Ikke funnet'} tommer")
        print(f"  Twist Rate:    {result['twist_rate'] or 'Ikke funnet'}")
        print(f"  Action:        {result['action_type']}")
        print(f"  Confidence:    {result['confidence']}")
        
        if result['sources']:
            print(f"  Kilder:        {', '.join(result['sources'])}")
        
        if result['notes']:
            print(f"  Notater:       {result['notes']}")
    
    print("\n" + "=" * 70)
    print("\n✅ Test ferdig!\n")
    print("💡 Tips:")
    print("  - AI prøver å finne produkt-sider automatisk")
    print("  - Hvis ikke funnet, ekstraheres data fra navnet")
    print("  - Du kan ALLTID redigere alle feltene manuelt før lagring")
    print("  - Confidence: high/medium/low indikerer hvor sikker AI-en er")
    print("\n🎯 I GUI-en:")
    print("  1. Klikk 'Ny Rifle' i Rifle & Optikk Manager")
    print("  2. Skriv inn rifle-navn")
    print("  3. Klikk '🤖 AI Lookup'")
    print("  4. Rediger feltene hvis nødvendig")
    print("  5. Klikk 'Lagre'\n")


if __name__ == "__main__":
    test_rifle_lookup()
