# Komponentdata: To-Do og Videre Plan

## Mål
Bygge en egen, frikoblet komponentdatabase for Hjemmelading som:
- bruker standarddata for kuler, krutt, kalibre, hylser og tennhetter
- lar brukeren registrere lagerbeholdning per lot
- lagrer kontrollmålinger per lot
- beregner snitt, spredning og avvik for hver lot
- gjør at resten av programmet kan bruke faktiske lot-data når de finnes

## Prinsipp
- Importerte Gordon-filer er kun startdata.
- Hjemmelading sin egen database er sannhetskilden videre.
- Rådata beholdes for sporbarhet.
- Lastedata skal kunne peke til konkrete lotter, ikke bare generiske komponenter.

## Fase 1: Datamodell
- [ ] Definere kjerneentiteter:
  `components`, `component_lots`, `component_measurements`, `component_lot_stats`
- [ ] Avklare hvilke komponenttyper som støttes først:
  `bullet`, `powder`, `brass`, `primer`, `caliber`
- [ ] Definere felter for standarddata per komponenttype
- [ ] Definere felter for lot-informasjon:
  lotnr, antall, kjøpsdato, leverandør, pris, notater, aktiv/inaktiv
- [ ] Definere felter for målinger:
  vekt, lengde, diameter, tykkelse, hylsevolum, primerdimensjoner, fukt/temp ved behov
- [ ] Definere hvilke statistikker som skal beregnes:
  snitt, min, max, std.avvik, antall målinger

## Fase 2: Database og migrasjoner
- [ ] Lage SQLite-skjema for komponentdatabase
- [ ] Lage migrasjon for nye tabeller
- [ ] Lage indekser for raske oppslag på komponenttype, produsent, navn og lotnr
- [ ] Lage relasjoner mellom standardkomponent, lot og målinger
- [ ] Lage lag for versjonering av skjema

## Fase 3: Importpipeline
- [ ] Lage import fra dagens frikoblede kunnskapsbase
- [ ] Mappe eksisterende kuledata til `components`
- [ ] Mappe eksisterende kruttdat a til `components`
- [ ] Mappe kaliberdata til referansetabell
- [ ] Merke alle importerte poster med `source=seed_import`
- [ ] Lage deduplisering og merge-regler
- [ ] Beholde rå JSON for sporbarhet

## Fase 4: Domenelogikk
- [ ] Lage tjenestelag for oppretting og oppdatering av komponenter
- [ ] Lage tjenestelag for lot-håndtering
- [ ] Lage tjenestelag for registrering av målinger
- [ ] Lage beregning av lot-statistikk
- [ ] Lage fallback-regel:
  bruk lot-statistikk hvis tilgjengelig, ellers standarddata
- [ ] Lage validering for ugyldige mål og enheter

## Fase 5: UI i komponentdelen
- [ ] Lage visning for standardkomponenter
- [ ] Lage visning for lager og lotter
- [ ] Lage skjema for å opprette ny lot
- [ ] Lage skjema for å registrere kontrollmålinger
- [ ] Lage oversikt som viser nominelle mål vs målte snittverdier
- [ ] Lage varsling ved store avvik fra standardverdier
- [ ] Lage enkel eksport/import av egne komponentdata

## Fase 6: Integrasjon i ladeprogrammet
- [ ] Oppdatere ladedata slik at de kan velge konkret lot
- [ ] Bruke faktisk lot-vekt/lengde når beregninger kjøres
- [ ] Vise hvilken lot som ble brukt i hver ladning
- [ ] Låse eller logge endringer i data som påvirker historiske ladninger
- [ ] Vise om en ladning bruker standardverdi eller målte lot-data

## Fase 7: Kvalitet og test
- [ ] Lage tester for datamodell og migrasjoner
- [ ] Lage tester for import og deduplisering
- [ ] Lage tester for statistikkberegning
- [ ] Lage tester for fallback mellom standarddata og lot-data
- [ ] Lage UI-smoketester for komponent- og lotflyt
- [ ] Lage noen golden-testdata for typiske lot-målinger

## Anbefalt rekkefølge
1. Lage databaseskjema og migrasjon
2. Importere seed-data fra kunnskapsbasen
3. Lage tjenestelag for komponenter, lotter og målinger
4. Lage enkel UI for komponenter og lotter
5. Koble lot-data inn i ladeflyten
6. Bygge ut statistikk, varsler og eksport

## Første leveranse
MVP for første arbeidsrunde:
- standardkomponenter for kule, krutt og kaliber
- lotter for kule og krutt
- manuell registrering av målinger for kuler
- automatisk beregning av snittvekt og snittlengde per lot
- enkel kobling mellom ladning og valgt lot

## Åpne valg vi bør ta når vi implementerer
- Skal `brass` og `primer` være med i første migrasjon eller runde to?
- Skal målinger lagres som generisk nøkkel/verdi eller som egne felter per komponenttype?
- Skal vi regne statistikk ved lagring, ved behov, eller begge deler?
- Skal historiske ladninger fryse lot-statistikk ved lagring, eller alltid lese siste verdi?
