# Plattformplan for ladeutvikling og analyse

## Status 2026-04-03

Dette er retningen som na bor styre neste store loft i laddedelen:

- laddedelen skal vaere vapenstyrt fra forste skjerm
- aktiv pipe eller lop skal vaere obligatorisk kontekst for simulering, analyse og anbefaling
- brass-data under pipeprofil er ikke bare metadata, men fysikk- og evidensdata
- H2O, skuldermalinger og andre hylsemal ma kunne spores til hvilken ladning som formet hylsa
- pipeprofilen skal ikke bare lagre geometri, men ogsa kronografdata, samlingsbilder og testhistorikk
- harmonikk skal vaere en aktiv del av ladningsvurderingen, ikke bare et sideverktuy
- demper, brems, pipeprofil, innfestning, fri flukt, twist og rifleretning skal inngaa i vurderingen
- kuledata som lengde, diameter, boat tail, base-type, tip-type, konstruksjon og BC ma brukes aktivt i simulering og analyse
- kulebiblioteket ma videreutvikles til et prosjektilbibliotek med data for jakt- og terminal oppforsel der det er relevant
- kruttdata som energitetthet, burn-rate-parametre, temperaturdata, valideringsstatus og simuleringsparametre ma brukes aktivt i simulering og analyse
- bruksmal som subsonisk, jakt, presisjon og langhold skal styre hva som anbefales
- systemet skal vaere selvlærende per vapen + pipe + ladning + lot
- brukeren skal kunne overstyre masterdata med egne malinger og egne felt uten a miste originaldata

## Ny hovedmodell

Programmet bor tenke slik:

- vapenprofil + aktiv pipe + brass-baseline + komponentlotter + ladning + malt data = beslutningsgrunnlag

Dette betyr i praksis:

- vapenprofil er toppniva
- pipeprofil er operativ enhet
- brass-baseline er pipe-spesifikk
- ladning vurderes alltid i kontekst av valgt pipe
- kulebiblioteket ma behandles som et fysikkbibliotek, ikke bare et navne- og vektregister
- kronograf, samlingsbilder og observasjoner bygger kunnskap for akkurat den pipa
- harmonikk, trykk, stabilitet, ytre ballistikk og terminal vurdering ma bruke samme datagrunnlag
- anslagsenergi, impact velocity, ekspansjonsvindu og bruksegnethet ma kunne vurderes nar kuledataene er gode nok
- brukerdata skal vinne over masterdata nar brukeren har bedre, malte eller lot-spesifikke verdier

## Status 2026-03-23

Arbeid som faktisk er pa plass i kodebasen na:

- vapenprofil stotter bade rifle og pistol
- ett vapen kan ha flere piper eller lop med eget kaliber, brukstype, status og aktivt valg
- pipe- eller lopprofil kan lagre munningsutstyr, pipeprofil, innfesting og pipe-spesifikke hylsemal
- H2O eller case capacity kan registreres fra skutte hylser med flere malinger og automatisk snitt
- ladeutvikling, simulering, ballistikk og harmonikk bruker aktiv pipe eller lop
- builderen har datagrunnlag-boks, kalibreringstabell, filtrering og enkle trendgrafer
- kalibreringsserier kan lagres med kule, krutt, charge, settedybde, neck tension, chrono, gruppe, bilde, avstand og temperatur
- builderen kan filtrere og analysere serier per krutt, kule, lot, avstand og temperatur
- builderen har enkel temperaturdrift-visning og temperaturgraf
- brukeren kan registrere og redigere egne kuler og krutt direkte fra builderen
- systemet gir na enklere vurdering av om kule og krutt ser ut til a passe i valgt rifle og pipe, inkludert Sg-estimat nar nok data finnes
- manglende harmonikk- og stabilitetsdata synliggores bedre, med enklere vei tilbake til riktig profilredigering
- vapenprofilen kan apne builderen direkte med valgt pipe eller lop
- kuleeksport finnes na og viser at vi har et bredt datagrunnlag med lengde, diameter og andre kulefelt som kan brukes mer aktivt i motoren

## Formål

Målet er å bygge en helhetlig plattform for ladeutvikling, analyse, ballistikk, våpenprofiler, batchstyring og test/logging.

Programmet skal ikke bare være en kalkulator, men et system som hjelper brukeren med å:

- forstå hva som skjer når en variabel endres
- simulere og planlegge ladninger
- sammenligne simulert og målt resultat
- logge testdata på en strukturert måte
- koble ladning, våpen, optikk og resultat sammen
- bruke historikk til å gi bedre råd over tid

Dette skal være nyttig for:

- hobbybrukere
- jegere
- konkurranseskyttere
- avanserte hjemmeladere
- testmiljøer
- produsenter og ammo-utviklere
- vitenskapelig og systematisk bruk

## Produktvisjon

Programmet skal være et intelligent analyse- og utviklingsmiljø for ammunisjon, våpen, optikk og ballistikk, der brukeren kan forstå, simulere, teste, justere og dokumentere hele utviklingsprosessen visuelt og systematisk.

## Det vi er enige om

Dette er hovedpunktene som er landet så langt:

- programmet skal være en plattform, ikke bare en kalkulator
- ladeutvikling er hovedkjernen i systemet
- brukeren skal velge våpenprofil først når ladeutvikling startes
- våpenprofilen skal støtte både rifle og pistol
- pistol skal behandles som en førsteborger i produktet, ikke som et etterpåheng
- ett våpen kan ha flere piper eller løp med eget kaliber og egen historikk
- AI skal være inne i arbeidsflyten, ikke som en løs og isolert chat
- systemet skal støtte både batch-basert arbeid og fri oppbygging
- systemet skal være visuelt og pedagogisk, ikke bare tabeller og rå tall
- systemet skal hjelpe brukeren med å legge inn riktige data og redusere vanlige feil
- systemet skal støtte både metriske og imperiale enheter på en trygg og tydelig måte
- språk og enheter skal ikke låses hardt sammen; brukeren må kunne velge enheter per fagområde
- systemet skal gjøre det lett for brukeren å stille spørsmål når noe er uklart
- harmonikkdelen skal hjelpe med anbefalte testområder, ikke late som den har en absolutt fasit
- systemet må tydelig skille mellom simulert data og målt data
- systemet må tydelig skille mellom masterdata, brukerdata, lotdata og beregnede data
- optikk, null og klikk må være integrert i ladeutviklingen
- historikk og læring skal være knyttet til våpenprofil, prosjekt og batch
- kalibrering, hylsemål, H2O-volum og munningsutstyr må kunne knyttes til valgt pipe eller løp
- kronografdata, samlingsbilder og testhistorikk må kunne knyttes til valgt pipe eller løp
- brass-baseline må kunne spores til ladningen som formet hylsa
- harmonikkvurdering må bruke pipeprofil, brass-data og faktisk testhistorikk sammen
- kulegeometri og konstruksjonsdata ma brukes direkte i stabilitet, seating/jump, harmonikk, ytre ballistikk og terminal vurdering
- bedre kuledata skal ogsa brukes til jaktrelevant vurdering som impact velocity, anslagsenergi, forventet ekspansjonsvindu og egnet hold
- plattformen skal kunne brukes av hobbybrukere, jegere, konkurranseskyttere, utviklere og labmiljøer
- brukeropplevelsen skal være bedre, mer moderne og mer forklarende enn GRT og QuickLOAD
- sikkerhetsgrenser må være tydelige, særlig i ballistikk- og planleggingsdelen

## Rifle og pistol

Plattformen skal bygges for begge hovedspor:

- rifle
- pistol

Det betyr at videre utvikling ikke skal anta at rifle er standard dersom det påvirker modell, UI eller arbeidsflyt.

Konkrete følger:

- våpenprofil må støtte rifle og pistol like godt
- laddedelen må kunne åpnes for begge våpentyper uten spesialomveier
- analyser må tåle at noen vurderinger er rifle-spesifikke, mens andre er pistol-spesifikke
- harmonikk, langhold og spindrift er primært rifle-spor
- funksjon, rekylsystem, pipe-/sleideoppførsel og kortere avstander blir viktigere i pistol-sporet
- subsonisk arbeid, kortpipe, munningshastighet, funksjonssikkerhet og presisjon på praktiske hold må kunne vurderes for pistol
- brukergrensesnitt, enheter, historikk, lotter og evidens skal være felles der det gir mening, men faglogikken må kunne skille våpentypene

