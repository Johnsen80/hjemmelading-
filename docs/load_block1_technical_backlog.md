# Blokk 1 Technical Backlog

## Status
- Oppdatert: 2026-04-10
- Gjelder: teknisk restliste for Blokk 1

## Formål

Dette dokumentet oversetter Blokk 1 fra produkt- og gjennomføringsplan til konkret kodearbeid.

Blokk 1 handler om én ting:

å gjøre `load_development_sessions` + runtime-laget til faktisk kanonisk sannhetskilde for aktiv ladeutvikling.

## Kjerneprinsipp

Når det finnes både:

- `workflow_context/*` i `QSettings`
- en rad i `load_development_sessions`

skal domenedata leses fra session/runtime, og `QSettings` skal kun brukes for navigasjon, fokus og gjenåpning.

## Høyeste prioritet

### 1. Standardiser én felles lesebane

Dette mønsteret skal bli standard i alle kjerneflater:

1. Les `workflow_context/load_session_id`
2. Hent runtime via `build_load_session_runtime(...)`
3. Les rifle/barrel/barrel_configuration fra runtime
4. Bruk `workflow_context` bare som fallback eller UI-fokus

Første moduler:

- `modern_load_builder.py`
- `batch_workspace.py`
- `chronograph_importer.py`
- `target_analyzer.py`
- `safety_dashboard.py`

### 2. Standardiser én felles skrivebane

Nye målinger og oppdateringer skal så langt mulig skrives tilbake med:

- `load_session_id`
- `rifle_id`
- `barrel_id`
- `barrel_name`
- `barrel_configuration_id`
- `barrel_configuration_name`

## Fil-for-fil backlog

## A. `src/tools/load_session_runtime_service.py`

Rolle:
skal være hovedinngang for normalized runtime payload.

Teknisk backlog:

- [ ] Verifisere at runtime-payload alltid inkluderer:
  - session identity
  - rifle context
  - barrel context
  - barrel configuration context
  - component selection
  - component lots
  - evidence summary
  - learning state
  - recommendation state
  - confidence/safety summary
- [ ] Dokumentere payload-shape tydelig i kode eller docs
- [ ] Sikre at payloaden er trygg å bruke som eneste lesekilde i UI
- [ ] Redusere behovet for at widgets henter de samme tingene på nytt via egne DB-spørringer

Første mål:
runtime-payloaden skal være komplett nok til at builder, batch, chrono og target kan bruke den direkte.

## B. `src/tools/load_development_session_service.py`

Rolle:
skal være eneste generelle service for create/get/update av canonical session.

Teknisk backlog:

- [ ] Verifisere at alle viktige runtime-felter kan oppdateres via `update_load_development_session(...)`
- [ ] Sikre at `component_selection_json`, `component_lots_json`, `evidence_summary_json` og `learning_state_json` brukes konsekvent
- [ ] Dokumentere hvilke felter som er canonical for session versus bare derived/runtime
- [ ] Rydde bort mønstre der UI-moduler skriver lignende tilstand andre steder i stedet for hit

Første mål:
alle session-oppdateringer i kjerneflyten skal kunne spores til denne tjenesten.

## C. `src/modules/smart_loading_wizard.py`

Nåværende rolle:
oppretter session og skriver `workflow_context`.

Teknisk backlog:

- [ ] Beholde wizard som inngang, men sikre at den kun oppretter/initialiserer session truth
- [ ] Verifisere at alle nødvendige felter skrives inn i `load_development_sessions` ved opprettelse
- [ ] Minimere avhengighet til legacy loading session i videre flyt
- [ ] Sørge for at `workflow_context` bare peker videre til canonical session
- [ ] Skrive eksplisitt `barrel_id`, `barrel_name` og session-relevant context til `workflow_context` der det mangler

Første mål:
wizard skal være en ren intake-front til canonical runtime, ikke starten på et parallelt spor.

## D. `src/modules/modern_load_builder.py`

