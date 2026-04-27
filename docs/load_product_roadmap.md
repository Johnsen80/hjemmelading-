# Product Roadmap for Ladedelen

## Status
- Oppdatert: 2026-04-10
- Gjelder: videre produktplan for ladedelen

## Formål

Dette dokumentet låser videre retning for ladedelen som produktets viktigste satsing.

Målet er ikke bare å bygge flere tekniske moduler.

Målet er å gjøre ladedelen til et faglig troverdig, lærende og praktisk system som:

- hjelper brukeren å utvikle tryggere og mer presis ammo
- reduserer bortkastet testing, tid og kostnad
- skiller bedre mellom hva som er målt, modellert, antatt og anbefalt
- lærer rifle, pipe, ladning og brukskontekst å kjenne over tid
- forklarer hvorfor systemet mener det det mener

## Låst prioritering

Denne prioriteringen gjelder til den blir eksplisitt endret:

1. Ladedelen er hovedsatsingen.
2. Scientific Core og lokal læringsmotor prioriteres foran nye sideflater.
3. Spredningslære og årsaksanalyse er en del av kjernen, ikke pynt.
4. Kart/feltballistikk og ammo-testmodul er viktige, men kommer etter at ladekjernen er sterkere.
5. Produktet skal optimaliseres for presisjon i virkeligheten, ikke bare teoretisk fine resultater.

## Produktmål for ladedelen

Ladedelen skal være et offline-first system som lærer rifle, pipe, ladning og brukskontekst å kjenne, slik at brukeren får:

- tryggere beslutninger
- bedre presisjon i virkeligheten
- færre unødvendige tester
- tydeligere neste steg
- dypere forståelse av hva som påvirker trykk, hastighet, samling og robusthet

## Hva "ferdig" betyr for ladedelen

Ladedelen er ikke ferdig bare fordi den har mange skjermer og beregninger.

Den er nær mål når den:

- bruker én tydelig sannhetsmodell for rifle, pipe, pipekonfigurasjon, komponenter, lotter og evidens
- kan rangere datakvalitet og senke anbefalingsstyrken når grunnlaget er svakt
- kan skille mellom lovende enkelttreff og robust, repeterbar ladning
- kan gi neste test med høyest verdi i stedet for å be brukeren skyte tilfeldig videre
- kan forklare om avvik sannsynligvis kommer fra ladning, skytter, miljø eller oppsett
- kan tilpasse anbefalinger etter bruksmål: jakt, konkurranse eller læring/hobby

## Bruksmål i ladedelen

Ladedelen skal støtte tre ulike mål i samme system:

### Jakt
- trygghet og konservativ vurdering
- kaldskudd og praktisk treffpunkt
- terminalt arbeidsvindu og realistisk jaktavstand
- robuste ladninger, ikke bare toppresultat

### Konkurranse
- lav ES/SD og repeterbar samling
- setup-separasjon per rifle, pipe, pipekonfigurasjon og lot
- tydelig historie og sammenligning
- små, presise justeringer med høy sporbarhet

### Læring / hobby
- lav terskel og god forklaring
- enkel registrering og tydelige neste steg
- hjelp til å forstå hva som påvirker hva
- mindre risiko for å trekke feil konklusjoner

## Kjernekapabiliteter som må løftes

### 1. Scientific Core

Dette er grunnmuren under alt annet.

Systemet må bli tydeligere på:

- `measured`
- `modeled`
- `derived`
- `recommended`
- `confidence`
- `uncertainty`
- `evidence quality`

Det må bygges inn som felles motorlag, ikke som spredte signaler i enkeltmoduler.

### 2. Lokal læringsmotor

Programmet skal ikke bare lagre data. Det skal lære:

- hva akkurat denne rifla liker
- hva akkurat denne pipa tåler og responderer på
- hvilke komponent- og lotkombinasjoner som er robuste
- hvordan modell og virkelighet avviker over tid

Læringen må være knyttet til:

- rifle
- pipe
- pipekonfigurasjon
- kule
- krutt
- tennhette
- hylse / lot
- målt chrono
- målt samling
- miljøvindu

### 3. Spredningslære og årsaksanalyse

Dette er en sentral del av produktverdien.

Analysemodulen skal ikke bare si at en gruppe er god eller dårlig.

Den skal forsøke å skille mellom:

- ladningsproblem
- skytterfeil / teknikkproblem
- miljøproblem
- våpen-/oppsettproblem
- blandet eller utilstrekkelig evidens

