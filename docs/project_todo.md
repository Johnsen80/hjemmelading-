# Project TODO

Dette dokumentet er den operative arbeidslisten for neste store forbedringsrunde i Hjemmelading.
Det bygger pa struktur- og arbeidsflytplanen, inkludert ny kalibreringsdel i vapenprofilen.

## Last retning for motoren

Denne retningen er last til den blir eksplisitt endret.

- Programmet skal vaere offline-forst og fullt brukbart uten nett.
- Programmet skal ikke ha kobling til OpenAI eller andre eksterne AI-tjenester i kjerneflyten.
- Det er greit a bruke vanlige lokale biblioteker og utviklerverktoy, men selve motoren, presisjonen, kalibreringen og anbefalingslogikken skal eies internt.
- Systemet skal vaere larende uten generativ AI: det skal forbedre seg gjennom malte data, historikk, kalibrering og eksplisitt evidensvurdering.
- Programmet skal vaere solid, stabilt og sokkelrent nok til a kunne selges som faktisk produkt.
- Kjerneflyten skal fungere sokmlost nok til at brukeren ikke ma tenke pa interne modulgrenser eller gamle sidebaner.
- Gammel funksjonalitet som ikke styrker kjerneproduktet kan ryddes, isoleres eller fjernes dersom det gir bedre stabilitet og mindre driftsskyld.
- All viktig beslutningslogikk skal kunne forklares med fysikk, datagrunnlag, confidence og uncertainty.
- `measured`, `modeled`, `derived` og `recommended` skal skilles tydelig i lagring, analyse og UI.
- Hvis datagrunnlaget er tynt eller antatt, skal anbefalingsstyrken ned og usikkerheten opp.

## Last plan for smart load engine

Denne planen er last til den blir eksplisitt endret. Rekkefolgen under er na styrende for videre arbeid.

Styrende dokumenter for denne blokken:

- [local_smart_ammo_engine_plan.md](local_smart_ammo_engine_plan.md)
- [local_smart_ammo_engine_execution_plan.md](local_smart_ammo_engine_execution_plan.md)
- [local_smart_ammo_engine_todo.md](local_smart_ammo_engine_todo.md)
- [load_module_finish_todo.md](load_module_finish_todo.md)

1. [ ] Las pipe-, kammer- og hylsemodell
  Status: domenemodell last i `weapon_learning_domain_model.md`; neste konkrete arbeid er schema-migrering for pipekonfigurasjon og barrel-aware jump-data.
2. [ ] Definer malehierarki og datatillit
  Status: hierarkiet er na last som `weapon platform -> barrel -> barrel configuration -> session -> batch -> test session -> evidence`.
3. [ ] Bygg komponent- og lotmodell
4. [ ] Bygg vapen-, pipe- og komponentmatch
5. [ ] Koble kronograf og samlingsdata
6. [ ] Bygg en samlet ladeflyt
7. [ ] Lag laringsmotor per pipe
8. [ ] Ranger optimale ladekombinasjoner
9. [ ] Koble ballistikk til faktisk data
10. [ ] Bygg datainntak og analysepipeline
11. [ ] Rens, anonymiser og strukturer innsikt
12. [ ] Sikre robusthet med ende-til-ende tester

Praktiske regler for denne planen:

- Vi endrer ikke rekkefolgen uten eksplisitt beslutning.
- Punkt 1 og 2 er fundament for resten og skal styre datamodell og UI.
- Smartmotoren skal vaere pipe-spesifikk, kammerbevisst og komponentbevisst.
- Kuledata, krutdata, tennhettedata, hylsedata og lotdata er first-class input i hele planen.
- Brukerens malte data skal foretrekkes framfor generelle standarddata nar kvaliteten er god nok.
- Nye moduler skal kobles til eksisterende sannhetskilder, ikke lage parallelle modeller.
- Nye hjelpeflater skal bygges som lokal analyse og radgivning, ikke som ekstern AI-chat.

Se ogsa [load_engine_target_spec.md](load_engine_target_spec.md) for last teknisk spesifikasjon av fase 1.
Se ogsa [load_module_blueprint.md](load_module_blueprint.md) for konkret konsolideringsplan for lade-modulen.
Se ogsa [load_product_roadmap.md](load_product_roadmap.md) for last produktroadmap og prioriteringsrekkefolge for ladedelen.
Se ogsa [weapon_learning_domain_model.md](weapon_learning_domain_model.md) for last domenemodell og [weapon_learning_schema_plan.md](weapon_learning_schema_plan.md) for konkret migrasjonsrekkefolge.

## Last produktretning for ladedelen

Denne produktretningen er last til den blir eksplisitt endret.

- Ladedelen er prosjektets viktigste satsing.
- Målet er bedre presisjon i virkeligheten, ikke bare teoretisk fine resultater.
- Scientific Core, lokal laringsmotor, spredningslaere og neste-test-motor prioriteres foran nye sideflater.
- Produktet skal hjelpe brukeren a skille mellom ladningsfeil, skytterfeil, miljofeil og oppsettsfeil nar evidensen tillater det.
- Robusthet og repeterbarhet skal vektes hoyere enn pene enkeltskiver.
- Kart/feltballistikk og ammo-testmodul er viktige senere spor, men skal ikke ta fokus fra ladekjernen na.

## Neste anbefalte utviklingsblokker for ladedelen

Denne rekkefolgen er anbefalt na:

1. [ ] Samlet sannhetsmodell for ladekjernen
  Mal: builder, workflow, batch, chrono og target skal lese samme aktive kontekst og samme sannhetskilde.
2. [ ] Input quality, confidence og uncertainty
  Mal: alle kritiske rad skal vise evidenskvalitet, confidence, uncertainty og viktigste svakhet i datagrunnlaget.
3. [ ] Laringsprofil per rifle, pipe og lot
  Mal: chrono, target og kalibreringsserier skal oppdatere samme laringsprofil.
4. [ ] Spredningslaere og arsaksanalyse v1
  Mal: systemet skal kunne gi en konservativ forstevurdering av om avvik virker ladningsdrevet, skytterdrevet, miljodrevet eller oppsettdrevet.
5. [ ] Robusthetsmotor og neste-test-motor
  Mal: systemet skal kunne rangere robuste ladninger og foresla neste test med hoyest verdi.

