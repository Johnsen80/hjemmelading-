"""
Test AI Chat Capabilities
Demonstrerer alle emnene AI-chatten kan svare på
"""

# Test questions the AI can answer
test_questions = [
    # KRUTT / POWDER
    "Hvilket krutt anbefaler du?",
    "Hvor mye krutt skal jeg bruke?",
    "Hvordan påvirker temperatur kruttet?",
    "Hva er brennhastighet?",
    "Hvordan lagre krutt?",
    # KULER / BULLETS
    "Hvor dypt skal jeg sette kulen?",
    "Hva er CBTO?",
    "Hva er bullet jump?",
    "Hvilken kulevekt skal jeg velge?",
    "Hva er BC?",
    # TENNHETTER / PRIMERS
    "Hvilken tennhette skal jeg bruke?",
    "Standard eller magnum primer?",
    "Hvorfor er tennhetten flat?",
    "Tennhette har hull - hva betyr det?",
    # HYLSER / BRASS
    "Når skal jeg trimme hylser?",
    "Hva er neck tension?",
    "Hvordan gløde hylser?",
    "Hvordan preparere hylser?",
    "Hvor mange ganger kan jeg bruke hylsen?",
    # DIER / DIES
    "Hvordan stille inn diene?",
    "Full length eller neck sizing?",
    "Hvordan funker seating die?",
    "Skal jeg crimpe?",
    "Hylsen setter seg fast i die - hva gjør jeg?",
    # TRYKK / PRESSURE
    "Hvorfor er trykket så høyt?",
    "Hvilke tegn på høyt trykk?",
    "Hva er SAAMI-grenser?",
    "Er dette trygt?",
    # PRESISJON / ACCURACY
    "Hvordan forbedre presisjonen?",
    "Hva er ES og SD?",
    "Hvordan teste ladningen?",
    # LØP / BARREL
    "Hva er løpsharmonikk?",
    "Hvor lang løpslengde trenger jeg?",
    "Hvordan rengjøre løpet?",
    # VERKTØY / TOOLS
    "Hvilket verktøy trenger jeg?",
    # PROSESS
    "Hvordan er ladeprosessen?",
    "Hva er stegene i lading?",
]

print("🤖 AI CHAT KOMPETANSE - Modern Load Builder")
print("=" * 70)
print("\nAI-chatten kan nå svare på ALT om ladeprosessen!\n")

categories = {
    "📦 KOMPONENTER": [
        "Krutt: anbefalinger, mengde, temperatur, brennhastighet, lagring",
        "Kuler: seating depth, CBTO, bullet jump, vekt, BC",
        "Tennhetter: standard vs magnum, problemer, anbefalinger",
        "Hylser: trimming, neck tension, annealing, prep, levetid",
    ],
    "🔧 DIER & PROSESS": [
        "Die innstilling og justering",
        "Full length vs neck sizing",
        "Seating die funksjon",
        "Crimping (når og hvordan)",
        "Problemløsning (stuck cases, etc)",
    ],
    "📊 TEKNISK": [
        "Trykk: årsaker, tegn, SAAMI-grenser, sikkerhet",
        "Presisjon: forbedring, ES/SD forklaring",
        "Testing: OCW, ladder, test-planer",
    ],
    "🎯 RIFLE & BALLISTICS": [
        "Løpsharmonikk og vibrasjon",
        "Løpslengde effekter",
        "Løpsrengjøring",
    ],
    "🛠️ PRAKTISK": [
        "Verktøy-anbefalinger (nybegynner til avansert)",
        "Komplett ladeprosess steg-for-steg",
    ],
}

for category, topics in categories.items():
    print(f"\n{category}:")
    for topic in topics:
        print(f"  • {topic}")

print("\n" + "=" * 70)
print("\n💡 EKSEMPEL-SPØRSMÅL:\n")

for i, question in enumerate(test_questions[:10], 1):
    print(f"{i:2}. {question}")

print("\n... og mange flere!")

print("\n" + "=" * 70)
print("\n✅ AI-chatten er din venn og ekspert innen lading!")
print("✅ Spør hva som helst - den svarer på norsk eller engelsk!")
print("✅ Detaljerte svar med emojis, lister og praktiske tips!")
print("✅ Sikkerhet alltid i fokus - advarsler når nødvendig!")
print("\n🚀 Start Modern Load Builder og prøv AI-chatten!")