Den skal bruke:

- gruppemønster
- vertikal vs horisontal spredning
- flyers vs kjernegruppe
- kaldskudd vs oppfølgingsskudd
- chrono-data
- vind og miljø
- skyttekontekst

### 4. Robusthet framfor enkelttreff

Produktet skal rangere og forklare forskjellen mellom:

- beste enkeltskyting
- beste gjennomsnitt
- mest robuste ladning
- beste jaktladning
- beste konkurranseladning

Målet er å finne ladninger som holder seg gjennom små endringer i:

- temperatur
- lot
- seating
- pipekonfigurasjon
- normal bruksvariasjon

### 5. Neste-test-motor

Systemet skal foreslå neste test med høyest verdi.

Det betyr at det må kunne svare på:

- hva bør testes nå
- hva bør fryses
- hva bør forkastes
- hvor store steg bør brukes
- når brukeren bør stoppe videre testing

## Faglige løft som bør inn fra vitenskap/litteratur

Følgende områder skal eksplisitt løftes inn i produktet:

### Måleusikkerhet
- usikkerhet per chrono-oppsett og måleserie
- tydelig svakere tillit ved dårlige måleforhold
- usikkerhet i target-analyse og miljøgrunnlag

### Evidenshierarki
- brukerens målte data i riktig kontekst skal vektes høyest
- publiserte eller generiske data skal være referanse, ikke fasit
- gamle, tynne eller indirekte data skal gi lavere tillit

### Design of Experiments
- bedre testdesign enn rene lineære sweeps
- screening av variabler
- responsflate-tenkning
- stoppkriterier når videre testing gir lav verdi

### Prosessdrift over tid
- pipe-/løpstilstand
- fouling
- rundetelling
- lotskift
- temperaturdrift
- modellbias over tid

### Skille ammoeffekt fra skyttereffekt
- skytestøtte
- stilling
- rytme og seriebrudd
- mønstre som ligner skytterfeil mer enn ladningsfeil

### Bedre drag- og terminalgrunnlag
- sterkere bruk av segmented BC
- transonic-risk og uncertainty
- konservativ terminalvurdering ved svak kuleevidens

## Hovedfaser

## Fase 1: Lås kjernen

Mål:
Gjøre ladedelen til ett sammenhengende produkt i stedet for flere tilstøtende verktøy.

Må være på plass:

- én kanonisk runtime for aktiv ladeutvikling
- tydelig pipe- og pipekonfigurasjonskontekst overalt
- bedre kobling mellom builder, workflow, batch, chrono og target
- samme anbefalingsgrunnlag brukt på tvers av modulene
- mindre legacy-fragmentering

Utfall:

- brukeren forstår hvor sannhetskilden er
- samme ladning oppfører seg likt i alle relevante flater

## Fase 2: Scientific Core

Mål:
Bygge det felles vitenskapelige grunnlaget som alle råd hviler på.

Må være på plass:

- felles input-quality engine
- confidence/uncertainty engine
- målt vs modellert vs anbefalt-lag i payloads og UI
- eksplisitt evidence quality i kritiske vurderinger
- første versjon av måleusikkerhet og datakvalitet per datakilde

Utfall:

- systemet tør å være forsiktig når datagrunnlaget er svakt
- tillit bygges gjennom forklarbarhet

## Fase 3: Læringsmotor per rifle og pipe

Mål:
La systemet lære våpenet å kjenne på en måte som er nyttig i praksis.

Må være på plass:

- lokal læringsprofil per rifle, pipe og pipekonfigurasjon
- lot-læring for kule, krutt, tennhette og hylse
- samlet modellstatus: rå modell, delvis kalibrert, godt kalibrert
- oppdatering av læring fra chrono, target, batch og kalibreringsserier
- eksplisitt modellbias mellom simulert og målt resultat
- læringsmotor som prioriterer neste steg ut fra:
  - trykk/usikkerhet før optimalisering
  - manglende datagrunnlag før fine-tuning
  - bruksmål som jakt, konkurranse eller læring/hobby
- læringsmotor som forklarer:
  - hva systemet vet
  - hva systemet ikke vet ennå
  - hvorfor neste anbefalte test er valgt
- læringsvisning som viser datagrunnlag, svakeste ledd og aktiv tillit per setup
- første praktiske læringsheuristikker for:
  - datastyrke
  - driftstatus
  - signalhint om ammo/setup/trykk eller utilstrekkelig evidens