Nåværende rolle:
sterkeste ekspertflate, men bærer fortsatt mye lokal state.

Teknisk backlog:

- [ ] Gjøre runtime service til primær lesekilde ved init/gjenåpning
- [ ] Kartlegge hvor lokal widget-state dupliserer canonical session state
- [ ] Flytte oppdatering av aktiv komponenttilstand til `update_load_development_session(...)` som standardbane
- [ ] Sørge for at `_sync_active_load_session_context()` er tydelig canonical sync, ikke bare “best effort”
- [ ] Innføre tydelig last/refresh-bane fra runtime når session endres utenfra
- [ ] Gjøre læringsvisning smartere med samme runtime som kilde:
  - vis datagrunnlag som chrono/test-count
  - prioriter trykkbekreftelse før videre optimalisering
  - skill jaktflyt fra konkurranseflyt i læringsguidance
  - gjør svakeste ledd og neste fokus mer forklarbart

Spesielt å se på:
- `_get_active_load_session_runtime()`
- `_get_cached_or_active_load_session_runtime()`
- `_build_active_load_session_component_selection()`
- `_build_active_load_session_intake_snapshot()`
- `_format_learning_runtime_label()`
- `build_learning_workflow_guidance(...)`
- `_sync_active_load_session_context()`

Første mål:
builder skal være runtime-drevet, ikke bare runtime-synkronisert på siden.

## E. `src/modules/batch_workspace.py`

Nåværende rolle:
oppfølging, evidens og batch-verifisering.

Teknisk backlog:

- [ ] Redusere lokal logikk som rekonstruerer aktiv kontekst fra `QSettings` alene
- [ ] Bruke `load_session_id` til å hente session truth når den finnes
- [ ] Sikre at batch-visning og batch-oppretting knytter seg tydelig til canonical load session
- [ ] Verifisere at batch-sessioner og notater beholder pipekonfigurasjon konsekvent
- [ ] Vurdere om `_get_active_workflow_context()` bør dele felles helper med andre moduler

Første mål:
batch workspace skal være oppfølgingsflate til aktiv load session, ikke et halvseparat spor.

## F. `src/modules/chronograph_importer.py`

Nåværende rolle:
bruker `workflow_context`, beriker fra DB, og lagrer chrono-session.

Teknisk backlog:

- [ ] Gjøre `load_session_id` til førstevalg når aktiv kontekst finnes
- [ ] Verifisere at `rifle_id`, `barrel_id` og `barrel_configuration_*` hentes fra session/runtime og ikke bare fra `QSettings`
- [ ] Standardisere hvordan chrono-import skriver tilbake til sessionrelatert evidens
- [ ] Redusere duplisert `_get_active_workflow_context()`-logikk hvis mulig

Første mål:
chrono-import skal ikke gjette hvilken session serien hører til når aktiv session allerede finnes.

## G. `src/modules/target_analyzer.py`

Nåværende rolle:
bruker `workflow_context`, beriker fra DB, og lagrer target-resultater.

Teknisk backlog:

- [ ] Gjøre `load_session_id` til hovednøkkel for aktiv sessionkontekst
- [ ] Sikre at rifle/barrel/barrel_configuration fylles fra canonical session når den finnes
- [ ] Standardisere target-resultat som session-evidens
- [ ] Redusere duplisert workflow-context-oppslag og gjøre fallback tydelig

Første mål:
target-analyse skal peke tilbake til samme aktive session som chrono og batch.

## H. `src/modules/safety_dashboard.py`

Nåværende rolle:
arbeider på aktiv workflow/load-session-kontekst for trykktegn.

Teknisk backlog:

- [ ] Sikre at pressure/primer evidence alltid knyttes til canonical load session når den er kjent
- [ ] Verifisere at pipekonfigurasjon ikke mistes
- [ ] Redusere lokal duplisering av workflow-context-oppslag hvis mulig

