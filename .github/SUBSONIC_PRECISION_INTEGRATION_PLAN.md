# Integrert plan: Subsonisk modus, presisjon og stabilitet i ladeutvikling

## Mål

Bygge subsonisk støtte, presisjonsrådgivning og stabilitetsanalyse inn i eksisterende lademodul, slik at brukeren ikke må hoppe mellom egne verktøy eller moduser som lever hver for seg.

Målet er én samlet builder der brukeren:

- velger våpen og pipe eller løp
- velger komponenter og lotter
- kan huke av for `Subsonisk modus`
- får riktige råd, varsler og visualiseringer for valgt bruksområde
- kan leke med charge og settedybde og se hva som skjer
- kan bygge videre på historikk, lot-data og målte resultater

## Grunntanke

- Subsonisk støtte skal ikke være et eget mini-program.
- Det skal være et lag inni dagens ladeutvikling.
- Presisjon, sikkerhet, stabilitet og læring skal bruke samme datagrunnlag.
- Nye funksjoner for subsonisk arbeid skal samtidig styrke vanlig presisjonslading.

## Hvorfor dette er viktig

Det samme datalaget løfter flere områder samtidig:

- bedre vurdering av trykk og publisert charge-vindu
- tydeligere forståelse av komprimert ladning og fill rate
- bedre seating-rådgivning og sweet spot-læring
- bedre stabilitetsvurdering og tumble-risiko
- bedre retest-råd ved komponent- og lotbytte
- bedre sammenligning mellom simulert og målt resultat
- bedre læring per våpen, pipe, kule, krutt og lot

## Det brukeren skal oppleve

Når brukeren åpner ladeutvikling:

1. velges våpenprofil
2. pipe eller løp og kaliber hentes inn
3. komponenter og lotter velges som i dag
4. bruker kan huke av for `Subsonisk modus`
5. builderen justerer rådgivningen og visualiseringene automatisk

Dette skal påvirke samme skjerm, ikke sende brukeren til et annet verktøy.

## Hva subsonisk modus skal gjøre

Når `Subsonisk modus` er aktiv:

- velocity-mål skifter fra ytelse til trygg margin under lydmuren
- trykk og sikkerhet beholdes, men suppleres med subsoniske risiki
- fyllgrad og lav charge blir mer sentralt
- stabilitetsvurdering vektes høyere
- demperrisiko og baffle-risk synliggjøres
- cycling- og funksjonslogg blir relevant for halvauto
- retest-rådene blir mer konservative
- charge- og seating-sandboxene bruker subsonisk språk og mål

## Hovedproblemer vi skal løse

### 1. Krutt og charge

Programmet skal hjelpe brukeren å se:

- publisert min og maks når data finnes
- hvor dagens charge ligger i forhold til publisert vindu
- om ladningen er komprimert
- om fyllgraden er lav og potensielt ustabil
- hvordan små charge-endringer påvirker trykk, fart, fyllgrad og barrel time

### 2. Settedybde

Programmet skal hjelpe brukeren å se:

- valgt COAL og CBTO
- målt jam og beregnet jump
- historisk sweet spot
- hvordan små seating-endringer påvirker trykk, fart, jump og barrel time
- om endringen flytter ladningen inn eller ut av historisk arbeidsvindu

### 3. Presisjon

Programmet skal hjelpe brukeren å forstå:

- hvordan ES og SD påvirker forventet vertikalspredning
- hvilke seating-vinduer som historisk har fungert best
- om ladningen ser robust ut eller er svært følsom
- om avvik sannsynligvis kommer fra seating, krutt, lot eller stabilitet

### 4. Stabilitet og tumbling

Programmet skal hjelpe brukeren å se:

- om kule, twist og hastighet virker som en trygg kombinasjon
- om stabiliteten er marginal
- om subsonisk fart gjør kulen sårbar for tumble eller dårlig presisjon
- om demperbruk øker konsekvensen av dårlig stabilisering

### 5. Subsonisk spesifikt

Programmet skal hjelpe brukeren å se:

- om ladningen sannsynligvis holder seg under lydmuren
- hvor stor margin som finnes mot sonic crack
- om lav fyllgrad eller svak akselerasjon gir squib-risiko
- om kule og twist ser ut til å være nok til stabil subsonisk flyvning
- om halvauto sannsynligvis vil sykle eller ikke

## Faseplan