Utfall:

- systemet kan gi mer kontekstspesifikke råd
- brukeren slipper å starte på nytt hver gang
- læringsrådene blir mer praktiske og mindre generiske

## Fase 4: Spredningslære og årsaksanalyse

Mål:
Hjelpe brukeren å forstå hvorfor gruppen ble som den ble.

Må være på plass:

- klassifisering av spredningsmønstre
- analyse av vertikal, horisontal, flyers og kaldskudd
- kobling mellom target, chrono, miljø og skyttekontekst
- første årsakskategorier:
  - sannsynlig ladningsdrevet
  - sannsynlig skytterdrevet
  - sannsynlig miljødrevet
  - sannsynlig oppsettdrevet
  - blandet / utilstrekkelig evidens

Utfall:

- færre gode ladninger forkastes feilaktig
- færre dårlige ladninger får skylden på skytteren

## Fase 5: Robusthetsmotor og neste-test-motor

Mål:
Gjøre systemet aktivt nyttig i videre testplanlegging.

Må være på plass:

- robusthetsscore for ladning og lot
- rangering av mest robuste kombinasjoner
- forslag til neste test med høyest verdi
- forslag til hva som bør fryses og hva som bør verifiseres
- stoppregler mot overtesting

Utfall:

- mindre tid og penger kastes bort
- mer fokus på høyverdige tester

## Fase 6: Real-world precision verification

Mål:
Verifisere at produktet hjelper brukeren i virkeligheten, ikke bare i modellen.

Må være på plass:

- holdout-verifisering mot nye serier
- test av modell mot ekte bane-/feltdata
- referansedatasett og regresjonstester
- sammenhengende kontroll av at builder, workflow og ballistikk bruker samme logikk

Utfall:

- bedre faktisk troverdighet
- mindre risiko for intern selvmotsigelse

## Konkret prioritering for neste arbeid

### P0 - Må starte nå
- låse en samlet produktretning for ladedelen
- styrke felles scientific core
- gjøre input-quality / evidence-gating tydeligere og mer konsekvent
- styrke pipekonfigurasjons-sensitivitet i læring og anbefaling
- redusere gap mellom bygget logikk og faktisk koblet hovedopplevelse

### P1 - Må bygges før 1.0
- lokal læringsprofil per rifle og pipe
- robusthetsscore og tydelig rangering
- neste-test-motor
- spredningslære / første årsaksanalyse
- konservativ terminalvurdering for jakt
- bedre drag-/BC-håndtering og transonic-risk

### P2 - Viktig, men etter kjernen
- praktisk kart- og feltballistikk
- konkurranseplanlegging på bane
- jaktpostplanlegging med DOPE, sikkerhetsvinkler og bakgrunn
- ammo test & lot validation for bedrifter og testere

Disse sporene er viktige og strategisk sterke, men de skal bygge på en moden ladekjerne i stedet for å konkurrere med den.

## Neste 5 utviklingsblokker

Dette er anbefalt rekkefølge for de neste konkrete arbeidsblokkene.

### Blokk 1 - Samlet sannhetsmodell for ladekjernen

Mål:
Fjerne tvil om hvor aktiv ladetilstand og evidens egentlig bor.

Skal levere:

- én tydelig kanonisk runtime for aktiv ladeutvikling
- konsekvent rifle -> pipe -> pipekonfigurasjon -> session -> batch -> evidence-kjede
- samme aktive kontekst i builder, workflow, batch, chrono og target
- mindre avhengighet av legacy-baner i kjerneflyten

Definition of done:

- samme aktive ladning og pipekonfigurasjon kan åpnes og tolkes likt i alle kjerneflater
- anbefalingsgrunnlaget leses fra samme sannhetskilde

### Blokk 2 - Input quality, confidence og uncertainty

Mål:
Hindre at systemet virker sikrere enn datagrunnlaget tillater.

Skal levere:

- felles input-quality scoring
- tydelig confidence/uncertainty i sentrale vurderinger
- første måleusikkerhetsmodell for chrono, target og miljøgrunnlag
- eksplisitt markering av `målt`, `modellert`, `antatt`, `anbefalt`

Definition of done:

- alle kritiske råd viser evidenskvalitet og viktigste svakhet i grunnlaget
- systemet senker anbefalingsstyrken når data er tynne eller antatte

### Blokk 3 - Læringsprofil per rifle, pipe og lot

