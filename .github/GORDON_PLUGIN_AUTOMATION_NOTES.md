# Gordon Plugin Automation Notes

Dette er et kort notat om hvorfor plugin/API-sporet nå ser ut som en realistisk neste vei videre.

## Bekreftede funn

- Gordon dokumenterer en lokal plugin-API via IPC/socket i:
  - `doku/en/doku/plugin-api.txt`
- Plugin start skjer med kommandolinjeparametre som:
  - `--ipcport <port>`
  - `--ipcfile <filepath>`
- Gordon sender JSON-pakker over IPC.
- Dokumenterte kommandoer inkluderer blant annet:
  - `Get_Tab`
  - `Get_TabList`
  - `Get_TabOnTop`
  - `Get_TabResults`
  - `Get_Chunk`
  - `Close_ChunkStream`

## Hvorfor dette er interessant

- Dette er en offisiell, dokumentert integrasjonsvei.
- Den krever ikke intern hacking av den krypterte `.db`-fila.
- Den kan potensielt brukes til å:
  - lese åpne tabs og resultater
  - eksportere simulerings-/resultatdata systematisk
  - bygge vår egen bro fra Gordon til vårt eget system

## Begrensning akkurat nå

- Dokumentasjonen vi har bekreftet handler tydelig om tab-/resultatdata og plugin-integrasjon.
- Vi har foreløpig **ikke** funnet dokumenterte plugin-kommandoer som lister hele projectile-/propellant-/caliber-databasen direkte.
- Derfor er plugin-API foreløpig mest lovende for:
  - automatisert uttrekk av aktive load-/resultatdata
  - mulig fremtidig UI-styrt eksport sammen med et hjelpeplugin

## Realistiske neste steg

1. Lese de dokumenterte `plugin-api-cmd-*`-sidene lokalt og kartlegge eksakt hva som kan hentes.
2. Lage et lite testplugin som kun logger IPC-tilkobling og mottatte events.
3. Se om plugin-kommandoene kan hente mer enn tab/resultatdata.
4. Hvis ikke:
   - kombinere plugin-sporet med UI-eksport av projectile/propellant/caliber
   - og la vår ingest-pipeline ta imot outputen

## Konklusjon

Plugin/API-sporet ser nå ut som den mest presise og minst spekulative automatiseringsveien ved siden av XML-eksportene. Det er fortsatt ikke bevist at det gir full database-eksport, men det er en mye sterkere neste retning enn blind DB-forensics alene.