## Fase 1: Modus og arbeidsflyt i builderen

- [ ] Legge inn avhuking for `Subsonisk modus` i eksisterende builder
- [ ] Lagre modusvalg i batch og prosjektkontekst
- [ ] Sørge for at modus påvirker labels, råd og sikkerhetsvurderinger
- [ ] Vise tydelig hvilket modus som er aktivt

Leveranse:
- én builder
- ett modusvalg
- samme dataflyt videre

## Fase 2: Krutt og charge-rådgivning

- [ ] Stramme visning av publisert min og maks charge
- [ ] Tydeliggjøre når data er publisert, inferert eller modellert
- [ ] Vise `komprimert`, `høy fill`, `lav fill`, `under publ. min`, `over publ. maks`
- [ ] Utvide powder sandbox med tydeligere farge-/statuslogikk
- [ ] Lage egen subsonisk vurdering av lav fyllgrad og mulig position sensitivity

Leveranse:
- bedre kruttvindu
- bedre sandbox
- tydeligere forståelse av charge-risiko

## Fase 3: Stabilitetsrådgiver

- [ ] Lage egen `Stability Advisor` i builderen
- [ ] Bruke kulevekt, kulelengde, diameter, twist, fart og atmosfæriske forhold
- [ ] Vise nivåer som `trygg`, `marginal`, `risiko`
- [ ] Løfte frem tumble-risiko ved subsonisk fart og lang kule
- [ ] Vise ekstra varsel ved demperbruk og marginal stabilitet

Leveranse:
- stabilitet synlig i samme arbeidsflate
- tumbling ikke bare fanget opp i ettertid

## Fase 4: Subsonisk rådgiver

- [ ] Lage egen `Subsonic Advisor` inni builderen
- [ ] Vise target velocity-band med sikkerhetsmargin
- [ ] Vise sonic-margin i forhold til temperatur
- [ ] Vise squib-risiko og cycling-risiko
- [ ] La bruker registrere om ladningen syklet, var stille, cracka eller keyhola
- [ ] Bruke historikken til å forbedre anbefalinger per våpen og pipe

Leveranse:
- subsonisk arbeidsstotte i samme modul
- læring fra ekte subsonisk testing

## Fase 5: Seating og presisjonsløft

- [ ] Koble seating-rådgiver enda tettere til stabilitet
- [ ] Vise tydeligere presisjonskostnad ved stor ES og marginal stabilitet
- [ ] Lage enkel forventet vertikalspredning ved valgt avstand
- [ ] Lage støtte for å markere `robust node` versus `smal node`
- [ ] Bevare og rangere beste seating-vinduer med mer evidens

Leveranse:
- bedre forståelse av hvorfor en ladning skyter bra eller dårlig
- bedre sammenheng mellom historikk, simulering og målte resultater

## Fase 6: Test- og historikkmodell

- [ ] Utvide batch og session med subsoniske observasjoner:
  `cycling`, `sonic crack`, `keyhole`, `baffle concern`, `cold bore note`
- [ ] Gi retest advisor egne subsoniske regler
- [ ] La historikken skille mellom vanlig og subsonisk bruk
- [ ] Vekte beste kjente data etter temperatur, lot, pipe og modus

Leveranse:
- historikk som faktisk lærer av subsonisk arbeid

## Fase 7: Kammer, patronstandard og videre simulering

- [ ] Bruke patronstandard-data mer aktivt i seating og stability-advisors
- [ ] Legge til mer SAAMI- og CIP-basert hylse- og målestøtte
- [ ] Forberede sammenligning mellom patronstandard, hylse og kammer
- [ ] Bruke dette til å gjøre friflukt, throat og neck-vurderinger skarpere

Leveranse:
- mer presis geometri-forståelse
- bedre grunnlag for simulering og kammeranalyse

## Fase 8: Visuell simulering og 3D-støtte

- [ ] Lage en teknisk visualiseringsmodell som skiller mellom:
  `publisert geometri`, `målt geometri`, `modellert plassering`
- [ ] Starte med 2.5D eller teknisk snittvisning for patron, kule og kammer
- [ ] Vise seating depth, jump, freebore, throat og neck clearance visuelt
- [ ] Koble charge- og seating-sandbox til visualiseringen slik at brukeren ser hva som flyttes
- [ ] Lage enkel stabilitetsvisning med `trygg`, `marginal`, `risiko`
- [ ] Vise demper- og baffle-risk når stabiliteten er marginal
- [ ] Vurdere ekte interaktiv 3D først etter at datagrunnlaget er godt nok