Mål:
Begynne å gjøre produktet virkelig lærende i praksis.

Skal levere:

- lokal læringsprofil per rifle, pipe og pipekonfigurasjon
- første samlede bias-/robustness-/confidence-status
- lot-læring for kule, krutt, tennhette og hylse
- modellstatus: `rå modell`, `delvis kalibrert`, `godt kalibrert`

Definition of done:

- chrono, target og kalibreringsserier oppdaterer samme læringsprofil
- brukeren kan se hva systemet faktisk har lært om valgt oppsett

### Blokk 4 - Spredningslære og årsaksanalyse v1

Mål:
Løfte target-/analysebanen fra ren måling til nyttig tolkning.

Skal levere:

- klassifisering av gruppemønster
- skille mellom sannsynlig ladningsfeil, skytterfeil, miljøfeil og oppsettsfeil
- kobling mellom target, chrono, vind og skyttekontekst
- konservativ `ikke nok data`-tilstand når signalet er uklart

Definition of done:

- analyseflaten kan gi første kvalifiserte årsaksvurdering
- brukeren får tydelig forslag til hva som bør verifiseres videre

### Blokk 5 - Robusthetsmotor og neste-test-motor

Mål:
Gjøre systemet bedre til å spare brukeren tid, komponenter og penger.

Skal levere:

- robusthetsscore for ladninger og lotter
- forskjell mellom toppresultat og robust resultat
- forslag til neste test med høyest verdi
- forslag til hva som bør fryses, hva som bør justeres og hva som bør stoppes

Definition of done:

- systemet kan rangere en ladning som `lovende`, `robust`, `ustabil`, `må verifiseres`
- systemet kan gi en konkret neste test i stedet for bare generell oppfordring til mer testing

## Konkret arbeid per blokk

For å gjøre blokkene operative bør hver blokk brytes i samme mønster:

1. Datamodell og sannhetskilde
2. Service-/motorlag
3. UI-visning og forklaring
4. Testdekning og referansedata
5. Enkel dokumentasjon og produktregel

## Hva som bevisst ikke prioriteres før disse blokkene er i gang

- større utvidelser i kartdelen
- full konkurransebanemodell
- jaktpostplanlegging med sikkerhetssektorer
- profesjonell ammo test & lot validation som hovedsatsing
- flere sideverktøy som ikke styrker ladekjernen direkte

Disse områdene er strategisk riktige senere, men skal bygge på at ladekjernen allerede har bedre evidensmotor, læringsmotor og årsaksanalyse.

## Senere moduler som skal bevares i retningen

### Feltballistikk og kart

Denne delen skal senere brukes til:

- planlegging av konkurransescenarioer på ulike baner
- planlegging av jaktposter
- analyse av vær, vind, terreng, vinkler og sikkerhetsforhold
- DOPE og praktiske konsekvenser i felt
- læring og bevisstgjøring rundt virkelige forhold

Denne modulen skal være et verktøy og en pedagogisk flate, men den er ikke hovedfokus før ladekjernen er sterkere.

### Ammo Test & Lot Validation

Denne delen skal senere brukes av:

- bedrifter
- ammo-testere
- avanserte brukere som vil teste fabrikkammo og lotter systematisk

Den skal kunne:

- registrere testforhold og ammo-data
- bruke chrono, samlingsbilder og miljødata
- sammenligne lotter og testserier
- vurdere robusthet, avvik og praktisk egnethet

Det finnes spor av denne retningen i prosjektet, men den skal prioriteres etter ladekjernen.

## Konkrete prinsipper for videre arbeid

- Ikke bygg flere parallelle sannhetsmodeller.
- Ikke prioriter ny skjermflate foran bedre evidensmodell.
- Ikke la systemet virke sikrere enn datagrunnlaget tillater.
- Ikke optimaliser bare for små grupper; optimaliser for robuste og brukbare ladninger.
- La produktet hjelpe brukeren å tenke bedre, ikke bare registrere mer.
- Hver sentral anbefaling skal kunne forklares med data, effekt, confidence, uncertainty og neste verifisering.

## Neste dokumenter som denne roadmapen skal styre

- `project_todo.md`
- `load_block1_execution_plan.md`
- `load_module_blueprint.md`
- `scientific_accuracy_todo.md`
- `release_1_0_roadmap.md`

Denne roadmapen skal brukes som produktmessig filter for videre prioritering i ladedelen.
