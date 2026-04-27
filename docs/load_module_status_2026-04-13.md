# Lade-modul: Statussnaphot 2026-04-13

## Hensikt

Dette dokumentet er et datert statussnaphot av lade-modulens ferdigstillelse.
Det svarer på: «hva har vi igjen før vi har et ferdig lade-modul som er robust og funker i praksis opp mot teorien?»

Det er et supplement til `load_module_finish_todo.md` — det dokumentet definerer HVA som skal gjøres,
dette dokumentet sier HVOR VI ER per 2026-04-13.

Oppdater dette dokumentet ved neste statusgjennomgang, ikke ved hvert enkelt commit.

---

## Overordnet ferdigstillelse

| Aspekt                              | Ferdig | Risiko   |
|-------------------------------------|--------|----------|
| Kjerne-fysikk (trykk, seating, harmonics) | 90 %  | Lav      |
| Canonical runtime (én sannhetskilde)      | 75 %  | Høy      |
| Engine input (komplett kontekst)          | 70 %  | Høy      |
| Evidens-kvalitet (standardisert)          | 65 %  | Høy      |
| Læringsløkke (aktivert og lukket)         | 55 %  | Høy      |
| Anbefaling-robusthet                      | 75 %  | Middels  |
| Duplikat-logikk ryddet bort               | 50 %  | Middels  |
| Defensiv input-håndtering                 | 20 %  | Kritisk  |
| End-to-end validert arbeidsflyt           | 40 %  | Høy      |

**Samlet: ~60–65 % mot produksjonsklar**

### Oppdatering 2026-04-13 (dagens økt)

**Fullført:**
- Ruff-rensking av `src/` (alle sjekker passerer)
- Kanoniske signal-hint normalisert (`ammo_signal` → `ammo_or_process_signal`, `setup_signal` → `possible_shooter_or_setup_signal`)
- Læringsløkke-determinisme: `recompute_batch_analysis_from_db` kjøres headless fra chrono-importer og target-analyzer
- Shot-count robusthet: 3-skudd gruppe capper til "moderate" evidens selv ved lav mm-verdi; `small_sample_group` eksponert i `candidate_profile`
- Validerings-gates håndhevet: `insufficient_evidence` og `pressure_or_ammo` signal-hint blokkerer `candidate_ranking` og setter `robustness_level` til "low"
- `batch_analyzer` konsumerer engine-output: per-session `signal_hint` (fra `load_development_sessions.evidence_summary_json`) aggregeres til batch-signal; mest blokkerende vinner
- End-to-end CI-test skrevet og passererer (3 tester, 16 s): session → builder → chrono → target → gjenåpne → engine-output

**Gjenstår fra planen:**
- Blokk 4 (rest): Charge-window-læring — persister lærte grenser i `learning_state_json`
- Blokk 4 (rest): Lot-drift-minne for krutt/kule/primer i `learning_state_json`

---

## Status per blokk (ref. load_module_finish_todo.md)

### Blokk 1: Canonical Truth Path

**Status: ~70 % fullført**

Hva som er på plass:
- `load_development_sessions` + runtime service (`load_session_runtime_service.py`) er etablert og fungerer
- Session-opprettelse via `load_development_session_service.py` fungerer
- De fleste moduler leser fra runtime i normalflyt

Hva som gjenstår:
- `modern_load_builder.py` (20 000+ linjer) blander widget-state og runtime — ingen garantert prioritering
- `batch_workspace.py` rekonstruerer kontekst fra QSettings fremfor eksplisitt session-kobling
- `chronograph_importer.py` og `target_analyzer.py` har ad hoc session-oppslag som fallback
- Resume-bane etter lukking og gjenåpning mister noen ganger barrel_configuration_id
- Barrel configuration vises ikke konsekvent i alle kritiske anbefalingsflater

Blokkerer: Ja — alt som bygger på feil kontekst gir feil råd.

---

### Blokk 2: Engine Input Completion

**Status: ~70 % fullført**

Hva som er på plass:
- Smart engine kan bygge input fra runtime i normalflyt
- Komponent- og lot-kontekst delvis løst fra session