## Status 2026-03-26

Ferdig eller godt i gang siden forrige planrunde:

- [x] Grunnmur for vapenprofil med stotte for bade rifle og pistol.
- [x] Ett vapen kan ha flere piper eller lop med eget kaliber, brukstype og status.
- [x] Aktiv pipe eller lop kan velges og brukes videre i arbeidsflyten.
- [x] Pipe- eller lopdata brukes na i ladeutvikling, simulering, ballistikk og harmonikk.
- [x] Munningsutstyr, innfesting og pipeprofil kan registreres med veiledning i UI.
- [x] H2O eller case capacity kan registreres fra skutte hylser med flere malinger og automatisk snitt.
- [x] H2O-visning har na antall malinger, min, maks, spread og enkel kvalitetsvurdering.
- [x] Kalibreringsserier kan lagres per aktiv pipe eller lop med ladedata, chrono, gruppe og bilde.
- [x] Builderen har na datagrunnlag-boks, trendanalyse, kalibreringstabell og grafer med filtre.
- [x] Filtre for krutt, kule, lot, avstand og temperatur er pa plass i kalibreringsvisningen.
- [x] Enkel temperaturdrift-visning og temperaturgraf er lagt inn.
- [x] Manuell registrering og redigering av egne kuler og krutt er pa plass.
- [x] Builderen gir na enklere vurdering av kule eller krutt mot pipe, inkludert Sg-estimat nar data finnes.
- [x] Manglende data for harmonikk og stabilitet forklares tydeligere og kan folges opp fra UI.
- [x] Vapenprofilen kan na apne builderen direkte med valgt aktiv pipe eller lop.
- [x] App-shell er omstrukturert til:
  `Ladeutvikling`, `Prosjekter`, `Ballistikk`, `Lager og batcher`, `Vapenprofiler`, `Lab og testing`, `Innstillinger`.
- [x] De viktigste hovedomradene har na egne startsider med hurtigvalg og kort arbeidsforklaring.
- [x] Startsider viser na enkel arbeidsstatus for prosjekt, profiler, batcher, lager og grunnleggende oppmerksomhetspunkter.
- [x] Prosjektet har na en stabil `core`-testsuite med dokumentert lokal kommando og CI-kjoring.
- [x] Batcher lagrer na prosjektkontekst og kan aapnes direkte fra relevante startsider.
- [x] Ladeokter og skyteokter arver na aktivt prosjekt og vises med prosjektkontekst i loggboka.
- [x] Historikkvisningen kan na filtrere og lese sesjoner per prosjekt.
- [x] Aktiv importopprydding i `src/modules` er gjennomfort for levende `.py`-moduler.
- [x] `ruff check src tests` er na gronn sammen med `pytest -q -m core`.
- [x] Malarbeid for bugjakt har gitt konkrete guard-fikser i loggbok, GRT-import, smart wizard, ladder test og flere profil-/inventory-flyter.
- [x] Bugjakt-passasjen er utvidet med flere konkrete runtime-fikser i chronograph, workflow-resume, barrel-valg, measurement wizard, environmental compare, component database, drop chart og workflow-flyter.
- [x] Guard-testene for brukerflytene er utvidet betydelig og holder seg gronne sammen med `core`.
- [x] Hele den moderne testsuiten under `tests/` er na verifisert gronn: `111 passed`.
- [x] `Ladeutvikling` har na tydeligere `Testplan`, pressure/spike-varsling og handlingsnavigasjon til batch, chrono og target-analyse.
- [x] Workflow, batch, chrono og target-analyse deler na eksplisitt workflow-kontekst i metadata og/eller lagret oppsummering.
- [x] Startsidene og hovedlandingen viser na aktiv workflow-status med anbefalt neste handling basert pa faktisk readiness.
- [x] `stop`, `trenger data` og `ready` apner na riktig verktøy med fokus for trykkgjennomgang, datainnsamling eller neste steg i batch.
- [x] CSV- og GRT-import har na mer tolerant feltmapping, tydeligere importrapport og egne tester for validering.
- [x] `component_database` har na fungerende import/eksport for bullets og powders via JSON/CSV i stedet for `Coming soon`.
- [x] Import/eksport har na ogsa runde-trip-testgrunnmur for `component_database` og ORM-basert CSV for krutt og kuler.
- [x] Historikk- og komponenteksport har na enkel schema-versjonering og eksportmetadata i JSON/CSV, med bakoverkompatibel lasting for komponentdatabasen.
- [x] ORM-basert CSV-eksport for krutt og kuler har na ogsa egen schema-kolonne, slik at eksportsporet er mer konsekvent pa tvers av moduler.
- [~] Enhetssystemet har na faktiske konverteringshelpers for lengde, vekt, hastighet, trykk og avstand, og brukes i `Drop Chart`, `Vapenprofil`, `Chronograph`, `Target Analyzer`, `Batch Workspace` og `Historikk`.
- [x] `Bruksprofil` er na lagt inn i `Ladeutvikling`, lagres per workflow og styrer testplan mot presisjon, trening eller jaktbruk.
- [x] Workflow lagrer na ogsa eksplisitt kule- og kruttkobling i `load_development_workflows`.
- [x] Første versjon av `Impact Window` er na levert i workflow, startsider og builder for jaktstyrte workflows.
- [x] `Impact Window` viser na ogsa enkel `confidence` og `uncertainty` i stedet for bare punktestimat.
- [x] Lotkompensasjon viser na ogsa `confidence` og enkel `uncertainty` i bade workflow og builder.
- [x] Workflow-readiness, `best next test` og komponentrobusthet viser na egne confidence-/uncertainty-lag.
- [x] `Evidenskvalitet` er na innfort som et samlet signal for readiness, robusthet, lotverifisering, neste test og impact-vurdering.
- [x] `Evidenskvalitet` vises na i wizard-summary, workflow-detaljer og startsidene, med korte checks som forklarer hva som trekker vurderingen opp eller ned.
- [~] I18n-sporet har na faktisk grunnmur med fallback, manglende-nokkel rapportering og synlig sprakstatus i settings.
- [~] Felles i18n-lag brukes na i settings, startsider, `Batch Workspace`, `Ladeutvikling`, `Modern Load Builder` (inkludert sentrale dialoger og safety/status-tekster), `Chronograph Import`, `Target Analyzer`, `Historikk` og `Component Database`.
- [ ] Fullfore sprakpakke-sporet som langsiktig losning i stedet for a hardkode appen til engelsk.
  Mal:
  engelsk som profesjonell standard/default, norsk som valgbart sprak, og all synlig tekst gjennom ett konsekvent i18n-lag.