Minimumskrav videre:

- ikke hardkode rifle som skjult standard i nye features
- nye analysekort må kunne vite om de gjelder rifle, pistol eller begge
- anbefalingsmotoren må kunne velge enklere og mer relevante råd når våpentype er pistol

## Terminologi

Begrepet som skal brukes i prosjektet er:

- ladeutvikling

Ikke:

- lastutvikling

## Hovedprinsipp

Brukeren skal starte ladeutvikling ved å velge våpenprofil først.

Anbefalt startflyt:

1. Velg våpenprofil
2. Velg aktiv pipe eller løp, optikk og nullprofil
3. Velg bruksmål: subsonisk, jakt, presisjon, langhold, trening eller lab
4. Velg komponentmodus: fra batch eller fritt
5. Velg brass/hylsebatch, kulelot, kruttlot og tennhettelot
6. Bygg ladning
7. Simuler og juster
8. Se harmonikk, trykk, stabilitet, ytre og terminal vurdering i samme flyt
9. Logg målt resultat, kronograf og samlingsbilder
10. Sammenlign simulert mot målt
11. Lagre og bruk historikken videre

## Språk og enhetsstrategi

Produktet kan gjerne ha engelsk som sterkt hovedspor for marked og salgbarhet, men enheter må være fleksible og styres separat fra språk.

Praktisk hovedregel for videre arbeid:

- produktets primærspråk skal være engelsk
- nye UI-tekster bør skrives på engelsk som standard
- norsk kan støttes via oversettelser, men ikke være skjult standard i nye skjermer

Hovedregel:

- bruker skal kunne velge språk
- bruker skal kunne velge enheter separat for hver kategori
- språkvalg skal ikke tvinge fram ett bestemt målesystem

Dette er viktig fordi mange brukere blander systemer i praksis, for eksempel:

- twist som `1:11"` eller `1:10"`
- øvrige våpen- og hylsemål i `mm`
- kulevekt i `grain` eller `gram`
- kruttvekt i `grain` eller `gram`
- hastighet i `fps` eller `m/s`
- trykk i `bar`, `psi` eller `MPa`
- avstand i `meter` eller `yard`
- gruppestørrelse i `mm`, `MOA` eller `mil`

Produktet bør derfor støtte:

- globale språkvalg
- fleksible enhetsprofiler
- manuell overstyring per kategori
- egne presets, for eksempel:
  - Norge blandet
  - Full metric
  - US / Imperial
  - PRS / langhold
  - Jakt / Europa
- manuell finjustering per kategori

Minimumskategorier for egne enhetsvalg:

- kulevekt
- kruttvekt
- hastighet
- trykk
- lengde
- twist-visning
- temperatur
- avstand
- gruppestørrelse

Presets skal bare være startpunkt.

Brukeren må alltid kunne overstyre hver enkelt kategori manuelt etterpå.

Dette skal regnes som en del av kjerneproduktet, ikke som en sen kosmetisk forbedring.

## Pipeprofil som laerende enhet

Hver pipe eller hvert lop bor ha sin egen kunnskapsflate.

Under hver pipe bor systemet kunne lagre:

- geometri og konfigurasjon
- brass-baseline
- hvilken ladning som formet baseline
- kronografserier
- bilder av samlinger
- gruppestorrelser
- trykktegn og observasjoner
- lotbytter og effekter av disse
- harmonikk-score, node-band og confidence

Pipeprofilen skal dermed ikke bare vaere et sted for statiske data, men et sted der programmet bygger kunnskap over tid om hva som faktisk fungerer.

## Brass-baseline og observasjoner

Brass-data under vapen- og pipeprofil ma skilles i to lag:

1. Brass baseline
- H2O / case capacity
- base-to-datum
- shoulder bump
- neck diameter
- trim length
- fireformed referanse

2. Brass observation
- hvilken ladning som ble brukt
- kule og kulelot
- krutt og kruttlot
- charge
- COAL / CBTO / settedybde
- tennhette og lot
- dato, temperatur og pipe
- eventuelle trykktegn

Dette gjor at systemet kan vite hvilket trykk- og formingsregime en bestemt hylsemaling kommer fra.

## Harmonikk som aktiv beslutningsstotte

Harmonikkdelen skal ikke leve ved siden av ladeutvikling, men vaere en del av den.

For hver ladning i valgt pipe bor systemet vise:

- harmonikk-score
- node-fit
- barrel time
- charge sensitivity
- seating sensitivity
- confidence
- hvordan pipeprofil, innfestning, fri flukt og munningsutstyr pavirker vurderingen
- hvordan kulelengde, base-type, tip-type, konstruksjon og BC pavirker stabilitet, seating og terminal vurdering

Brass-baseline, H2O og skutte-hylse-malinger skal brukes til a forbedre internballistikken, som igjen forbedrer barrel time og node-vurdering.

## Samlet anbefalingsmotor

Neste store tekniske grep bor vaere ett samlet service-lag som samler logikken som i dag er spredd.

Det laget bor bruke:

- vapenprofil
- aktiv pipe
- brass-data
- komponenter og lotter
- kuledata og kulegeometri
- kruttmasterdata og simuleringsdata
- ladning
- miljo
- historiske malinger
- bruker-overstyringer og egne malte data

Det laget bor returnere:

- trykkvurdering
- harmonisk fit
- stabilitetsvurdering
- internballistisk sammendrag
- ytre ballistisk sammendrag
- terminal vurdering
- datakvalitet
- vurdering av kuledata og eventuell manglende kulegeometri
- vurdering av terminal egnethet nar prosjektildataene er sterke nok
- anbefalt charge-vindu
- anbefalt seating-vindu
- neste anbefalte test

## Nyskapning og differensiering

Hvis plattformen skal loftes noen tydelige hakk over vanlige reloading-apper og ogsa ga utover klassiske simuleringsverktoy, bor vi satse pa det konkurrentene ofte mangler:

- pipe-spesifikk laering, ikke bare generelle kalkyler
- neste beste test, ikke bare et statisk charge-vindu
- tydelig usikkerhet og tillit, ikke bare pene tall
- forklarende visualisering, ikke bare flere tabeller

De mest lovende nyskapende sporene er:

1. Digital tvilling per pipe
- systemet bor bygge en laerende modell av hva akkurat denne pipa liker
- den skal bruke geometri, brass-baseline, lotter, chrono, grupper, trykktegn og harmonikk sammen
- den skal vite hvilke noder som faktisk holder over tid, ikke bare hvilke som ser lovende ut i en simulering

2. Neste beste test-motor
- programmet bor foresla hvilken test som gir mest nytte per skudd
- det kan vaere charge-stige, seating-test, lotverifisering, temperaturserie eller ren kontrollserie
- anbefalingen bor bygge pa hva som allerede er malt, hvor usikkerheten er storst, og hva bruksmalet er

3. Tillitskart for hver ladning
- hver ladning bor vise hva som er:
  - malt
  - simulert
  - avledet
  - antatt
- dette gjor det lettere a se hvor modellen er sterk og hvor brukeren bor vaere konservativ

4. Presisjon som stabilitet, ikke bare beste gruppe
- programmet bor bruke repeterbarhet, mean radius, temperaturrobusthet, lotrobusthet og ES/SD sammen
- malet er a rangere hvor stabil en ladning faktisk er, ikke bare hvilken serie som ga den peneste gruppa en gang

5. Malbasert optimalisering
- brukeren bor kunne velge hva som er viktigst:
  - stillest mulig sub
  - trygg jaktladning
  - minste ES/SD
  - beste langholdsprofil
- anbefalingene bor deretter optimaliseres mot det malet i stedet for en generell standardlogikk

6. Forklarende 3D der det faktisk hjelper
- 3D bor brukes bare der det gjor geometri lettere a forsta
- de beste kandidatene er:
  - kammer/patron-fit
  - jump/freebore
  - seating geometry
  - hylsevolum og fyllingsgrad