Første mål:
safety-evidens skal høre til samme læringssløyfe som chrono og target.

## I. `src/ui/main_window.py`

Nåværende rolle:
skallogikk og åpning av flater.

Teknisk backlog:

- [ ] Verifisere at hovedvinduet åpner builder/batch ut fra canonical active session når mulig
- [ ] Stramme inn routing så bruker ikke sendes til feil flate på grunn av stale `QSettings`
- [ ] Gjøre “aktiv session” tydeligere som begrep i shell-logikken

Første mål:
main window skal åpne riktig arbeidsflate basert på faktisk session truth.

## Gjenbruk som bør innføres

Det finnes nå flere moduler med nesten samme helper:

- `_get_active_workflow_context()` i `batch_workspace.py`
- `_get_active_workflow_context()` i `chronograph_importer.py`
- `_get_active_workflow_context()` i `target_analyzer.py`
- `_get_active_workflow_context()` i `safety_dashboard.py`

Teknisk backlog:

- [ ] Lage én delt helper eller service for aktiv UI-kontekst + canonical session enrichment
- [ ] Fjerne lokal kopiert logikk der det er mulig

Status 2026-04-10:

- første felles enrichment-helper er innført i `load_session_runtime_service.py`
- `modern_load_builder`, `batch_workspace`, `chronograph_importer`, `target_analyzer` og `safety_dashboard` bruker nå samme canonical enrichment-retning
- første measurement-sync er innført slik at chrono-, target- og batch-registrering kan skrive fersk måleoppsummering tilbake til aktiv `load_development_session`
- spredningslære v1 er koblet inn uten nye UI-felt:
  - skiller konservativt mellom `ammo_or_process_signal`, `possible_shooter_or_setup_signal`, `setup_drift_watch`, `environment_or_condition_signal`, `node_or_barrel_timing_signal`, `pressure_or_ammo` og `insufficient_evidence`
  - bruker eksisterende batch-, chrono-, target-/gruppe- og notatdata
  - tolker første sett norske og engelske notatord for trykk, skytter/serie, setup/utstyr og miljø
  - bruker eksisterende vertikal/horisontal samlingsdata når den finnes:
    - horisontal-dominant samling peker konservativt mot vind, mirage, støtte, kanting eller stilling
    - vertikal-dominant samling med stabil ES/SD peker mot kontroll av seating, pipetiming, tracking og siktepunkt før bred kruttendring
    - POI-drift mellom økter peker mot setup-/zero-/pipe-/forholdskontroll før ladningen forkastes
  - lar trykktegn vinne over presisjonsoptimalisering
  - sender spread-signal, begrunnelse, watchouts, notatflagg, mønsterflagg, POI-drift og vindkontekst videre til session evidence og learning summary
  - lar `modern_load_builder` bruke signalet til mer praktisk neste-steg-guidance
  - legger nå ved en strukturert kontrollplan per signal:
    - sikkerhets-/trykkkontroll
    - ammo-/prosesskontroll
    - kontrollert repeat-gruppe
    - setup-/zero-kontroll
    - kjent-miljø repeat
    - vertikal/pipetiming/seating-kontroll
    - innsamling av manglende paired evidence
  - kontrollplanen har prioritet, tittel, primærhandling, skuddplan, hva brukeren bør unngå og suksesskriterier
  - legger også ved decision gate per batchsignal:
    - `safety_stop`
    - `process_control_required`
    - `repeat_before_rejecting`
  - legger også ved en bruksmålsstyrt validation/readiness-status:
    - jakt kan markeres som `field_validation_pending` eller `cold_bore_confirmation_pending`
    - konkurranse kan markeres som `ranking_validation_pending`, `tuning_validation_pending` eller `cautious_ranking_candidate`
    - læring/hobby kan markeres som `collect_more_data` eller `learning_cycle_ready`
  - validation/readiness-statusen sendes videre til runtime, learning guidance, batch workspace og HTML-oppsummering slik at systemet tydelig kan si om batchen fortsatt bare er foreløpig
  - batch-workspace bygger nå også en konservativ sammenligningsbasis mellom søsterbatcher:
    - kombinerer gruppescore, evidenskvalitet og readiness
    - straffer tynne/provisoriske batcher og ikke-avklarte signaler
    - prøver å hindre at én heldig serie rangeres over bedre validert data
  - batch-workspace legger nå også ved et comparison advisory / promotion gate:
    - forklarer om batchen leder, leder men fortsatt er foreløpig, henger etter eller er blokkert
    - peker på hva som må bekreftes før batchen kan løftes over andre kandidater
  - comparison basis og promotion gate sendes nå også videre til canonical runtime og learning guidance slik at samme konservative rangeringstenkning kan brukes utenfor batch-workspace
  - comparison-laget har nå også en strukturert head-to-head / promotion-protokoll:
    - peker på hvordan to batcher faktisk skal skytes mot hverandre under matchede forhold
    - brukes nå i batch-workspace, runtime-delta og learning guidance
  - comparison-laget har nå også en eksplisitt forklaring på hva som holder batchen tilbake eller frem:
    - identifiserer sammenligningsflaskehals som sikkerhet, valideringsdybde, evidenskvalitet, feltvalidering eller årsaksseparasjon
    - peker på neste viktigste måling som vil gjøre sammenligningen mer sann
  - comparison-laget har nå også verdict + checklist:
    - systemet kan si om batchen ikke bør promotéres ennå, bør holdes som foreløpig leder, eller er kandidat for betinget promotering
    - comparison checklist peker på hva som må være likt og hva som må måles i neste sammenligningstest
  - comparison-laget har nå også en scorecard-visning:
    - peker på om batchen hovedsakelig taper på presisjon, evidenskvalitet eller readiness
    - brukes nå i batch-workspace, runtime-delta og learning guidance
  - comparison-laget har nå også confidence + learning note:
    - comparison confidence sier hvor robust sammenligningen er akkurat nå
    - comparison learning note forklarer hva brukeren faktisk bør lære av utfallet, ikke bare hvem som leder
  - comparison-laget har nå også en acceptance gate:
    - den sier hva som faktisk må være sant før en batch får lov til å overta som jakt-, konkurranse- eller læringskandidat
    - den peker også på gjenstående gap og neste gate før promotering
  - comparison acceptance har nå også progress:
    - score, nivå og antall oppfylte betingelser gjør det lettere å se hvor nær batchen er reell overtakelse
  - comparison-laget har nå også et status board + next test brief:
  - comparison-laget har nå også campaign board + session queue + session manifest:
    - batcher prioriteres nå som shoot_now, confirm, hold, pause eller reject_watch
    - systemet kan dermed samle neste skyteøkt som en konkret manifest med første batch, primærbøtte og styrende handling
  - comparison-laget har nå også next session brief + today plan:
    - systemet kan si hva som skal skytes først, hva som må verifiseres først og hva som bevisst skal holdes tilbake i neste økt
    - dette brukes nå som mer direkte operativ anbefaling i runtime og learning guidance
    - status board samler leder, readiness-band, verdict og progress i én kort oppsummering
    - next test brief sier hvilken sammenligningstest som faktisk bør skytes nå
  - comparison-laget har nå også profile priority + mission brief:
    - jakt, konkurranse og læring får hver sin guardrail og suksessmarkør for neste økt
    - mission brief gjør neste sammenligning mer som en konkret oppgave enn en løs anbefaling
  - comparison-laget har nå også portfolio + session strategy:
    - portfolio viser hvilken kandidatportefølje som faktisk konkurrerer og hva hele settet bør fokusere på
    - session strategy sier hvilken type økt neste test faktisk skal være
  - comparison-laget har nå også campaign view + action plan:
    - campaign view samler leder, readiness-band, session-mode og hovedmål i ett toppnivåbilde
    - action plan peker på hva som faktisk skal gjøres først i neste runde
    - `setup_control_required`
    - `condition_control_required`
    - `focused_tuning_after_repeat`
    - `collect_matched_evidence`
    - `ready_for_cautious_optimization`
  - decision gate styrer om systemet foreløpig bør tillate optimalisering, avvise ladningen, akseptere ladningen eller kreve kontrollserie først
  - bruksmål er koblet inn i samme signal:
    - jakt får sikkerhets-, kaldskudds-, feltstøtte- og human field-reliability-fokus
    - konkurranse får repeterbarhet, ES/SD, setup-separasjon, lot-/prosesskontroll og rangering først etter kontrollserier
    - læring/hobby får pedagogisk språk, små tester og én-variabel-om-gangen
  - profile guidance sendes videre sammen med spread signal, kontrollplan og decision gate
  - evidence quality er lagt til som eget maskinlesbart lag:
    - score 0-100
    - nivå: `very_thin`, `thin`, `moderate`, `strong`
    - styrker i datagrunnlaget
    - begrensninger i datagrunnlaget
    - manglende data
    - anbefalt logging for neste tur
  - evidence quality bruker eksisterende chrono-count, gruppe-count, paired chrono/group, target-pattern, notater, vind og bildevedlegg
  - læringsforklaring er lagt til som eget maskinlesbart lag:
    - tittel
    - enkel oppsummering
    - årsakskjede
    - hva brukeren bør følge med på neste gang
    - brukerrettet takeaway
    - kompleksitetsnivå basert på jakt, konkurranse, læring/hobby eller generell bruk
  - læringsforklaringen sendes videre til runtime, builder-guidance og batch evidence basis
  - neste-capture-checklist er lagt til som eget maskinlesbart lag:
    - hva brukeren bør logge neste gang
    - hvorfor akkurat dette datapunktet hjelper
    - prioritert etter signal, datakvalitet og bruksmål
  - checklisten tilpasses jakt, konkurranse og læring/hobby:
    - jakt: kaldskudd, feltstøtte, vind-/forholdsnotat
    - konkurranse: same-setup repeat, prosesskontroll, smale bracket-tester
    - læring/hobby: én variabel, korte notater, liten matched serie