- [ ] Lage konkret restliste for full sprakbytting i hovedflater, eldre verktøy, dialoger, rapporter og eksporttekster.
- [x] `Auto / G1 / G7` er na sydd inn som felles dragspor i `Drop Chart`, ammo-profiler, wizard, `Modern Load Builder`, `Zero Shift` og `Ladeutvikling`.
- [x] Appen har na egen innstilling for foretrukket dragmodell, slik at arbeidsstandarden kan styres sentralt.
- [ ] OBT/harmonikksporet skal viderefores som forsiktig heuristikk: nyttig for nodejakt, men ma alltid bekreftes med chrono, target og kalibreringsprofil.

## Status 2026-04-09

Ferdig siden forrige statusblokk:

- [x] `rifle_profile_editor` lagrer na kammerdetaljer per pipe via `chamber_details_by_barrel` i stedet for a blande dem pa våpenniva.
- [x] Munningsutstyr, lyddemper-/bremsestatus og POI-shift lagres na direkte pa aktiv pipe i `profile_json["barrels"]`, med legacy-speiling beholdt for kompatibilitet.
- [x] Pipevelgere i kule-, kammer- og munningsfaner holdes na synkronisert slik at aktiv pipe er konsistent i editoren.
- [x] Aktiv pipekonfigurasjon er na standardisert via `src/utils/barrel_configuration.py` og brukes i `Modern Load Builder`, `Smart Loading Wizard` og `Batch Workspace`.
- [x] Nye batcher, batch-sesjoner og wizard-opprettede ladeokter arver na `barrel_configuration_id`, `barrel_configuration_name` og snapshot automatisk.
- [x] Apen aktiv `load_development_session` synkroniserer na ogsa aktiv pipekonfigurasjon tilbake til kanonisk runtime-rad via `_sync_active_load_session_context()`.
- [x] Guard-tester dekker pipe-scopet editorlogikk og runtime-propagasjon; full suite var sist verifisert gronn pa `486 passed, 1 skipped, 5 deselected`.

## Neste konkrete framdrift

Denne rekkefolgen er anbefalt videre fra dagens status:

1. [ ] Gjore sammenligning, historikk og laring pipekonfigurasjons-sensitive slik at evidens ikke blandes mellom `bare muzzle`, brems og lyddemper-oppsett pa samme pipe.
2. [ ] La anbefalinger og confidence-signaler eksplisitt vise hvilken pipekonfigurasjon de bygger pa i UI og analysepayloads.
3. [ ] Innfore eksplisitte navngitte pipekonfigurasjoner i profil/editor/runtime, utover dagens utledede ID fra aktiv pipe + munningsstatus.
4. [ ] Utvide ende-til-ende tester rundt pipekonfigurasjon pa tvers av editor -> wizard -> builder -> batch -> historikk.

## Ny arbeidsblokk: Scientific Accuracy Core

- [ ] Følg [scientific_accuracy_todo.md](scientific_accuracy_todo.md) som ny hovedplan for felles ballistikkmotor, miljodata, kalibrering, input-kvalitet og terrengrisiko.
- [ ] Samle ekstern ballistikk i ett felles motorlag i stedet for flere modulspesifikke beregninger.
- [ ] Gjore miljodata og `density altitude` til first-class input i alle sentrale ballistikkvisninger.
- [ ] Lage en samlet kalibreringsprofil per våpen, pipe/løp, lot og miljøvindu.
- [ ] Innføre felles input-quality / evidence-gating før kritiske råd og simuleringer.
- [ ] Innføre fyllrate, kompresjonsgrad og modellert burn completeness som del av internballistisk QA.
- [ ] Lage `terrengrisiko` i kartmodulen som første realistiske steg mot mer avansert terrenganalyse.
- [~] Lage tverrmodul-verifisering som sikrer at samme input gir samme svar overalt.
  Første konsistensblokk er na testet for delt ballistikkbane (`drop`, `retained velocity`, `time of flight`, `wind drift`, `zero shift`); videre dekning gjenstar for flere moduler og referansecaser.

## Ny arbeidsblokk: Lokal læringsmotor

- [ ] Folg [local_smart_ammo_engine_execution_plan.md](local_smart_ammo_engine_execution_plan.md) som last gjennomforingsplan for lokal smart ammo engine.
- [ ] Folg [local_smart_ammo_engine_todo.md](local_smart_ammo_engine_todo.md) som last og bindende todo-liste for motorblokken.
- [ ] Gjore `load_development_sessions` + runtime-laget til eneste kanoniske sannhetskilde for aktiv ladeutvikling.
- [ ] Innfore en lokal laringsprofil per våpen og pipe med bias, robustness, confidence, uncertainty og anbefalt neste steg.
- [ ] Innfore lot-laring for kulelot, kruttlot, tennhettelot og hylselot med eksplisitt drift- og konsistenssignaler.
- [ ] La kalibreringsserier, chrono og samlingsdata oppdatere samme laringsprofil i stedet for parallelle delmodeller.
- [ ] Lage en eksplisitt anbefalingsmotor som rangerer neste test ut fra fysikk + historikk + inputkvalitet.
- [ ] Erstatte AI-begrepet i kjerneflytene med lokal analyse, lokal radgiver eller laringsmotor.
- [ ] Fjerne eller deaktivere OpenAI-sporet fullstendig i produktets hovedflyt.
- [ ] Sikre at alle råd kan forklares med: datagrunnlag, endring, effekt, confidence, uncertainty og neste verifisering.
- [ ] Innfore modellstatus som minst viser: `rå modell`, `delvis kalibrert`, `godt kalibrert`.
- [ ] La systemet skille mellom lokal kunnskap per våpen/pipe og generelle referansedata fra standard eller produsent.