7. Prosjektilbibliotek med bruksvurdering
- kulebiblioteket bor utvikles til et rikere prosjektilbibliotek, ikke bare et BC-register
- det bor kunne bruke konstruksjonstype, minimum impact velocity, ekspansjonsvindu og bruksmal i vurderingen
- dette gjor jaktvurdering, anslagsenergi og praktisk egnethet mer relevante enn rene banetall alene

Dette er sporene som mest sannsynlig kan gjore plattformen merkbart mer moderne og nyttig enn bade klassiske kalkulatorer og enkle loggboker.

## Kommersiell verdi, eierskap og risikoreduksjon

Hvis plattformen en dag skal kunne selges til et firma, ma vi ikke bare tenke funksjoner. Vi ma ogsa bygge produktet pa en mate som oker verdi og reduserer usikkerhet for en eventuell kjoper.

Det som mest sannsynlig vil drive salgspris og strategisk verdi er:

- eierrett til data og teknologi
- hvor unik motoren faktisk er
- hvor mye utviklingstid og risiko en kjoper sparer
- om plattformen kan videreutvikles og selges videre
- hvor ferdig, testet og dokumentert systemet er
- hvor ryddig IP, datakilder og provenance er

De storste usikkerhetene vi ma jobbe aktivt med er:

1. IP- og datakilde-ryddighet
- det ma vaere tydelig hva som er vart eget arbeid
- import- eller ingest-spor ma kunne skilles fra sluttproduktet
- data som brukes videre ma vaere normalisert, beriket og eid i vart eget domene
- vi ma kunne dokumentere hvilke datakilder som er brukt, hva som er beholdt, og hva som er transformert

2. Modenhetsgrad
- koden ma bli mer samlet, testet og forutsigbar
- kjerneflytene ma vaere stabile
- brukeropplevelsen ma oppleves som ett produkt, ikke en samling verktoy
- vi ma redusere teknisk og produktmessig risiko for en eventuell kjoper

3. Dokumentert kommersiell brukbarhet
- plattformen ma vise at den faktisk loser et tydelig problem bedre enn alternativene
- de viktigste differensiatorene ma kunne demonstreres
- det ma vaere lett a forklare hvorfor en kjoper sparer tid, penger eller utviklingslop ved a overta dette

Dette betyr at vi ma styre utviklingen etter tre parallelle mal:

- bygge et bedre produkt
- bygge egen IP og eget dataeierskap
- bygge dokumentert verdi for en framtidig kjoper

For hver stor endring bor vi derfor sporre:

- styrker dette vart eget eierskap til teknologien?
- gjor dette produktet mer unikt?
- reduserer dette risiko for en framtidig kjoper?
- blir det enklere a forklare og demonstrere verdien?

## Statusmatrise for verdi og salgbarhet

Dette er en arbeidshypotese for hvor vi ligger akkurat na. Tallene er ikke juridiske eller finansielle sannheter, men et praktisk styringsbilde for videre arbeid.

### 1. Eierrett til data og teknologi: 55-65 %

Bra na:
- mye av dataen er hentet inn, normalisert, beriket og brukt i egne modeller
- aktiv UI og logikk er flyttet mer over i vart eget domene
- vi bygger egne service-lag, helsemodeller, tillitskart og anbefalingslogikk

Mangler:
- full IP- og datakildeoversikt
- full opprydding av gamle ingest- og kompatibilitetsspor
- tydeligere dokumentasjon pa hva som er egne transformasjoner og egen teknologi

### 2. Hvor unik motoren faktisk er: 60-70 %

Bra na:
- vapenprofil, pipeprofil, brass, lotter, malinger og analyse henger sammen
- harmonikk, fyllingsgrad, forbrenning, evidens og tillitskart er pa vei inn i samme motor
- pipehistorikk og lot-laering begynner a bli reelle differensiatorer

Mangler:
- digital tvilling er ikke fullt bygd
- neste beste test-motor er bare delvis der
- fysikkmotor og presisjonsmodell kan fortsatt loftes flere hakk

### 3. Hvor mye tid en kjoper sparer: 65 %

Bra na:
- mye struktur og retning er allerede bygd
- datainnhenting, modellering, lotlogikk og workflow er kommet langt
- en kjoper ville slippe mye grunnarbeid

Mangler:
- mer moden og gjennomtestet kjerne
- mindre overlapp og mindre arv fra eldre spor

### 4. Om dette kan bli et produkt de selger videre: 60 %

Bra na:
- det finnes en tydelig plattformretning
- produktet er mer enn en prototype
- det kan bli et premium nisjeprodukt

Mangler:
- mer helhetlig UI og samlet hovedflyt
- tydeligere pakking som ett produkt, ikke flere delsystemer
- sterkere dokumentasjon av differensiatorer

### 5. Hvor ferdig og risiko-redusert det er: 40-50 %

Bra na:
- mange sentrale funksjoner finnes
- builder, profiler og referansevisninger snakker mer samme sprak
- plan og arkitektur er mye tydeligere enn tidligere

Mangler:
- mer testdekning og stabilitetsarbeid
- mindre teknisk mellomlag og mindre gammel struktur
- mer produktpolish og ferdig samling

### 6. IP- og datakilde-ryddighet: 35-45 %

Bra na:
- retningen er tydelig: data skal bli vart eget domene
- synlig sprak og hovedflyt er blitt mye mer nøytral
- nøytrale service-lag er pa plass flere steder

Mangler:
- mer intern opprydding
- tydelig provenance- og transformasjonsdokumentasjon
- ingest-broen lever fortsatt som teknisk arv

### 7. Modenhetsgrad: 50-60 %

Bra na:
- sterk grunnmur
- mye funksjonalitet henger sammen
- produktretningen er tydelig

Mangler:
- mer robusthet, testbarhet og opprydding
- mer samlet og ferdig brukeropplevelse

### 8. Dokumentert kommersiell brukbarhet: 30-40 %

Bra na:
- vi ser tydelig verdi og differensiering
- det finnes en sterk produktfortelling i emning

Mangler:
- tydelig ROI-/verdiargumentasjon
- sterkere demonstrasjon av hvorfor dette er bedre enn alternativene
- bedre pakking for overdragelse eller salg

## Samlet vurdering akkurat na

- teknologisk potensial: hoyt
- produktmessig potensial: hoyt
- kommersiell salgsklarhet akkurat na: middels
- IP- og overdragelsesryddighet akkurat na: middels til svak

Konklusjonen er at vi ligger bra an pa ide, motor og retning, middels bra an pa produktisering, og svakere an pa full IP-ryddighet og salgsklar pakking. Det er derfor riktig a jobbe videre med bade produkt, egen IP og modenhet samtidig.

## Hva ma fikses na for vi bygger videre

For a unnga a bygge oss inn i mer teknisk gjeld, mer uklart dataeierskap og mer overlapp, bor vi ta en egen oppryddings- og spikringsfase na.

Denne fasen har ett mal:

- rydde arkitektur, datamodell og provenance nok til at videre arbeid skjer pa trygg grunn

Dette er lettere a gjore na enn senere, fordi:

- gammel ingest-tenkning fortsatt finnes i deler av koden
- noen service-lag overlapper fortsatt
- datamodellen er sterk, men ikke fullt spikret som eneste sannhet
- IP- og provenance-arbeid er billigere mens vi fortsatt har full oversikt

### Hoy prioritet: ma tas tidlig

1. Rydd domenet helt
- nøytrale moduler ma vaere hovedspor
- gamle ingest- og kompatibilitetslag ma bli tynne aliaser eller fases ut
- brukerflyten ma ikke lekke gammel datakildetenking

2. Frys kjernedatamodellen
- definer tydelig sannhetskilde for:
  - vapenprofil
  - pipeprofil
  - brass-baseline
  - lotter
  - ladning
  - malinger
  - referanse/simulering
  - evidens, helse og tillit

3. Lag provenance- og IP-struktur
- dokumenter hva som er:
  - masterdata
  - brukerdata
  - transformert data
  - egen analyse/logikk
  - midlertidig ingest-bro

4. Samle de viktigste service-lagene
- samlet motor, evidensmodell, helsesammendrag, tillitskart og ladningskort ma ha tydelige hovedinnganger
- unnga at samme oppsummering bygges flere steder i UI