Leveranse:
- rå visuell simulering uten å miste faglig presisjon
- bedre romforståelse rundt patron, kammer og kuleoppførsel
- tydeligere sammenheng mellom tall og faktisk geometri

## Hvilke dataløft som gir mest verdi

Dette er de viktigste dataene å løfte videre:

### Krutt

- publiserte min og maks charge-data
- fyllgrad og kompresjon
- temperaturfølsomhet
- lot-forskjeller
- subsonisk egnethet

### Kule

- faktisk lengde per lot
- base-to-ogive
- vektspredning
- stabilitetsrelevante mål
- subsonisk egnethet og eventuell ekspansjonsprofil

### Våpen og pipe

- twist
- friflukt eller jam-data
- throat-erosjon
- demperstatus
- gassystem, buffer og lignende for halvauto der relevant
- chamber neck og relevante kammermål for visuell sammenligning

### Visualisering

- nok geometri til å tegne patron, kule og kammer i skala
- tydelig skille mellom standardmal og målte verdier
- regler for hva som er pedagogisk visualisering versus fysisk modell
- kobling mellom visualisering og aktive sliders for charge og seating

### Testresultat

- faktisk fart
- ES og SD
- gruppe
- temperatur
- avstand
- cycling ja eller nei
- sonic crack ja eller nei
- keyholing ja eller nei

## Hva dette også forbedrer i resten av programmet

Dette er ikke et sidespor. Det løfter resten av plattformen:

- bedre sikkerhetslogikk i vanlig lading
- bedre charge- og seating-sandbox generelt
- bedre harmonikkvurdering
- bedre retest-råd
- bedre batchhistorikk
- bedre rifle- og pipeprofiler
- bedre AI-rådgivning fordi mer av konteksten blir strukturert
- bedre grunnlag for senere simuleringer og sammenligninger
- bedre brukerforståelse fordi geometri og risiko blir synlig, ikke bare forklart

## Prioritert rekkefølge

Anbefalt gjennomføring nå:

1. Subsonisk modus i eksisterende builder
2. Stability Advisor
3. Subsonic Advisor
4. Utvidet test- og observasjonslogg for subsonisk arbeid
5. Presisjonsløft med vertikalspredning og robust node-vurdering
6. Videre SAAMI/CIP og kammergeometri-løft
7. Teknisk visualisering og 2.5D eller 3D-støtte der det gir faglig verdi

## Første konkrete leveranse

MVP for første runde:

- avhuking for `Subsonisk modus`
- stability advisor i builderen
- subsonisk rådgivningspanel med sonic-margin, squib-risk og cycling-risk
- subsoniske observasjoner i batch/session
- tydeligere integrasjon mot charge- og seating-sandbox

## Prinsipper for 3D og visuell simulering

- 3D skal brukes der romforståelse faktisk hjelper brukeren
- 2D og vanlig UI skal fortsatt være hovedflate for tall, input og sikkerhetsvarsler
- teknisk snitt eller 2.5D er første steg, ikke full 3D overalt
- visualisering skal alltid være koblet til datakilde og evidensnivå
- programmet skal aldri presentere pedagogisk visualisering som om den er eksakt målt geometri
- ekte interaktiv 3D skal bygges først når patron-, hylse- og kammerdata er presise nok

## Arbeidsprinsipper

- samme builder skal brukes videre
- samme lot- og komponentmodell skal gjenbrukes
- samme historikk skal brukes til læring
- alt skal tydelig merkes som `publisert`, `modellert`, `målt` eller `inferert`
- bruker skal kunne utforske uten at programmet skjuler risiko
- sikkerhet og forklarbarhet skal alltid komme foran “magiske anbefalinger”

## Åpne valg vi bør ta underveis

- Skal `Subsonisk modus` være en enkel checkbox eller del av en større `load intent`-modell?
- Hvor hardt skal vi advare ved mulig squib eller marginal stabilitet?
- Skal demper og halvauto-funksjon være frivillige avanserte felter eller del av standardflyten?
- Hvor detaljert skal cycling-loggen være i første runde?
- Skal vi prøve å modellere sonic crack-margin direkte mot temperatur, eller først bare gi enklere marginregler?