## Ny arbeidsblokk: Vitenskapelig verifisering

- [ ] Lage referansedatasett med kjente ladeoppsett, miljødata og forventede utfall for regresjonstesting av motoren.
- [ ] Innfore holdout-verifisering der nye serier testes mot modell uten at de samme dataene brukes til kalibrering først.
- [ ] Logge modellversjon, kalibreringsstatus og svakeste antakelse sammen med sentrale resultater.
- [ ] Innfore eksplisitte uncertainty-band for fart, drop, impact-vurdering og anbefalt arbeidsvindu der datagrunnlaget tillater det.
- [ ] Kreve at kritiske råd viser hva som er målt, hva som er antatt og hva som bor verifiseres videre.
- [ ] Lage systematiske tester for at samme input gir samme output i builder, workflow, ballistikk og rapportspor.

## Fase 1: Struktur og retning

- [ ] Lase hovedstruktur for appen.
- [x] Lase startsiden som hovedinngang.
- [x] Lase hovedmeny:
  `Ladeutvikling`, `Prosjekter`, `Ballistikk`, `Lager og batcher`, `Vapenprofiler`, `Lab og testing`, `Innstillinger`.
- [~] Flytte AI, bildeanalyse og kronografimport inn i arbeidsflytene.
- [~] Flytte AI, bildeanalyse og kronografimport inn i arbeidsflytene.
  Batch, chrono og target er na koblet direkte til workflow-kontekst; gjenstarende arbeid er mer komplett ende-til-ende styring og visning i UI.
- [ ] Definere hvilke arbeidsflyter som er kjerneflyter i V1.
- [ ] Lage enkel prioriteringsliste for hva som ma bygges forst.
- [x] Lage enkel prioriteringsliste for hva som ma bygges forst.
- [ ] Bygge arbeidsflytene slik at de veileder brukeren og reduserer risiko for feilregistrering.
- [ ] Lage tydelige steg, hjelpetekster og validering i alle kjerneflyter.
- [ ] Bygge inn tydelige muligheter for at brukeren kan stille sporsmal nar noe er uklart.

## Fase 2: Vapenprofil som kjerne

- [x] Bygge vapenprofil som et generelt system for bade rifle og pistol.
- [x] Lage `vapentype` i profilen:
  `Rifle`, `Pistol`, med mulighet for flere typer senere.
- [x] Gjore vapenprofil til hovedstartpunkt for ny ladeutvikling.
- [x] Utvide vapenprofil med lop, optikk, nullprofil og tekniske data.
- [x] Stotte systemvapen med flere piper eller lop under samme vapen.
- [x] La hver pipe eller hvert lop ha eget kaliber, brukstype og status:
  `treningspipe`, `konkurransepipe`, `jaktpipe`, `reservepipe`.
- [x] Lage pipe- eller lopprofiler under vapenprofilen i stedet for flat struktur.
- [x] La hver pipe eller hvert lop ha eget oppsett for munningsutstyr:
  `brems`, `comp`, `lyddemper`, eller ingen.
- [x] Lagre vekt og lengde for munningsutstyr pa pipe- eller lopniva.
- [ ] Koble vapenprofil til ladninger, batcher og testhistorikk.
- [~] Koble vapenprofil til ladninger, batcher og testhistorikk.
- [x] Lage oversikt over historikk per vapenprofil.
- [ ] Lage grunnlag for solver-kalibrering per vapen.
- [x] Tilpasse vapenprofil-UI etter vapentype slik at pistol og rifle far ulike relevante felt.

## Fase 3: Kalibrering i vapenprofil

- [x] Legge til `Kalibrering` som egen seksjon i vapenprofil.
- [x] Definere hva som er `malt`, `beregnet` og `utledet`.
- [x] Knytte kalibrering primart til valgt pipe eller lop, ikke bare til vapenet generelt.
- [x] Lage registrering av kalibreringsokt med `5-20 skudd`.
- [x] Lage felter for ladedata:
  `krutt`, `kruttmengde`, `kule`, `settedybde`, `neck tension`, `hylse`, `tennhette`, `COAL/CBTO`.
- [x] Lage felter for skyteforhold:
  `avstand`, `temperatur`, `vind`, `dato`, `notater`.
- [x] Lage felter for resultatdata:
  `kronografdata`, `snitthastighet`, `ES`, `SD`, `gruppestorrelse`, `POI`, `bilde av samling`.
- [x] Lage oversikt over tidligere kalibreringsokter.
- [x] Lage oppsummering av hva programmet har lart om vapenet.
- [ ] Lage `modellstatus` og tillitsniva:
  `lav`, `middels`, `hoy`.

## Fase 4: Database og datamodell

- [x] Lage datamodell for generisk vapenprofil som stotter bade rifle og pistol.
- [x] Lage datamodell for pipe eller lop under vapenprofil.
- [x] Lage datamodell for pipe-spesifikke maledata og tekniske data.
- [x] Lage datamodell for munningsutstyr per pipe eller lop:
  type, modell, vekt, lengde, monteringsstatus.
- [x] Lage datamodell for kalibreringsokt.
- [x] Lage datamodell for skuddserie.
- [x] Lage datamodell for kronografdata.
- [x] Lage datamodell for bilde- og samlingsvedlegg.
- [x] Lage felter for pipe-spesifikke hylsemal:
  standardmal, trimlengde, skuldermal, base-til-datum, neckmal.
- [x] Lage felt for pipe-spesifikt H2O-volum.
- [x] Sikre at hylsemal og H2O-volum folger pipeprofilen og brukes i ladeutvikling.
- [ ] Lage database-tabeller for kalibrering.
- [ ] Knytte tabellene til vapenprofil.
- [x] Knytte kalibrering og ladedata til riktig pipe eller lop.
- [~] Knytte dem til ammo- eller ladningsdata der det er relevant.
  `bc_segments_json` migreres na trygt for eldre databaser i `bullets` og `ammo_profiles`, og dette er verifisert med egen migreringstest.
- [x] Lage migreringer for nye tabeller.
- [x] Sikre at gammel data fortsatt fungerer.

## Fase 5: Ladeutviklingsflyt

- [~] Lage standard startflyt:
  vapenprofil -> nullprofil -> komponentmodus -> formal.