5. Definer MVP-kjernen hardt
- dette ma vaere produktets ufravikelige kjerne:
  - vapenstyrt laddedel
  - pipe/brass/lot-kontekst
  - simulering + analyse
  - malinger + evidens
  - neste steg

### Middels prioritet: bor tas rett etter

6. Styrk tester og stabilitet rundt kjernen
- prioriter importtester, smoke-tester og noen tydelige kjernetester
- builder, profilvisning, service-lag og vapenprofilflyt ma verifiseres jevnlig

7. Lag tydelig produktfortelling
- hva er produktet?
- hvem er det for?
- hvorfor er det bedre?
- hva er unikt og eget?

8. Lag enkel IP- og datakildeoversikt
- dette bor vaere et eget dokument som en framtidig kjoper eller partner kan lese

### Lavere prioritet: etter at grunnmuren er trygg

9. Stor 3D-satsing
- kun nar hovedflyt, fysikk, datamodell og kommersiell retning er stabile

10. Bred sideverktoyvekst
- nye delmoduler ma ikke stjele fokus fra kjerneplattformen

## Veien videre til 100 % ferdig produkt

For a komme helt i mal bor vi tenke i faste faser, ikke bare enkelttiltak.

### Fase 1: Rydding og grunnmur

Mal:
- rydde domenet
- spikre kjernedatamodellen
- dokumentere provenance og IP-struktur
- redusere gammel ingest-arv

Ferdig nar:
- kjerneflyten bruker nøytrale moduler
- kjernedata har tydelige sannhetskilder
- provenance og datatyper er dokumentert

Leveranser i denne fasen:

- `KJERNDATAMODELL_OG_SANNHETSKILDER.md`
- `IP_OG_PROVENANCE_OVERSIKT.md`

### Fase 2: Samlet motor og felles arbeidsflate

Mal:
- samle fysikk, evidens, tillit, helse og anbefaling i ett tydelig tjenestelag
- builder, profilvisning og referansevisning skal bruke samme modell

Ferdig nar:
- samme ladningskort og tillitsmodell brukes pa tvers av kjerneflatene
- charge, seating, trykk, forbrenning, lotter og brass leses fra samme motor

### Fase 3: Pipe-laering og malebasert styring

Mal:
- gjore pipa til en ekte laerende enhet
- styrke brass, lotter, chrono, grupper og harmonikk som samlet evidens

Ferdig nar:
- hver pipe har brukbar historikk, baseline og laering
- systemet kan gi mer pipe-spesifikke rad enn generelle simuleringer alene

### Fase 4: Innovasjonssporene blir ekte funksjoner

Mal:
- bygge neste beste test-motor
- bygge ekte tillitskart
- loft presisjonsmodellen
- starte digital tvilling-logikk

Ferdig nar:
- systemet ikke bare viser tall, men prioriterer hva brukeren bor teste og hvorfor

### Fase 5: Kommersiell modning

Mal:
- dokumentere verdi
- redusere risiko
- styrke salgbarhet og overdragbarhet

Ferdig nar:
- IP-/datakildebildet er ryddig
- ingest-broen kan fjernes fra sluttproduktet
- produktfortelling, demonstrerbar verdi og modenhet er pa plass

### Fase 6: Ferdig produkt

Mal:
- helhetlig, stabil og salgbar plattform

Et 100 % ferdig produkt betyr at:

- kjerneflyten er hel og lett a forsta
- fysikk, evidens, tillit og anbefaling henger sammen
- dataeierskap og provenance er ryddig
- UI oppleves som ett produkt
- kjernefunksjonene er stabile og testet
- gamle ingest-spor ikke trengs i sluttproduktet
- plattformen kan demonstreres, brukes og eventuelt overdras med lavere risiko

## Oppdatert prioritert todo

### Na

- [ ] Ta en egen rydde- og spikringsfase for domenet for vi bygger videre tungt
- [ ] Gjor nøytrale moduler til reelt hovedspor og reduser gamle ingest-/kompatibilitetslag
- [ ] Frys kjernedatamodellen og dokumenter sannhetskildene
- [ ] Holde `KJERNDATAMODELL_OG_SANNHETSKILDER.md` oppdatert nar kjernemodellen endres
- [ ] Gjor vapenprofil til inngangen til laddedelen
- [ ] Gjor aktiv pipe eller lop til obligatorisk kontekst
- [ ] Bygg ut `src/ballistics/services.py` som samlet anbefalingsmotor
- [ ] Koble `src/modules/modern_load_builder.py` til dette service-laget
- [ ] Bruk harmonikk fra `src/utils/rifle_harmonics.py` direkte i ladningsvurderingen
- [ ] Bruk brass-data under pipeprofil aktivt i simuleringen
- [ ] Bruke kuledata som lengde, diameter, boat tail, tip-type, konstruksjon og BC aktivt i stabilitet, seating og terminal vurdering
- [ ] Utvide kulebiblioteket til et prosjektilbibliotek med tydelig konstruksjonstype, bruksmal og jaktrelevante felt der data finnes
- [ ] Lagre hvilken ladning som formet brass-baseline
- [ ] Koble inventory-lotter til kule, krutt, tennhette og hylsebatch i laddedelen
- [ ] Vis valgt pipekonfigurasjon tydelig i ladningskortet
- [ ] Fjerne rester av Gordon/GRT-sprak fra vanlig brukerflyt
- [ ] Bygge grunnlaget for et tillitskart som skiller mellom malt, simulert, avledet og antatt data
- [ ] La builder og profilvisning bruke samme forklarende helse- og evidensmodell
- [ ] Dokumentere tydelig hva som er egen teknologi, egne modeller og egne transformasjoner av data
- [ ] Skille ingest/importspor fra sluttproduktet enda tydeligere, slik at broen kan fjernes senere
- [ ] Redusere synlige og interne rester av gammel datakildetenking der det ikke lenger trengs
- [ ] Lage en enkel provenance- og IP-struktur for masterdata, brukerdata, transformert data og egen logikk
- [ ] Holde `IP_OG_PROVENANCE_OVERSIKT.md` oppdatert nar ingest, transformasjon eller eierskap endres
- [ ] Definere MVP-kjernen hardt sa videre utvikling holder fokus

### Snart

- [ ] Gi hver pipe egen testhistorikk
- [ ] La pipeprofilen lagre kronografdata per test
- [ ] La pipeprofilen lagre bilde av samling per test
- [ ] Koble testoppforinger til konkret ladning og lotter
- [ ] Bruke kronograf og gruppedata under pipeprofilen til a forbedre harmonikk-confidence
- [ ] La bruksmal styre anbefalingene: subsonisk, jakt, presisjon, langhold, trening
- [ ] La anbefalingsmotoren foresla charge-vindu og seating-vindu
- [ ] Heve kulebiblioteket fra katalog til fysikkbibliotek med tydelig kvalitet pa kulelengde, base-type, tip-type og konstruksjon
- [ ] Koble ytre ballistikk sterkere til valgt bruksmal
- [ ] Legge til terminal vurdering per bruksmal
- [ ] Bruke bedre kuledata til a vurdere impact velocity, anslagsenergi og ekspansjonsvindu for jaktrelevante hold
- [ ] Skille tydelig mellom ren energivurdering og faktisk terminal egnethet i UI og motor
- [ ] Bygge et tydelig "neste steg"-kort i UI
- [ ] Lage en "neste beste test"-motor som prioriterer testtypen med hoyest laeringsverdi
- [ ] Bygge et ekte tillitskart per ladning og pipe
- [ ] Loft presisjonsvurderingen fra beste gruppe til stabilitetsvurdering med repeterbarhet og mean radius
- [ ] La bruksmal styre optimalisering av anbefalingene tydeligere enn i dag
- [ ] Lage en enkel IP- og datakildeoversikt som viser hva som er masterdata, brukerdata, transformerte data og egen logikk
- [ ] Bygge mer dokumentert modenhet gjennom tester, stabile kjerneflyter og enklere demonstrasjon av verdi
- [ ] Lage en tydelig produktfortelling for hvorfor plattformen er bedre enn kalkulatorer og enkle loggboker
- [ ] Samle builder, profilvisning og referansevisning rundt samme kjernearbeidsflate
- [ ] Gjor pipe-laering og malehistorikk til tydelig kjerne i produktet