- neste steg er å la flere skrivebaner oppdatere samme session truth like konsekvent som lesebanene

Første mål:
samme type oppslag skal ikke implementeres fire ganger med litt forskjellig oppførsel.

## Testbacklog

### Kritiske tester som bør lages eller styrkes først

- [ ] wizard oppretter canonical session med riktig rifle/barrel/barrel_configuration
- [ ] builder leser aktiv session fra runtime og ikke bare fra widget-state
- [ ] chrono import lagrer mot riktig `load_session_id`
- [ ] target analyzer lagrer mot riktig `load_session_id`
- [ ] batch workspace arver og viser riktig pipekonfigurasjon fra aktiv session
- [ ] samme aktive session overlever overgang:
  wizard -> builder -> batch -> chrono -> target

## Foreslått rekkefølge for kodearbeidet

1. `load_session_runtime_service.py`
2. `load_development_session_service.py`
3. `modern_load_builder.py`
4. `smart_loading_wizard.py`
5. felles helper for aktiv workflow/session context
6. `chronograph_importer.py`
7. `target_analyzer.py`
8. `batch_workspace.py`
9. `safety_dashboard.py`
10. `main_window.py`

## Hva som er ferdig nok i Blokk 1

Blokk 1 er teknisk langt nok når:

- minst én shared helper/runtime-bane brukes av flere kjerneflater
- builder er tydelig runtime-drevet
- chrono og target lagrer session-knyttet evidens konsekvent
- batch og safety mister ikke pipekonfigurasjon på veien
- testene viser at samme aktive session flyter gjennom kjernebanen uten at kontekst må rekonstrueres manuelt