- [~] Lage standard startflyt:
  Workflowen har na eksplisitt bruksprofil/formal i wizard og plan; gjenstarende arbeid er nullprofil og enda tydeligere inngang fra vapenprofil.
- [x] Kreve valg av riktig pipe eller lop nar et vapen har flere konfigurasjoner.
- [x] Bruke pipe-spesifikke hylsemal og H2O-volum aktivt i ladeutvikling.
- [x] Lage `Bygg ladning`.
- [x] Lage `Juster og simuler`.
- [ ] Lage `Testplan`.
- [~] Lage `Testplan`.
- [~] Lage `Testplan`.
  Testplan er na synlig i wizard og workflow-detaljer, med pressure-advisory og neste steg; gjenstarende arbeid er dypere automatikk fra resultater tilbake til videre plan.
- [x] Lage `Resultater`.
- [x] Lage `Sammenligning`.
- [ ] Koble hele flyten til vapenprofil og prosjekt.
- [~] Koble hele flyten til vapenprofil og prosjekt.
- [~] Koble hele flyten til vapenprofil og prosjekt.
  Workflow -> batch -> chrono -> target -> historikk er na delvis eksplisitt koblet; fortsatt arbeid gjenstar for enda tydeligere ID-baring og visning i alle flyter.
- [~] Bygge arbeidsflyten slik at den ogsa tilpasser seg formålet med ladningen.
  `Bruksprofil` styrer na testplan, neste steg og jaktvurdering; gjenstarende arbeid er dypere tilpasning av UI og analyse i flere moduler.
- [ ] Tilpasse arbeidsflyten til bade rifle og pistol.
- [ ] Tilpasse flyten for bade enkel og avansert bruker.
- [x] Legge inn tydelige kontrollpunkter som varsler om manglende eller sannsynlig feil data.
- [x] Vise forklaringer direkte i flyten for hva endringer betyr for indre og ytre ballistikk.

## Fase 6: Komponenter, lager og batcher

- [ ] Stotte bade batch-basert og fri oppbygging.
- [ ] Lage bedre batchstruktur for kule, krutt, hylse og tennhette.
- [ ] Lagre lotnummer, kostnad, beholdning og maledata.
- [ ] Lagre utvidede felter:
  `hylsevolum`, `trimstatus`, `antall omladinger`, `neck-tykkelse`, `gloding`, `kulelengde`, `vektvariasjon`.
- [ ] Koble batcher til vapenprofil og testserier.
- [ ] Koble kostnadsdata til ladning og analyse.
- [ ] Beregne fyllrate fra hylsevolum og kruttdata, og varsle ved svært lav eller komprimert ladning.

## Fase 7: Resultater og laring

- [x] Lage bedre logging av testresultater.
- [x] Lagre gruppestorrelse, POI, klikk, kronografdata, bilde og vaerforhold.
- [x] Lage tydelig `predicted vs observed`.
- [~] Sammenligne resultater per batch.
  Spredningslære v1 bruker nå eksisterende batch-, chrono-, gruppe-/target- og notatdata til et konservativt årsakshint for ammo/prosess, skytter/serie, setup/utstyr, miljø/forhold, node/pipetiming, trykk/ammo-watch eller utilstrekkelig evidens. Den bruker også vertikal/horisontal samlingsmønster og POI-drift når dette finnes. Hvert signal får nå en strukturert kontrollplan med primærhandling, skuddplan, hva brukeren bør unngå og suksesskriterier. I tillegg får batchen en decision gate som sier om systemet bør stoppe for sikkerhet, kreve kontrollserie, hindre tidlig forkasting eller åpne for forsiktig én-variabel tuning. Bruksmål er koblet inn slik at jakt prioriterer kaldskudd/feltstøtte/sikkerhet, konkurranse prioriterer repeterbarhet og setup-/lot-separasjon, og hobby/læring får mer pedagogisk én-variabel-om-gangen-fokus. Datakvalitet vurderes nå som eget lag med score, nivå, styrker, begrensninger, mangler og anbefalt logging. Læringsforklaring er også lagt til med enkel forklaring, årsakskjede, hva brukeren bør følge med på og profiltilpasset takeaway. En konkret neste-capture-checklist peker nå på hvilke observasjoner som vil gjøre neste beslutning bedre. Batchen får også en egen validation/readiness-status per bruksmål, slik at systemet kan si om ladningen fortsatt bare er foreløpig, ikke feltklar ennå, ikke ranking-klar ennå eller klar for neste læringssyklus. Batch-workspace beregner nå også en konservativ sammenligningsbasis mellom søsterbatcher, slik at sterkere evidens og readiness kan slå heldige enkelserier, og legger ved et comparison advisory som sier hva som må bekreftes før en batch bør løftes over andre kandidater. Denne comparison-logikken sendes nå også videre til runtime og learning guidance, har fått en strukturert head-to-head / promotion-protokoll for matchet sammenligning mellom batcher, forklarer nå også hvilken enkeltfaktor som holder en batch tilbake i sammenligningen og hva som bør måles neste gang, kan nå gi et eksplisitt comparison verdict og en comparison checklist før promotering, viser nå også et comparison scorecard som peker på om batchen hovedsakelig taper på presisjon, evidenskvalitet eller readiness, har fått comparison confidence + learning note for å gjøre sammenligningen mer ærlig og mer pedagogisk, har nå også en egen comparison acceptance gate som sier hva som faktisk må være sant før en batch får lov til å overta som jakt-, konkurranse- eller læringskandidat, har nå også acceptance progress med score, nivå og oppfylte betingelser slik at brukeren ser hvor nær batchen faktisk er en ærlig promotering, har nå også et samlet comparison status board + next test brief som viser hvem som leder, hvilken readiness-band batchen ligger i, og hvilken sammenligningstest som faktisk bør skytes nå, har nå også profile priority + mission brief slik at jakt, konkurranse og læring får hver sin guardrail, suksessmarkør og konkrete oppdrag for neste sammenligningsøkt, har nå også portfolio + session strategy som løfter vurderingen fra én batch til hele kandidatsettet og sier hva slags økt neste session faktisk bør være, har nå også campaign view + action plan som samler hele batch-settet i ett toppnivåbilde og peker på hva som faktisk skal gjøres først i neste runde, har nå også campaign board + session queue + session manifest slik at batchene kan sorteres som shoot_now, confirm, hold, pause eller reject_watch og neste skyteøkt kan beskrives som en konkret, konservativ kjøreplan, og har nå også next session brief + today plan slik at systemet kan si hva som skal skytes først i dag, hva som skal verifiseres først, og hva som bevisst skal holdes tilbake. Videre arbeid er mer visuell sammenligning og flere normaliserte skytestøtte-/stilling-/rytmefelt.