### Senere

- [ ] Kalibrere modellen per vapen + pipe + ladning + lot
- [ ] Lage personlig harmonikkmodell per pipe
- [ ] La systemet laere av kronograf, grupper og trykktegn over tid
- [ ] Bygge bedre prediksjon av seating-vindu basert pa faktisk pipehistorikk
- [ ] Modellere usikkerhet eksplisitt i anbefalingene
- [ ] Lage digital tvilling per pipeprofil
- [ ] La systemet laere POI-shift ved bytte av demper eller brems
- [ ] Bruke rifleretning og twist sterkere i ytre ballistikk og spindrift
- [ ] Modellere kuleform og konstruksjon tydeligere i terminaldelen, inkludert jakttype, matchtype og monolittiske prosjektiler
- [ ] Modellere terminal oppforsel tydeligere med minimum impact velocity, ekspansjonsvindu, restvekt/penetrasjonsprofil der data finnes
- [ ] La terminal vurdering bruke bade prosjektilbibliotek, ytre ballistikk og faktisk bruksmal sammen
- [ ] Legge til 3D bare der det gir praktisk verdi, som kammer/patron-fit og jump/freebore
- [ ] Gjore hele laddedelen til en laerende arbeidsflate per pipe
- [ ] Gjore den digitale tvillingen per pipe til en reell laeringsmotor
- [ ] Bruke malbasert optimalisering aktivt for subsonisk, jakt, presisjon og langhold
- [ ] Legge til forklarende 3D for kammer, jump, seating og fyllingsgrad der det gir pedagogisk verdi
- [ ] Rydde ingest-broen helt ut av sluttproduktet nar all nodvendig data er trygg hos oss
- [ ] Pakke plattformen som en tydelig overdragbar teknologi med lavere kommersiell risiko

## Oppstart og menyvalg når programmet åpnes

Når programmet starter, skal brukeren ikke kastes rett inn i et tilfeldig verktøy eller en rotete oversikt. Programmet skal åpne på en ryddig startsideside med tydelige hovedvalg.

Målet med startsiden er:

- gi rask tilgang til det vanligste arbeidet
- gjøre strukturen lett å forstå
- redusere rot og overlapp
- hjelpe nye brukere i gang
- gi raske snarveier for erfarne brukere
- gjøre det lett å forstå hvilke data som mangler og hvilke valg som må tas først

## Anbefalt oppstartsmeny

Når programmet åpnes, bør brukeren møte disse hovedvalgene:

1. Ladeutvikling
2. Prosjekter
3. Ballistikk
4. Lager og batcher
5. Våpenprofiler
6. Lab og testing
7. Innstillinger

## Hva hvert hovedvalg betyr

### 1. Ladeutvikling

Dette er hovedinngangen til nytt arbeid.

Her skal brukeren kunne:

- velge våpenprofil
- velge pipe eller løp, optikk og nullprofil
- velge komponenter fra batch eller fritt
- bygge opp en ladning
- justere variabler
- simulere og planlegge test
- logge og sammenligne resultater

### 2. Prosjekter

Dette er navet for historikk og videre arbeid.

Her skal brukeren kunne:

- åpne aktive prosjekter
- se eldre prosjekter
- fortsette tidligere arbeid
- sammenligne batcher og tester
- lese notater og rapporter
- bruke AI med prosjektkontekst

### 3. Ballistikk

Dette er egen modul for bane, vind, energi og planlegging.

Her skal brukeren kunne:

- bruke våpenprofil og ladning videre i ballistiske beregninger
- lage dopecard
- regne klikk og korreksjoner
- bruke vær og miljødata
- planlegge og analysere lovlige og trygge skytescenarioer

### 4. Lager og batcher

Dette er området for fysisk komponentkontroll.

Her skal brukeren kunne:

- registrere hylser, krutt, kuler og tennhetter
- knytte lotnummer og måledata til batcher
- føre beholdning og kostnad
- følge forbruk og historikk

### 5. Våpenprofiler

Dette er grunnlaget alt annet bygger på.

Her skal brukeren kunne:

- opprette våpenprofiler
- velge våpentype: rifle eller pistol
- registrere flere piper eller løp under samme våpen når det er relevant
- registrere løp, optikk og munningsutstyr
- lagre null og klikkdata
- følge presisjon og utvikling over tid
- koble ladninger og resultater til våpenet

### 6. Lab og testing

Dette er avansert modus for dypere analyse og mer profesjonell bruk.

Her skal brukeren kunne:

- kjøre større testserier
- bruke kvalitetskontroll
- sammenligne lotter og batcher
- generere rapporter
- bruke verktøy som passer utviklere, produsenter og testmiljøer

### 7. Innstillinger

Her skal brukeren kunne:

- velge brukermodus
- velge språk og enheter
- sette sikkerhetsnivå
- justere AI og personvern
- styre database, backup og utseende

## Innhold på startsiden

Selve startsiden bør i tillegg ha en tydelig toppflate med raske handlinger.

Anbefalte hurtigvalg:

- Fortsett siste prosjekt
- Start ny ladeutvikling
- Åpne prosjekter
- Gå til ballistikk
- Se lagerstatus
- Åpne våpenprofiler

Anbefalte informasjonsfelt på startsiden:

- siste aktive prosjekt
- nylig brukte våpenprofiler
- nylig brukte batcher
- siste kronografimport
- advarsler eller oppgaver
- lav lagerstatus
- forslag om å fortsette påbegynt arbeid

## Konkrett skisse for startsiden

Startsiden bør bygges som en ryddig forside med tre nivåer:

1. toppområde med hovedhandlinger
2. hovedkort for de viktigste modulene
3. informasjonsfelt og snarveier nederst

## Foreslått oppsett

### Øverst på siden

Her vises:

- programlogo eller navn
- aktiv brukerprofil hvis relevant
- valgt brukermodus: Enkel, Avansert eller Lab
- hurtigsøk
- varselsymbol
- knapp for innstillinger

### Stor hovedseksjon

Denne delen skal være det brukeren ser først, og den skal ha de viktigste valgene som store kort eller store knapper.

Anbefalte hovedkort:

- Start ny ladeutvikling
- Fortsett siste prosjekt
- Åpne prosjekter
- Gå til ballistikk
- Åpne våpenprofiler
- Se lager og batcher

Hvert kort bør ha:

- tydelig tittel
- kort forklaring
- ikon eller visuell markør
- eventuell status, for eksempel antall aktive prosjekter eller lav lagerstatus

### Anbefalt tekst på hovedkort

#### Start ny ladeutvikling

Starter en ny arbeidsflyt med valg av våpenprofil, komponenter og simulering.

#### Fortsett siste prosjekt

Åpner sist aktive prosjekt og lar brukeren fortsette der arbeidet stoppet.

#### Åpne prosjekter

Viser aktive og eldre prosjekter, batcher, notater, målinger og analyser.

#### Gå til ballistikk

Åpner bane, dopecard, vind og planleggingsverktøy med data fra våpenprofil og ladning.

#### Åpne våpenprofiler

Viser registrerte våpen, løp, optikk, nullprofiler og historikk.

#### Se lager og batcher

Viser komponentlager, batchdata, beholdning, lotnummer og kostnader.

## Seksjon for sist brukte og anbefalte handlinger

Under hovedkortene bør det være en seksjon som hjelper brukeren å komme raskt videre.

Denne seksjonen bør vise:

- sist brukte våpenprofil
- sist brukte ladning
- sist importerte kronografmåling
- sist åpnet prosjekt
- anbefalt neste handling

Eksempler på anbefalt neste handling:

- Fortsett test av .308 matchprosjekt
- Sammenlign siste måleserie mot simulering
- Nullstill optikk for ny ladning
- Fullfør registrering av ny batch

## Seksjon for status og varsler

Denne delen bør ligge nederst eller i høyre side og vise viktige ting uten å dominere forsiden.

Anbefalte felt:

- aktive prosjekter
- prosjekter som mangler måledata
- batcher med lav beholdning
- komponenter som snart er tomme
- siste lagrede kronografimport
- påminnelse om rengjøring eller vedlikehold på våpenprofil
- advarsler om modell og måledata som spriker mye