Hva som gjenstår:
- Komponent-kontekst (kule, krutt, tennhette, hylse) løses ikke alltid fra kanonisk session
- Lot-kontekst mangler tolerant fallback ved delvis valg
- Miljøkontekst (temperatur, tetthetsaltitude) hentes noen ganger fra UI-state fremfor persistent session
- Målt evidens (kronograf, skive, batch, trykk) kobles ikke alltid til setup-identitet
- Eldre rader uten eksplisitt barrel_configuration_id nedgraderes ikke konsekvent

Blokkerer: Ja — engine evaluerer av og til feil kontekst uten å varsle om det.

---

### Blokk 3: Evidence Weighting og Scientific Core

**Status: ~50 % fullført**

Hva som er på plass:
- 7-kategori spread-signal klassifisering (ammo, skytter, oppsett, miljø, timing, trykk, utilstrekkelig)
- Per-signal kontrollplaner med prioriteter
- Validerings-gates per batch-signal
- Evidens-kvalitets-scoring (0–100 med nivåer: very_thin / thin / moderate / strong)
- Konfidensmerking (low / medium / high trust)

Hva som gjenstår:
- Evidens-kvalitets-logikken er **ikke gjenbrukt** på tvers av builder, workflow, runtime og engine — fire parallelle implementasjoner
- Matched vs unmatched evidens-scoring finnes bare i batch_analyzer
- Cold-bore evidens er ikke first-class målingskanal
- Gruppe-mønster konfidensblanding er ufullstendig
- «Utilstrekkelig evidens» håndheves ikke konsekvent (forced diagnosis vinner)
- `measured` / `modeled` / `derived` / `recommended` er definert i digital_twin men ikke unified

Blokkerer: Ja — systemet kan se mer sikkert ut enn datagrunnlaget tilsier.

---

### Blokk 4: Local Learning Core

**Status: ~40 % fullført**

Hva som er på plass:
- Barrel-lærings-profiler med harmonics-score, kronograf-samples og skive-samples
- Hylse-lærings-profiler for gjenbrukssporing
- Jump-målinger spores per rifle/barrel
- Learning state JSON-skjema (v1) med barrel- og hylsekontekst

Hva som gjenstår:
- Charge-window-læring er ikke formalisert (anbefalte vindu finnes, men ikke lærte grenser)
- Seating-window-læring er ikke atskilt fra generelle anbefalinger
- Lot-drift-minne for kule/krutt/tennhette/hylse er ikke strukturert
- Confirmed-candidate-minne eksisterer ikke
- Rejected-candidate-minne persisteres ikke
- Model-status (`raw` / `partially_calibrated` / `well_calibrated`) brukes ikke konsekvent
- Kronograf/skive/batch-oppdateringer er ikke deterministisk koblet til læringstilstand

Blokkerer: Ja — systemet «glemmer» mellom øktene.

---

### Blokk 5: Recommendation og Robustness

**Status: ~75 % fullført**

Hva som er på plass:
- Kandidatrangering med robusthetsvekting
- «Ikke endre ennå»-validerings-gates
- Grunnleggende neste-steg-forslag per signaltype
- Sikkerhets- og evidens-blokkerer-rammeverk
- Baseline anbefaling (charge_gr, coal_mm, cbto_mm)
- **Ny:** Shot-count cap — 3-skudd gruppe ≤ "moderate" selv ved lav mm; `small_sample_group` i `candidate_profile`
- **Ny:** Validerings-gates håndhevet: `insufficient_evidence` og `pressure_or_ammo` blokkerer `candidate_ranking` og setter `robustness_level` til "low"

Hva som gjenstår:
- «Beste neste test»-rekkefølge er ikke fullstendig for jakt/konkurranse/lærings-formål
- Aktiv oppsett og konfidensgrunnlag eksponeres ikke alltid i anbefalings-payloads

Blokkerer: Nei lenger for shot-count og gate-problemer. Jakt/konkurranse neste-steg er fortsatt pending.

---

### Blokk 6: Consumer Migration og Deduplication

**Status: ~50 % fullført**

Hva som er på plass:
- smart_ammo_engine.py er etablert som kanonisk motor
- **Ny:** `batch_analyzer` konsumerer per-session engine signal_hint (via `_aggregate_session_hints`); raw-data-beregning brukes bare som fallback
- **Ny:** `recompute_batch_analysis_from_db` beriker sessions med `_signal_hint` fra `load_development_sessions`