- [x] Sammenligne resultater per temperatur.
- [x] Sammenligne resultater per vapenprofil.
- [x] Bruke malt data til a forbedre anbefalinger.

## Fase 8: Harmonikk og analyse

- [x] Lage forste versjon av harmonisk profil basert pa malt data.
- [x] Bruke settedybde, kruttmengde, hastighet og gruppestorrelse i analysen.
- [x] Ta hensyn til pipe- eller lopoppsett med brems, comp eller lyddemper i harmonisk analyse.
- [x] Regne vekt og lengde pa munningsutstyr som del av pipekonfigurasjonen.
- [ ] Lage nodeomrader som anbefaling, ikke fasit.
- [x] Lage temperaturfolsomhetsanalyse.
- [ ] Lage stabilitetsvurdering over tid.
- [x] Vise hvor sikkert datagrunnlaget er.

## Fase 9: Ballistikk og optikk

- [x] Koble ballistikk til kalibrert vapenprofil.
- [x] Bruke reell muzzle velocity der data finnes.
- [ ] Integrere nullprofil, klikkverdi og optikk i arbeidsflyten.
- [ ] Lage bedre dopecard og korreksjonsforslag.
- [ ] Skille mellom teoretisk og kalibrert ballistikk.
- [x] Vise tydelige sikkerhetsgrenser og advarsler.

## Fase 10: Lokal analyse og læring i arbeidsflyten

- [~] Erstatte eksisterende AI-spor med lokal analysehjelp i ladeutvikling.
- [ ] Erstatte AI-spor i prosjektvisning med lokal kontekst- og evidensbasert oppsummering.
- [ ] Erstatte AI-spor i ballistikk og testing med forklarbar, lokal rådgivning.
- [x] Bruke vapenprofil, batch og historikk som kontekst.
- [~] Lage lokal stotte for forklaring av resultater.
- [~] Lage lokal stotte for forslag til neste test.
  Spredningssignal fra batchanalyse skrives nå videre til `evidence_summary_json` og `learning_state_json.summary`, og `modern_load_builder` bruker signalet til mer praktisk guidance for kontrollserie, miljøkontroll, setup-drift eller ammo/prosess.
- [x] Unnga los chatbot som egen hovedmodul.
- [ ] Fjerne ekstern AI-konfigurasjon fra produktretningen nar lokal analysebane er komplett.
- [x] Lage AI-stotte som forklarer hva konkrete endringer gjor med trykk, hastighet, stabilitet, rekyl og kulebane.
- [x] Lage AI-stotte som oppdager sannsynlig feilregistrering og ber brukeren bekrefte eller rette data.
- [ ] Lage AI-stotte som tilpasser forklaringene til brukermodus og erfaringsniva.
- [x] Lage AI-stotte som oppmuntrer brukeren til a sporre nar noe er uklart.
- [x] Lage AI-stotte som kan stille oppklarende sporsmal tilbake nar brukerens data eller valg virker usikre.

## Fase 11: Visualiseringer

- [ ] Lage patronvisning med kule, hylse, fyllingsgrad og settedybde.
- [ ] Vise kompresjonsgrad og estimert forbrent andel i patron- og ladningsvisning.
- [x] Lage bedre grafer for trykk, hastighet, temperatur og stabilitet.
- [ ] Lage nodekart for kruttmengde vs resultat.
- [ ] Lage nodekart for settedybde vs resultat.
- [ ] Lage treffpunkt- og optikkvisning.
- [ ] Lage tydelig visning av forventet vs faktisk POI.
- [x] Lage selvforklarende grafer med tydelige etiketter, usikkerhet og forklaring av hva brukeren ser.
- [ ] Lage visuelle simuleringer for indre ballistikk, ytre ballistikk og effekt av parameterendringer.
- [x] Lage visninger som hjelper brukere med lite erfaring a forsta hva som skjer nar de endrer ladedata.

## Fase 12: Brukermoduser

- [ ] Lage modusene:
  `Enkel`, `Avansert`, `Lab`.
- [ ] Styre hvor mye UI som vises per modus.
- [ ] Styre hvor mange avanserte parametere som vises.
- [ ] Tilpasse forklaringer, rad og varsler per modus.
- [ ] Gi mer pedagogiske forklaringer i enkel modus og mer tett fagdata i avansert eller labmodus.

## Fase 13: Enheter, validering og brukerhjelp

- [x] La brukeren velge mellom metrisk og tommer der det er relevant.
- [ ] Stotte blandet bruk av enheter pa en trygg mate, med tydelig visning av aktiv enhet.
- [~] Lage robust enhetskonvertering for lengde, vekt, volum, hastighet, trykk og avstand.
- [~] Lage robust enhetskonvertering for lengde, vekt, volum, hastighet, trykk og avstand.
  Grunnmur for mm/in, grains/gram, fps/mps, yards/meters og psi/bar er pa plass; den brukes na ogsa i chrono-, target-, batch- og historikkvisning. Gjenstarende arbeid er bredere bruk i flere input- og analyseflyter.
- [ ] Lage felter som viser bade innskrevet enhet og intern standardenhet ved behov.
- [ ] Varsle om sannsynlige enhetsfeil, som for eksempel tommer lagt inn som millimeter eller omvendt.
- [x] Lage validering med fornuftige grenser og forklarende feilmeldinger.
- [x] Lage hjelpetekster og eksempler i felter der brukere ofte registrerer feil.
- [ ] Lage oppsummeringsskjerm for a la brukeren kontrollere kritiske data for lagring.
- [x] Lage enkle `Lurer du pa noe?`- eller `Vil du ha forklaring?`-punkter i kritiske deler av UI-et.
- [x] Gi brukeren rask tilgang til kort forklaring, eksempel og anbefalt metode i felt med hoy feilrisiko.