## Anbefalt førstegangsflyt fra startsiden

Når bruker klikker på `Start ny ladeutvikling`, bør følgende vises i denne rekkefølgen:

1. Velg våpenprofil
2. Velg løp og nullprofil
3. Velg komponentmodus: fra batch eller fritt
4. Velg formål: jakt, konkurranse, hobby eller lab
5. Åpne ladeutviklingsflaten

## Ladeutviklingsflaten etter oppstart

Når brukeren har gått gjennom startvalgene, bør hovedskjermen for ladeutvikling deles i tydelige områder:

- venstre side: komponentvalg og manuelle variabler
- midten: visualisering av patron, simulator og nøkkeldata
- høyre side: anbefalinger, harmonikk, risiko og AI-hjelp
- nederst: faner for måledata, historikk, optikk og sammenligning

## Hvilke faner ladeutviklingsflaten bør ha

Anbefalte faner:

- Oversikt
- Komponenter
- Simulering
- Harmonikk
- Optikk og null
- Måledata
- Sammenligning
- Historikk
- AI-hjelp

## Hva som bør vises i Oversikt

- valgt våpenprofil
- valgt løp
- valgt optikk
- valgt nullprofil
- valgt ladning
- sentrale nøkkeletall
- kort oppsummering av forventet oppførsel

## Hva som bør vises i Komponenter

- hylse
- kule
- krutt
- tennhette
- batchdata eller fri oppbygging
- kostnad og tilgjengelighet hvis batch brukes

## Hva som bør vises i Simulering

- trykktrend
- hastighet
- fyllingsgrad
- energi
- rekyl
- stabilitet
- temperaturfølsomhet
- bane og vinddrift

## Hva som bør vises i Harmonikk

- foreslått testområde for kruttmengde
- foreslått testområde for settedybde
- følsomhet for små endringer
- sannsynlige noder
- rolig eller nervøs ladning
- usikkerhetsnivå

## Hva som bør vises i Optikk og null

- nåværende null
- avstand
- faktisk avvik i treffpunkt
- beregnet klikk opp eller ned
- beregnet klikk høyre eller venstre
- lagring av optikkdata per ladning

## Hva som bør vises i Måledata

- importerte kronografdata
- ES og SD
- skivebilder
- gruppering
- POI
- temperatur og værdata
- kommentarlogg

## Hva som bør vises i Sammenligning

- predicted vs observed
- batch mot batch
- temperatur mot temperatur
- våpenprofil mot våpenprofil
- før og etter justering

## Hva som bør vises i AI-hjelp

AI-delen bør vise kontekstavhengig hjelp, for eksempel:

- forklaring på hvorfor en verdi endrer seg
- forslag til neste test
- oppsummering av avvik mellom modell og målt data
- varsler om risikable kombinasjoner
- forklaring av kuleform, hastighet, rekyl eller BC

## Viktig UI-prinsipp for startsiden

Startsiden skal ikke være full av små tekniske detaljer.

Den skal:

- gi retning
- vise tydelige valg
- hjelpe brukeren raskt videre
- gjøre avanserte ting tilgjengelige uten å være overveldende

Nye brukere skal forstå hvor de skal begynne.
Erfarne brukere skal kunne hoppe rett inn i siste prosjekt eller ny ladeutvikling.

## Viktig prinsipp for menystrukturen

AI-chat, bildeanalyse og kronografimport skal ikke være egne toppnivåmenyer.

De skal være støttefunksjoner inne i:

- ladeutvikling
- prosjekter
- ballistikk
- lab og testing

Dette er viktig for å unngå rot og gjøre systemet mer naturlig å bruke.

## Hovedmoduler

### 1. Våpenprofiler

Dette er grunnmuren for resten av systemet.

Våpenprofilen bør bygges som en hierarkisk struktur:

- våpen
- pipe eller løp
- konfigurasjon

Våpendelen bør inneholde:

- våpennavn
- produsent og modell
- våpentype: rifle eller pistol
- serienummer eller intern ID
- bruksområde
- magasinlengdebegrensning
- optikkmodell
- klikkverdi
- MRAD eller MOA
- montasjehøyde
- skinnevinkel hvis relevant
- chassis, grep eller skjefte hvis relevant
- avtrekksoppsett hvis relevant

Pipe- eller løpsdelen bør inneholde:

- kaliber
- løpslengde
- twist
- pipeprofil hvis kjent
- materiale hvis kjent
- antall skudd på løpet
- kammerinfo hvis relevant
- brukstype: trening, konkurranse, jakt, reserve eller annet
- status: aktiv, reserve, utslitt, under testing eller lignende
- nullprofiler
- historiske treffpunktendringer
- foretrukne ladninger
- kjente hastighetsområder
- temperaturhistorikk
- vedlikehold og rengjøringslogg
- solver-kalibrering mot faktiske målinger

Pipe- eller løpskonfigurasjonen bør i tillegg støtte:

- brems, comp, lyddemper eller ingen
- modellnavn på munningsutstyr
- vekt på munningsutstyr
- lengde på munningsutstyr
- om munningsutstyr var montert under test

Pipe- eller løpsspesifikke hylsedata bør kunne lagres:

- hylsemål etter standard
- trimlengde
- skuldermål
- base til datum-mål
- neckmål
- H2O-volum
- nullprofiler

Det er også enighet om at våpenprofilen må være mer enn et enkelt registerkort. Den skal være en datamotor som resten av systemet bruker i ladeutvikling, analyse, optikk og ballistikk.

Kalibrering bør i hovedsak knyttes til valgt pipe eller løp, ikke bare til våpenet generelt.

Brukeren må i tillegg få god veiledning når data registreres, slik at feil enhet, feil målemetode eller urimelige verdier fanges opp tidlig.

### 2. Komponent og batch

Modulen skal støtte to arbeidsmåter:

- batch-basert valg fra lager
- fri oppbygging uten lagerbinding

Data som bør kunne lagres:

- hylsebatch
- kulebatch
- kruttbatch
- tennhettebatch
- lotnummer
- målt hylsevolum
- hylselengde
- trimstatus
- antall omladinger
- neck-tykkelse
- gløding utført eller ikke
- faktisk kulelengde
- variasjon i kulevekt
- kostnad
- beholdning

Denne modulen skal støtte både brukere som vil ha full sporbarhet og brukere som bare vil teste en idé raskt uten å fylle ut unødvendig mange felt.

### 3. Ladeutvikling

Dette er hjertet i plattformen.

Brukeren skal kunne bygge en ladning med:

- valgt våpenprofil
- valgt pipe eller løp
- valgt komponentsett
- valgt formål
- frie manuelle justeringer

Følgende parametere bør kunne justeres:

- kruttmengde
- settedybde
- jump eller jam
- patronlengde
- neck tension
- hylsevolum
- hylselengde
- kulevekt
- kulelengde
- kuleprofil eller form
- tennhettevalg
- løpslengde
- munningsutstyr med vekt og lengde
- temperatur
- høyde over havet
- lufttrykk

Programmet skal vise hva som skjer når disse justeres.

Det er også enighet om at ladeutviklingsdelen må være bedre enn tradisjonelle verktøy på forklaring. Den skal ikke bare gi et tall, men også vise:

- hvorfor endringen skjer
- hvilke andre verdier som påvirkes
- hvor følsom ladningen er
- hvor usikker modellen er

Det bør også forklares visuelt hva som skjer i:

- indre ballistikk når ladedata eller komponenter endres
- ytre ballistikk når hastighet, BC, stabilitet eller vær endres
- harmonikk og forventet treffpunkt når pipekonfigurasjon eller munningsutstyr endres

Brukeren bør i tillegg enkelt kunne be om forklaring når noe er uklart, både i UI og via AI-støtte.

### 4. Fysikk- og simuleringsmotor

Programmet skal beregne og vise:

- trykktrend
- forventet hastighet
- fyllingsgrad
- rekylenergi
- rekylimpuls
- stabilitetsfaktor
- anslagsenergi
- forventet bane
- vinddrift
- temperaturfølsomhet
- BC-relatert oppførsel
- impact velocity
- estimert terminalvindu nar kuledataene tillater det
- tydelig skille mellom anslagsenergi og faktisk forventet prosjektiloppforsel