Hva som gjenstår:
- `modern_load_builder.py` dupliserer veiledning og neste-steg-logikk
- `digital_twin.py`, builder, runtime og workspace har uavhengig baseline-assembly
- Ingen integrasjonstest verifiserer at de produserer aligned output

Blokkerer: Redusert. batch_analyzer er nå koblet mot engine; builder og twin er fortsatt uavhengige.

---

### Blokk 7: End-to-End Hardening og Sale-Readiness

**Status: ~40 % fullført**

Hva som er på plass:
- Noen unit-tester for runtime, engine og session service
- Headless smoke-test for oppstart
- **Ny:** E2E-test for kjerne-kommersiell flyt: session → chrono → target → gjenåpne → engine-kontekst + evidens + signal_hint (`tests/test_load_module_e2e_core_workflow.py`, 3 tester, alle grønne)

Hva som gjenstår:
- `digital_twin.py` har 50+ Pylance-feil (`.get()` på `None`, `int | None` til numpy, `None` subscriptable)
- Engine og runtime er ikke tolerante overfor manglende felt — stille fallback til feil modell
- Gammel UI-state kan overstyre nyere reell evidens
- Ingen regresjonstester for ødelagte/delvise inputs
- Ingen release-readiness-sjekkliste for lade-modulen

Blokkerer: Redusert — kjerne-flyt er nå maskinvalidert.

---

## Kjente tekniske gjeld (ikke blokk-spesifikke)

### Pylance / type-sikkerhet i digital_twin.py

50+ feil av disse typene:
- `"get" is not a known attribute of "None"` — linje 89, 90, 202, 203, 247–252, 319, 327, 400–471, 524, 529, 542, 543, 553, 558
- `int | None` til numpy ConvertibleToInt — linje 131, 132, 133
- `float | None` til numpy ConvertibleToFloat — linje 134, 135
- `len()` på `None` — linje 531, 560, 574
- `None` subscriptable — linje 532, 533, 561, 562, 576

Root cause: metoder bruker `Dict[str, Any]` og kaller `.get()` uten å sjekke at resultatet ikke er `None` før neste kall.

### Det som fungerer i dag (praktisk bruk)

- Wizard kan kjøres for å opprette en session
- Builder kan åpne og redigere ladeparametere
- Kronograf-data kan importeres
- Målgrupper kan analyseres (grunnleggende mønstergjenkjenning)
- Batch kan logges og merkes for sammenligning
- Trykk-vurdering fungerer ved komplett data

### Det som bryter uten eksplisitt kontekst

- Gjenåpning etter lukking (kontekst kan gå tapt)
- Bytte mellom builder og batch workspace (state-drift)
- Import av kronograf mens aktiv session er uklar
- Læringsoppsummering når det finnes flere sessions
- Sammenligning av anbefalinger fra ulike moduler (de er i konflikt)

---

## Anbefalt rekkefølge for neste arbeid

Følg blokk-rekkefølgen i `load_module_finish_todo.md`. Ingen omrokkering uten eksplisitt beslutning.

Neste konkrete steg (i prioritert rekkefølge):

1. **Fiks Pylance-feil i digital_twin.py** — lavest risiko, høy symbolsk verdi som første steg mot defensiv input
2. **Tving canonical truth path i modern_load_builder.py** — les kun fra runtime ved init, ingen widget-state-prioritering
3. **Ekstraher felles evidens-service** — én implementasjon av quality score / confidence / spread-signal
4. **Lukk læringsløkken** — kronograf/skive/batch → læringstilstand deterministisk
5. **End-to-end CI-test** — én test som kjører hele flyten uten manuell intervensjon

---

## Referanser

- `docs/load_module_finish_todo.md` — operativ sjekkliste (hva som skal gjøres)
- `docs/load_block1_technical_backlog.md` — fil-for-fil backlog for Blokk 1
- `docs/load_module_blueprint.md` — låst intent: ett cockpit, ikke mange verktøy
- `docs/load_engine_gap_analysis.md` — fragmenteringsanalyse
- `docs/project_todo.md` — prosjektretning og prioriteringsrekkefølge
- `docs/load_product_roadmap.md` — produktroadmap og prioritering