## Fase 14: Testing og kvalitet

- [ ] Lage tester for kalibreringsdata.
- [ ] Lage tester for lagring og lasting av vapenprofil.
- [~] Lage tester for arbeidsflytene.
- [~] Lage tester for arbeidsflytene.
  Guard-tester dekker na mange stale-selection og missing-row baner i sentrale UI-flyter.
- [ ] Lage tester for `predicted vs observed`.
- [ ] Lage tester for koblinger mellom vapenprofil, batch og ladning.
- [~] Lage tester for koblinger mellom vapenprofil, batch og ladning.
- [~] Lage tester for koblinger mellom vapenprofil, batch og ladning.
  Workflow-koblingene har na egne plan-/context-tester; mer ende-til-ende dekning gjenstar.
- [x] Utvide smoke-tester for hovedflytene.
- [~] Lage tester for enhetskonvertering og blandet bruk av metriske og imperiale enheter.
- [~] Lage tester for enhetskonvertering og blandet bruk av metriske og imperiale enheter.
  Kritiske konverteringer er na testet i `test_units.py`, og UI-bruk er dekket i `drop_chart_generator` og `weapon_profile_dialog`; mer ende-til-ende dekning gjenstar.
- [ ] Lage tester for validering av ugyldige og uvanlige brukerdata.

## Fase 15: Dokumentasjon

- [x] Oppdatere plandokument med kalibrering som egen del.
- [ ] Lage spesifikasjon for vapenprofil.
- [ ] Lage spesifikasjon for kalibrering.
- [~] Lage spesifikasjon for startside og menystruktur.
- [ ] Lage spesifikasjon for ladeutviklingsflyt.
- [x] Holde denne TODO-listen oppdatert.
- [~] Dokumentere enheter, konverteringer og hvordan programmet handterer ulike malsystemer.

## Neste arbeidsblokk

Anbefalt neste fokus etter app-shell, importopprydding og testgrunnmur:

- [~] Koble vapenprofil, batcher, ladning og prosjekt tydeligere sammen i arbeidsflytene.
- [~] Gjore `Ladeutvikling` mer stegstyrt med tydelig `Testplan`, validering og prosjektkobling.
- [~] Gjore `Ladeutvikling` mer stegstyrt med tydelig `Testplan`, validering og prosjektkobling.
  Testplan, pressure-advisory og workflow-kontekst er pa plass; neste steg er tettere automatisk kobling til faktiske analyseresultater og videre steg i UI.
- [ ] Ta faktiske UX- og funksjonsbugs som gjenstar na som infrastrukturstoyen er ryddet bort.
- [ ] Utvide `core` med et par flere moderne flyttester nar arbeidsflytene er strammere.
- [ ] Kjore en bredere sluttpassasje og prioritere gjenstaende reelle funksjonsfeil over nye strukturendringer.
- [~] Kjore en bredere sluttpassasje og prioritere gjenstaende reelle funksjonsfeil over nye strukturendringer.
  Moderne testsuite og lint er gronn; neste steg er a bruke dette signalet til maalrettet UX- og funksjonsprioritering.

## Fase 17: Vitenskapelig 1.0 og produktloft

- [ ] Lage et felles `Scientific Core` som skiller mellom:
  `malt`, `modellert`, `utledet anbefaling`, `confidence` og `uncertainty`.
- [ ] Lage felles `Load Evidence Record` for rifle, pipe eller lop, batch, lot, chrono, target, vaer, trykktegn og modellresultater.
- [ ] Lage `confidence engine` som graderer datakvalitet for trykk, velocity, presisjon, harmonikk og jaktvurdering.
- [ ] Lage `calibration engine` som justerer modellene mot faktisk chrono, H2O, temperatur og historikk for valgt pipe eller lop.
- [ ] Vise usikkerhet og datakvalitet i UI, ikke bare ett estimat eller en enkel status.
- [ ] Skille tydelig i UI og eksport mellom `malt`, `beregnet` og `anbefalt`.
- [ ] Lage valideringspakke for `predicted vs observed` pa faktisk datasett.
- [ ] Lage faglige disclaimers for trykk, sikkerhet og terminal vurdering.

## Fase 18: Jakt, kuleoppforsel og anslagsvurdering

- [ ] Lage `Bruksprofil` i ladeutvikling:
  `Konkurranse`, `Trening`, `Jakt smavilt`, `Jakt radyr`, `Jakt hjort/elg`, `Langhold jakt`.
- [ ] Koble `Bruksprofil` til testplan, anbefalinger og vurdering av neste steg.
- [ ] Utvide kuleprofil med jakt- og terminalfelt:
  konstruksjon, kulekategori, minimum ekspansjonshastighet, anbefalt impact-vindu, typisk bruksomrade.
- [ ] Lage `Impact Window`-vurdering i ladeutvikling basert pa anslagshastighet, energi, momentum og kulekategori.
- [ ] Vise kuleoppforsel samlet som:
  `Indre ballistikk`, `Ytre ballistikk`, `Anslag / jaktvurdering`.
- [ ] Lage jaktspesifikk testplan med fokus pa kald pipe, forsteskudd, realistiske jaktavstander og praktisk skytestilling.
- [ ] Lage forsiktig terminal vurdering som beskriver sannsynlig kuleoppforsel uten a late som programmet kan forutsi faktisk sarkan al i dyr.
- [ ] Lage tydelige varsler nar valgt kule eller anslagshastighet ligger utenfor kulas antatte arbeidsvindu.

## Fase 19: Avansert presisjonsanalyse

- [ ] Lage bedre presisjonsmal enn bare gruppestorrelse:
  `mean radius`, `vertikal spredning`, `horisontal spredning`, `POI-shift`.
- [ ] Lage shot-count adequacy og advarsel nar for fa skudd brukes til sterke konklusjoner.
- [ ] Lage bedre temperaturmodell og temp-kalibrering per pipe eller lop og lot.
- [ ] Lage SPC eller kontrollkart for lotdrift, batchdrift og velocity-drift over tid.
- [ ] Lage adaptive testplaner som foreslar neste batch eller skudd der informasjonsgevinsten er storst.
- [ ] Lage sporbar `scientific audit trail` for anbefalinger, slik at brukeren kan se hvilke data og modeller som ligger bak.