Det er viktig at beregnet output presenteres som modellert data, ikke som absolutte sannheter.

Beregningene bør over tid kunne kalibreres mot faktisk rifle, faktisk optikk og faktisk målehistorikk.

Det bør også bygges inn støtte for:

- pipe- eller løpsspesifikk konfigurasjon
- pipe- eller løpsspesifikke hylsemål og H2O-volum
- kronografdata med kjent målemetode og gjerne måleusikkerhet
- termisk tilstand: kald pipe, varm pipe, ammunisjonstemperatur, antall skudd i streng
- gyroskopisk stabilitet og stabilitetsmargin
- prosjektildata som konstruksjonstype, ekspansjonsvindu og minimum impact velocity der det finnes

Programmet bør samtidig ha tydelig enhetsstøtte:

- brukeren må kunne velge metrisk eller tommer der det er relevant
- programmet må tåle at brukere tenker i ulike målesystemer
- felter med høy feilrisiko bør vise enhet svært tydelig
- sannsynlige enhetsfeil bør varsles før lagring

### 5. Harmonikk og optimalisering

Denne modulen skal hjelpe brukeren med å finne gode testområder, ikke gi en falsk fasit.

Input bør blant annet være:

- løpslengde
- twist
- pipeprofil
- våpenvekt
- pipe eller løpskonfigurasjon
- brems, comp eller lyddemper med vekt og lengde
- kulevekt
- kulelengde
- trykktrend
- hastighetsområde
- settedybde
- jump
- neck tension
- faktiske testresultater

Output bør være:

- anbefalt testområde
- sannsynlige noder
- sannsynlig stabile områder
- følsomhet for små endringer
- forventet rolig eller nervøs ladning
- usikkerhetsnivå

Harmonikkmodulen skal være et konkurransefortrinn. Målet er ikke å presentere magiske svar, men å hjelpe brukeren med å finne gode testområder for kruttmengde, settedybde og neck tension.

### 6. Skyte- og målelogg

Denne delen skal samle reelle observasjoner:

- kronografdata
- ES og SD
- rå hastigheter per skudd
- treffbilder
- gruppering
- mean radius når det er mulig
- POI
- miljødata
- temperatur på pipe eller ammo hvis kjent
- skytterkommentarer
- trykktegn
- hylseoppførsel
- optikkjusteringer

Dette skal knyttes til:

- våpenprofil
- pipe eller løp
- prosjekt
- batch
- konkret ladning

Denne delen er avgjørende fordi plattformen skal bli bedre ved å koble simulert teori til faktisk virkelighet.

Brukeren bør også hjelpes gjennom loggingen med:

- validering av urimelige verdier
- tydelige eksempler i felter med høy feilrisiko
- oppsummering av kritiske data før lagring
- raske muligheter for å spørre om hjelp eller forklaring

### 7. Optikk og null

Optikkdelen skal være integrert i ladeutvikling og testing.

Programmet skal kunne:

- lagre null på ulike avstander
- vite klikkverdi
- bruke MRAD eller MOA
- regne ut klikk til null
- vise avvik i treffpunkt
- lagre justeringer per ladning
- bruke data i dopecard og ballistikk

Optikkdelen skal ikke behandles som et tillegg. Den er en aktiv del av ladeutviklingen og testarbeidet.

### 8. Ballistikk og planlegging

Denne modulen skal brukes til:

- kulebane
- vinddrift
- energi på ulike hold
- dopecard
- planlegging mot kart og terreng
- sammenheng mellom våpenprofil, ladning og faktisk bruk

Denne delen må ha tydelige sikkerhetsgrenser for sivil bruk.

Det er enighet om at denne modulen må ha innebygde begrensninger og tydelig ansvarliggjøring slik at plattformen ikke utformes for kriminelle eller uforsvarlige formål.

### 9. Analyse og rapport

Programmet skal kunne:

- sammenligne ladninger
- sammenligne batcher
- sammenligne simulert mot målt
- vise utvikling over tid
- generere rapporter
- eksportere data
- lage PDF eller labrapporter

### 10. AI-assistent

AI skal ikke være en løs chatbot, men en støttefunksjon inne i arbeidsflyten.

AI bør kunne:

- forklare hvorfor ting skjer
- foreslå testområder
- advare ved risikable kombinasjoner
- oppsummere testresultater
- sammenligne prosjekter
- lære av historikk per våpenprofil

AI skal primært brukes som:

- forklaringsmotor
- rådgiver
- oppsummeringsmotor
- hjelp til sammenligning og læring

Ikke som en løs prateflate uten kontekst.

## Viktige konkurransefortrinn

For å bli bedre enn GRT og QuickLOAD bør plattformen være bedre på:

- forståelse og forklaring
- kobling mellom teori og praksis
- predicted vs observed
- visualisering
- harmonikkanalyse
- læring per våpenprofil
- optikk og null integrert i arbeidsflyten
- sporbarhet og rapportering

Det viktigste er ikke bare mer matematikk. Det viktigste er å være bedre på helheten:

- forståelse
- simulering
- logging
- sammenligning
- visualisering
- læring over tid

## Viktig designregel

Programmet må alltid skille tydelig mellom:

- simulert data
- målt data
- anbefalt testområde
- høy og lav sikkerhet i modellen

Tillit bygges ved å være tydelig på hva systemet vet, hva det antar, og hva brukeren faktisk har målt.

## Anbefalt hovedmeny

1. Ladeutvikling
2. Prosjekter
3. Ballistikk
4. Lager og batcher
5. Våpenprofiler
6. Lab og testing
7. Innstillinger

## Foreslått struktur for ladeutvikling

### Start

- velg våpenprofil
- velg pipe eller løp hvis våpenet har flere
- velg nullprofil
- velg komponentmodus
- velg formål

Denne startsekvensen er viktig og bør være standardflyten hver gang brukeren starter ny ladeutvikling.

### Bygg ladning

- velg kule
- velg krutt
- velg hylse
- velg tennhette
- sett startparametere

### Juster og simuler

- dra i variabler
- se grafisk endring live
- få advarsler og anbefalinger

### Testplan

- foreslå ladestige eller nodeområde
- foreslå settedybdeintervall
- foreslå måleserie

Systemet skal støtte både:

- enkel testplan for vanlige brukere
- mer avansert testdesign for konkurranse og labbruk

### Resultater

- importer kronografdata
- legg inn skivebilder
- logg gruppestørrelse og POI
- logg mean radius når det er mulig
- registrer faktiske klikk

### Sammenligning

- predicted vs observed
- endringer per batch
- endringer per temperatur
- endringer per våpenprofil
- endringer per pipe eller løp
- endringer per konfigurasjon med eller uten munningsutstyr

Dette er en av de viktigste funksjonene i hele plattformen og bør prioriteres høyt.

## Visualiseringer som bør prioriteres

### 1. Patronvisning

- kule
- hylse
- kruttfylling
- settedybde
- volumindikasjon

### 2. Grafer

- trykk
- hastighet
- temperaturpåvirkning
- fyllingsgrad
- stabilitet

Grafene bør være selvforklarende med:

- tydelige etiketter
- aktiv enhet
- forklarende tekst eller hint
- markering av usikkerhet der det er relevant

### 3. Nodekart

- kruttmengde vs resultat
- settedybde vs resultat
- kombinert følsomhetskart

### 4. Treffpunkt og optikk

- gruppevisning
- forventet POI
- faktisk POI
- klikkforslag

Det bør også være et mål at visualiseringene hjelper brukere med lite erfaring til å forstå hva som skjer, ikke bare vise fagdata for erfarne brukere.

## Brukermoduser

Systemet bør ha minst tre nivåer:

- Enkel
- Avansert
- Lab eller utvikler

Dette gjør det mulig å treffe både hobbybrukere og profesjonelle uten at alt blir rotete.

Brukermodusene bør styre:

- hvor mye som vises i grensesnittet
- hvor mye forklaring som gis
- hvor mange avanserte parametere som låses opp
- hvordan råd og varsler presenteres

I enkel modus bør programmet prioritere veiledning, trygg registrering, tydelige enheter og mer pedagogiske forklaringer.

