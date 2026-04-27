# IP og provenance-oversikt

## Formål

Dette dokumentet beskriver hvordan vi tenker om eierskap, datakilder, transformasjoner og midlertidige ingest-spor i Hjemmelading.

Målet er å gjøre det tydelig:

- hva som er vårt eget arbeid
- hva som er våre egne modeller og transformasjoner
- hva som er masterdata i produktet
- hva som er brukerdata
- hva som er midlertidige ingest-broer

## Hovedprinsipp

Data brukt i produktet skal ende opp som:

- våre egne masterdata
- våre egne transformerte data
- brukerens egne målinger og lotdata
- våre egne analyser, oppsummeringer og modeller

Opprinnelige ingest-kilder skal ikke være sluttproduktets identitet.

## Datatyper

### 1. Masterdata

Dette er data som produktet bruker som eget bibliotekgrunnlag.

Eksempler:

- kulebibliotek
- kruttbibliotek
- tennhettebibliotek
- hylsebibliotek
- eksporterte og berikede kataloger under `.github/data/exports`

Status:

- disse behandles som produktets egne operative masterdata
- de er i flere tilfeller beriket og normalisert videre hos oss

### 2. Brukerdata

Dette er data brukeren selv eier og legger inn.

Eksempler:

- våpenprofiler
- pipeprofiler
- brass-baselines
- lotter
- måleserier
- chrono
- grupper
- trykktegn
- notater
- bilder

Hovedregel:

- brukerdata skal alltid ha høy prioritet når de er mer spesifikke enn masterdata

### 3. Transformerte data

Dette er data vi selv har bearbeidet, beriket, normalisert eller tolket.

Eksempler:

- enriched/master CSV-er
- inferred bullet geometry
- inferred primer technical fields
- recommended twist
- shape/base/tip/construction-felt
- audit- og quality-rapporter

Dette er viktig for IP fordi:

- verdien ligger ikke bare i rådata, men i hvordan de er gjort operative i produktet

### 4. Egen logikk og teknologi

Dette er kjernen i det vi bygger som eget produkt.

Eksempler:

- analysemotoren i `src/ballistics/services.py`
- evidens-, helse- og tillitsmodeller
- lot-læring
- pipehistorikk
- harmonikkbruk i arbeidsflyten
- ladningskort og anbefalingslogikk
- brukerflyt, visualisering og forklarende modeller

Dette er det viktigste IP-sporet i produktet.

### 5. Midlertidig ingest-bro

Dette er kode og verktøy som bare eksisterer for å få data inn og sikre at de blir våre.

Eksempler:

- eldre importører
- kompatibilitetsmoduler
- temp extractors
- tidligere kildebroer og hjelpeskript

Hovedregel:

- disse er overgangsverktøy
- de skal ikke være del av sluttproduktets identitet
- de skal kunne fjernes når data og logikk er trygt inne i vårt eget domene

## Provenance-prinsipp

Vi skal kunne svare på disse spørsmålene for sentrale data:

1. Er dette rådata, brukerdata, transformert data eller egen modell?
2. Hvor lagres dette som sannhetskilde?
3. Er dette del av sluttproduktet eller bare en overgangsbro?
4. Kan denne delen fjernes uten å skade sluttproduktets egen identitet?

## Hva vi aktivt vil redusere

Videre arbeid skal redusere:

- gammel kildeidentitet i kode og UI
- unødvendige interne spor av overgangsbroen
- uklarhet om hva som er masterdata vs brukerdata
- dupliserte oppsummeringslag

## Hva vi aktivt vil styrke

Videre arbeid skal styrke:

- nøytrale domeneord
- egne service-lag
- egne analyser og oppsummeringer
- dokumentert transformasjon fra råstoff til produktdata
- testbar og ryddig arkitektur

## Praktisk sjekkliste for nye endringer

For hver ny modul, funksjon eller datastrøm skal vi spørre:

- bygger dette egen IP eller bare mer overgangslogikk?
- flytter dette oss nærmere et produkt som står på egne bein?
- er domenespråket vårt eget?
- kan en framtidig kjøper forstå hva som er vårt arbeid?
- gjør dette ingest-broen mindre viktig over tid?

Hvis svaret er nei, bør endringen omarbeides før vi går videre.

## Målbilde

Når produktet er modent skal bildet være:

- bruker og kjøper møter Hjemmelading som et eget produkt
- produktet står på egne data-, modell- og tjenestelag
- ingest-broen er ikke nødvendig i vanlig drift
- provenance og dataeierskap er tydelig nok til å redusere kommersiell risiko