## Fase 20: Selvlærende pipe eller lop og digital tvilling

- [ ] Lage `Weapon/Barrel Learning Profile` per pipe eller lop.
- [ ] Lagre laerte parametre separat fra ramalinger og manuelle profilfelter.
- [ ] La systemet bygge kalibrert velocity-offset per pipe eller lop basert pa faktisk chrono-historikk.
- [ ] La systemet laere temperaturrespons per pipe eller lop og bruke den i videre anbefalinger.
- [ ] La systemet laere typisk ES/SD-niva per pipe eller lop og bruke det i confidence-vurdering.
- [ ] La systemet laere robusthet i node eller ladningsomrade over tid, ikke bare ett enkelt testresultat.
- [ ] Spore `cold bore` vs `warm bore` per pipe eller lop, inkludert mulig POI-shift.
- [ ] La systemet merke drift nar lot, pipe, temperatur eller slitasje endrer oppforsel over tid.
- [ ] Lage en enkel modell for throat wear, round count og kalibreringsdrift per pipe eller lop.
- [ ] Knytte digital tvilling til `Ladeutvikling`, `Batch Workspace`, `Chronograph`, `Target Analyzer` og jaktvurdering.
- [ ] Vise tydelig `confidence` og `datagrunnlag` for hva den digitale tvillingen tror den vet om valgt pipe eller lop.
- [ ] Lage tydelig varsel nar den digitale tvillingen er basert pa for lite data til a gi sterke anbefalinger.

## Fase 21: Selvlærende komponenter og lotter

- [~] Lage `Case Lot Learning` for hylselotter:
  H2O, spredning, omladinger, trimdrift, gloding, neck tension og forventet levetid.
- [~] Lage `Powder Lot Learning` for kruttlotter:
  faktisk velocity offset, temperaturrespons, lotdrift og robusthet i ulike ladningsvinduer.
  Forste grunnmur er pa plass med egne laeringsprofiler for kruttlot og oppsummering i `Component Lot Tracker`; neste steg er tettere kobling til workflow, chrono og batchkontekst.
- [ ] Lage `Bullet Performance Learning` per kuleprofil og pipe eller lop:
  seating-depth-folsomhet, stabilitet, velocity-vindu og presisjonstrender.
- [ ] Lage felles lot- og komponentvurdering som kombinerer pipe, hylse, krutt og kule til en samlet robusthetsscore.
- [ ] Oppdage nar nytt lot avviker tydelig fra tidligere lot og varsle brukeren.
- [ ] Knytte komponentlaering til `Batch Workspace`, `Ladeutvikling`, `Chronograph`, `Target Analyzer` og historikk.
- [ ] Vise komponentspesifikk `confidence`, `drift` og `datagrunnlag` i UI.
- [ ] Lage forslag til neste test basert pa hvilken komponent som ser ut til a skape mest usikkerhet.

## Fase 16: Fysikk, modeller og nokkeldata

- [x] Behandle `vapen -> pipe eller lop -> konfigurasjon` som grunnmodell i systemet.
- [x] La pipe eller lop vaere den primare enheten for ladeutvikling og kalibrering.
- [x] Lage pipe- eller lopkonfigurasjon som ogsa inkluderer munningsutstyr.
- [x] Lagre pipe-spesifikke hylsemal og H2O-volum som del av kalibreringsgrunnlaget.
- [x] Bruke pipe-spesifikke hylsemal og H2O-volum direkte i ladeutvikling og analyse.
- [x] Implementere grunnmodell for gyroskopisk stabilitet (`Sg`) for kule og pipekombinasjon.
- [x] Vise stabilitetsmargin som del av analyse og anbefalinger.
- [x] Lage grunnmodell for pipeharmonikk basert pa lopslengde, profil, masse og munningsutstyr.
- [x] Regne munningsutstyr som del av pipekonfigurasjonen:
  `type`, `vekt`, `lengde`, `monteringsstatus`.
- [x] Ta hensyn til brems, comp og lyddemper i harmonisk analyse og POI-shift.
- [ ] Lage modell for termisk tilstand:
  `kald pipe`, `varm pipe`, `ammo-temp`, `pipe-temp`, `skudd i streng`, `tid mellom skudd`.
- [x] Bruke termiske data i analyse av hastighet, samling og stabilitet.
- [ ] Lagre kronografmetode og malekontekst:
  type kronograf, avstand fra munning, sensoroppsett, eventuelt oppgitt maleusikkerhet.
- [ ] Behandle kronografdata med eksplisitt maleusikkerhet i stedet for som absolutte sannheter.
- [ ] Lage bedre analysemal enn bare gruppestorrelse nar det er mulig:
  `mean radius`, `POI-shift`, `vertikal spredning`, `horisontal spredning`.
- [ ] Spore POI-shift per pipekonfigurasjon og per munningsutstyr.
- [ ] Tilpasse fysikk- og analysemotor for pistol i tillegg til rifle.
- [ ] Legge inn pistolspesifikke data der relevant:
  funksjon, mating, utkast, faktor, rekylfjar-oppsett.
- [ ] Dokumentere hvilke modeller som er malte data, hvilke som er fysikkmodeller, og hvilke som er utledede anbefalinger.

## Start her

Dette er anbefalt forste arbeidsblokk:

- [x] Skrive inn at vapenprofil skal stotte bade rifle og pistol.
- [x] Skrive inn at ett vapen kan ha flere piper eller lop med eget kaliber og egne maledata.
- [x] Skrive inn at pipeprofil skal lagre munningsutstyr med vekt og lengde.
- [x] Skrive inn `Kalibrering i vapenprofil` i plan-dokumentet.
- [x] Lage databaseplan for kalibreringsdata.
- [ ] Lage databaseplan for vapen -> pipe- eller lopstruktur.
- [x] Lage oversikt over fysikkdata og modeller som skal inn i forste versjon.
- [x] Lage enkel UI-seksjon i vapenprofil.
- [x] Lage forste registreringsskjema for kalibreringsokt.
- [x] Lage enkel analysevisning.