I avansert og labmodus bør programmet kunne vise mer rådata, flere analysevalg og tettere fysikkmodellering.

Uansett modus bør brukeren oppleve at programmet inviterer til spørsmål når noe er uklart, i stedet for å forvente at brukeren allerede forstår alt.

## Prioritering

### V1

Målet for V1 er å bygge en troverdig og ryddig kjerne.

Leveranser:

- våpenprofil som startpunkt
- støtte for rifle og pistol i våpenprofil
- pipe eller løp som underprofil med eget kaliber
- ladeutvikling med manuelle justeringer
- komponentvalg fra batch eller fritt
- pipe- eller løpsspesifikke hylsemål og H2O-volum
- simulert output
- kronografimport
- målt vs simulert
- optikk og klikk til null
- enkel harmonikkvisning
- prosjektlagring

### V2

Målet for V2 er å løfte analyse og læring.

Leveranser:

- avansert harmonikkmotor
- nodekart
- AI med prosjektkontekst
- bildeanalyse
- kostnad og lagerkobling
- temperaturmodell
- bedre kuleforståelse
- bedre visuell forklaring av indre og ytre ballistikk

### V3

Målet for V3 er profesjonell og lab-orientert bruk.

Leveranser:

- labmodus
- rapportgenerator
- eksport og sporbarhet
- kvalitetskontroll på batchnivå
- modellkalibrering mot historiske data
- fabrikk- og utviklerflyt

## Neste konkrete steg

1. Lage en endelig produktstruktur med skjermbilder og sider
2. Ferdigstille datamodell for våpenprofil, pipe eller løp og konfigurasjon utover dagens grunnmur
3. Definere datamodell for ladning, prosjekt og batch
4. Ferdigstille flyt for oppstart av ladeutvikling med valg av pipe eller løp
5. Bestemme hva som er V1 og hva som bevisst utsettes
6. Lage enkel prototype for hovedmeny og startflyt

## Forslag til neste dokumenter

Etter dette dokumentet bør følgende dokumenter lages:

1. Våpenprofil-spec
2. Pipe eller løp-spec med konfigurasjon og munningsutstyr
3. Datamodell for prosjekt, batch og ladning
4. UI-spesifikasjon for oppstartsmeny
5. UI-spesifikasjon for ladeutvikling
6. V1-funksjonsliste

## Konkret implementeringsrekkefolge i kodebasen

Denne rekkefolgen er laget for a gi mest mulig verdi uten a skape unodig rot eller stor risiko.

### Trinn 1: Samle motoren uten a rive UI

Mal:

- fa ett samlet service-lag som kan mate flere skjermer med samme vurdering

Filer som bor rores forst:

- `src/ballistics/services.py`
- `src/utils/rifle_harmonics.py`
- `src/utils/internal_ballistics.py`
- `src/utils/scientific_quality.py`
- `src/utils/advanced_ballistics.py`

Arbeid:

- bygg ett samlet resultatobjekt for ladeanalyse
- la dette objektet inkludere trykk, harmonikk, stabilitet, ytre ballistikk, terminal vurdering og datakvalitet
- bruk eksisterende funksjoner der de finnes, i stedet for a bygge duplikater i UI-laget
- la service-laget ta inn vapen, pipe, brass-data, komponenter, lotter, ladning og miljo som input

Dette er lav risiko og hoy verdi fordi det samler logikken uten a tvinge stor UI-ombygging med en gang.

### Trinn 2: Gjore pipeprofilen operativ

Mal:

- pipeprofilen skal ga fra statisk profil til laerende enhet

Filer som bor tas etter service-laget:

- `src/modules/weapon_profile.py`
- `src/modules/rifle_profile_editor.py`
- `src/modules/weapon_profile_dialog.py`
- `src/modules/rifle_database_manager.py`
- `src/database/database.py`

Arbeid:

- rydde og tydeliggjore pipeprofil-data
- innfore tydelig skille mellom brass-baseline og brass-observasjoner
- lagre hvilken ladning som formet baseline
- definere felt eller struktur for pipehistorikk:
  - chrono
  - samlingsbilder
  - grupper
  - trykktegn
  - lot-kontekst

Dette er middels risiko fordi det berorer datamodell, men det gir stor verdi videre.

### Trinn 3: Koble builderen til den nye modellen

Mal:

- den eksisterende builderen skal bli hovedarbeidsflate, ikke et sideverktoy

Hovedfiler:

- `src/modules/modern_load_builder.py`
- `src/modules/load_development_workflow.py`
- `src/modules/ballistics_simulator.py`

Arbeid:

- gjor vapenvalg og aktiv pipe til forste og obligatoriske steg
- legg inn bruksmal tydelig i builderen
- hent anbefalinger fra service-laget i stedet for spredt lokal logikk
- vis harmonikk, ytre ballistikk, terminal vurdering og datakvalitet i samme flyt
- bruk lotter og brass-data direkte i builderens simulering

Dette er hoy verdi og middels risiko, fordi builderen allerede er stor og sentral.

### Trinn 4: Pipehistorikk og testbevis

Mal:

- knytte faktisk evidens til pipe og ladning

Hovedfiler:

- `src/database/database.py`
- `src/database/batch_manager.py`
- `src/modules/chronograph_importer.py`
- `src/modules/load_development_workflow.py`
- `src/modules/session_logger.py`

Arbeid:

- sikre at chrono-data kan kobles til pipe og ladning tydelig
- sikre at samlingsbilder og grupper kan lagres som pipehistorikk
- bruke `batch_project_sessions` og `chronograph_sessions` som grunnmur der det passer
- la builderen og workflowen hente denne historikken inn i analysen

Dette er hoy verdi fordi det gjor systemet laerende med ekte data.

### Trinn 5: Ryggmarg i UI og oppstart

Mal:

- brukeren skal oppleve ett tydelig, moderne hovedspor

Hovedfiler:

- `src/ui/main_window.py`
- `src/modules/dashboard.py`
- `src/modules/workflow_hub.py`

Arbeid:

- gjor ladeutvikling til en tydelig hovedinngang
- la brukeren starte med vapenprofil
- vis status for valgt vapen, pipe, brass-baseline og manglende data
- gi korte, tydelige valg for bruksmal

Dette er hoy verdi for brukeropplevelsen, men bor tas etter at motor og datamodell er strammere.

## Konkret arbeidsrekkefolge: hva som bor bygges forst

1. Utvide `src/ballistics/services.py`
2. Knytte eksisterende harmonikk- og internballistikkfunksjoner til service-laget
3. Rydde datamodellen for pipe/brass-baseline i `src/modules/weapon_profile.py`
4. Oppdatere lagring/henting i `src/modules/rifle_profile_editor.py` og `src/database/database.py`
5. Koble `src/modules/modern_load_builder.py` til den nye motoren
6. Deretter hente inn pipehistorikk, chrono og samlingsbilder
7. Til slutt rydde hovedflyt og startsider i UI

## Hva som ikke bor gjores for tidlig

For a unnga rot bor disse tingene vente til grunnmuren er strammere:

- stor 3D-satsing
- mange nye sideverktoy
- ny stor AI-chat overalt
- mye ny visual flair uten samlet datamodell
- duplisering av beregning i flere moduler

Forst nar service-lag, pipeprofil og builder jobber mot samme sannhetskilde, bor videre spesialisering tas.

## Rask gevinst vs hoy verdi

### Rask gevinst

- bedre visning av valgt pipe i builder
- tydelig bruksmalvalg
- tydeligere harmonikkstatus og confidence i builderen
- bedre kobling mellom chrono og aktiv ladning

### Hoy verdi

- samlet anbefalingsmotor
- pipebasert testhistorikk
- brass-baseline med sporbar ladningskontekst
- laerende modell per pipe og lot

## Kort konklusjon

Retningen er svært sterk. Den største muligheten ligger ikke bare i mer beregning, men i å kombinere:

- bedre brukerflyt
- sterkere forklaring
- bedre visuell forståelse
- tryggere dataregistrering
- tydelig håndtering av enheter og målesystemer
- tettere kobling mellom simulering og virkelighet
- historikk og læring per våpenprofil

Hvis dette bygges riktig, blir det ikke bare et ladeprogram, men en reell utviklingsplattform.
