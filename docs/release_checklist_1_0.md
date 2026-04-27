# Release Checklist 1.0

Dette er den operative sjekklisten for å kunne kalle prosjektet en ryddig 1.0.

## Produkt og flyt

- [ ] Verifiser at hovedinngangene faktisk dekker ønsket 1.0-flyt:
  `Ladeutvikling`, `Prosjekter`, `Ballistikk`, `Lager og batcher`, `Våpenprofiler`, `Lab og testing`, `Innstillinger`
- [ ] Sørg for at eldre `All Tools`/legacy-faner ikke fremstår som anbefalt startpunkt
- [ ] Gå gjennom tomtilstander, feilmeldinger og popup-er i kjerneflytene
- [ ] Bekreft at kaliberlås fungerer i sentrale flyter for våpen, ammo, batch og tester

## Data og faglig tydelighet

- [ ] Verifiser at `Målt`, `Modellert` og `Anbefalt` vises konsekvent i sentrale analyseflater
- [ ] Verifiser at `confidence`, `uncertainty` og `evidenskvalitet` vises konsistent der de skal
- [ ] Gå gjennom safety/disclaimer-tekster før 1.0
- [ ] Bekreft at Ammo Test Lab, lot-læring og kjøpsbeslutning har tydelig kontekst og ikke lover mer enn dataene støtter

## Units og språk

- [ ] Kjør siste restpass på `units` i eldre input-/analysemoduler
- [ ] Kjør siste restpass på `i18n` i nisje-/legacy-dialoger
- [ ] Bekreft at global units faktisk slår gjennom i sentrale visninger og inputfelt
- [ ] Bekreft at språkbytte ikke ødelegger lagrede stabile verdier i combo-/valgfelter

## Import, eksport og rapport

- [ ] Verifiser schema/meta på sentrale eksportbaner
- [ ] Test PDF-rapport for Ammo Test Lab manuelt
- [ ] Verifiser at import/eksport fortsatt tåler eldre datafiler der det er lovet bakoverkompatibilitet

## Testing og release

- [x] Kjør `ruff check src tests`
- [x] Kjør hele moderne testsuiten
- [x] Kjør headless smoke/startup-test
- [ ] Kjør manuell røyk-test av 5-10 viktigste arbeidsflyter
- [ ] Verifiser at appen starter uten uventede legacy-vinduer eller stray widgets

## Verifisert nå

- [x] Bred moderne verifisering kjørt grønn: `100 passed`
- [x] Scientific Core konsistens-test lagt inn og kjørt grønn
- [x] Database-migrering for `bc_segments_json` verifisert mot eldre schema
- [x] Headless smoke er grønn for app-init, settings-dialog og font-/matplotlib-spor
- [x] Offscreen-instansiering av `MainWindow` er verifisert grønn via `instantiate_mainwindow_probe.py`

## Foreslått manuell røyk-test

1. Opprett/åpne våpenprofil og aktiv pipe/løp
2. Start ny ladeutvikling med riktig kaliberkontekst
3. Opprett eller åpne batch
4. Importer chrono-data
5. Kjør target-analyse
6. Verifiser readiness, robusthet og neste test
7. Åpne Ammo Test Lab og sammenlign lotter
8. Eksporter valgt rapport/PDF
9. Bytt språk og enhetssystem
10. Bekreft at hovedflyten fortsatt ser riktig ut
