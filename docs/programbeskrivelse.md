# Programbeskrivelse

## Kort beskrivelse

Hjemmelading er et offline-first desktopprogram for ladeutvikling, komponentstyring, måleanalyse og ballistisk planlegging. Programmet er laget for skyttere, hjemmeladere og fagmiljøer som vil bygge opp en mer presis og sporbar forståelse av hvordan våpen, pipe, hylser, kuler, krutt, tennhetter og lotter faktisk oppfører seg sammen.

Målet er ikke bare å lagre data, men å hjelpe brukeren å utvikle bedre ladninger basert på målinger, historikk, simulering og praktisk testresultat. Programmet skal etter hvert fungere som en lærende arbeidsflate per våpen og pipe, der mer data gir bedre vurderinger.

## Hva programmet skal være

- En samlet arbeidsflate for ladeutvikling fra første komponentvalg til verifisert ladning.
- Et system som lærer av den konkrete riflen, pipen og komponentkombinasjonen.
- Et analyseverktøy som skiller tydelig mellom målte data, avledede data, antakelser og simuleringer.
- Et visuelt og faglig sterkt verktøy for å forstå hva som påvirker trykk, hastighet, presisjon og konsistens.
- Et robust prosjektverktøy for historikk, batcher, eksport, dokumentasjon og senere produksjonsnær kvalitetssikring.

## Hvem programmet er for

- Hjemmeladere som vil bygge trygge og presise ladninger.
- Konkurranseskyttere som trenger systematisk testing av SD, ES, samling og temperaturfølsomhet.
- Jegere som vil tilpasse ladning til vilt, avstand, kuleoppførsel og faktisk våpen.
- Fagmiljøer og småskala produksjon som trenger sporbarhet, lotkontroll og dokumentasjon.

## Funksjonsbeskrivelse

### 1. Våpen- og pipeprofiler

Programmet lagrer våpenprofiler med kaliber, pipeinformasjon, twist, lengde, magasinkapasitet og annen relevant geometri. Det gjør det mulig å knytte all videre ladeutvikling til riktig våpen og riktig pipe, ikke bare til kaliber.

Dette er viktig fordi samme patron kan oppføre seg forskjellig i to ulike våpen. Programmet skal derfor bruke pipe og kammer som en aktiv del av vurderingen, ikke som passiv metadata.

### 2. Ladeutvikling

Ladeutviklingsmodulen er kjernen i programmet. Her velger brukeren kule, krutt, tennhette og hylse, og ser hvordan kombinasjonen oppfører seg mot aktiv rifle og pipe.

Modulen er bygget for å støtte:

- valg av komponenter og lotter
- seating depth og jump/CBTO/COAL
- vurdering av trykkmargin og fyllingsgrad
- kronografdata, samlingsdata og testresultater
- anbefalt neste steg i utviklingen
- senere læring per pipe og komponentkombinasjon

Retningen er at denne modulen skal bli en samlet ladecockpit der brukeren ser både simulert og målt grunnlag i samme flate.

### 3. Komponentdatabase

Programmet har støtte for referansedata og egne komponentdata for:

- kuler
- krutt
- tennhetter
- hylser

Komponentdatabasen skal brukes som arbeidsgrunnlag, ikke bare som statisk oppslagsverk. Det betyr at komponentdata kan kombineres med egne målinger, lotinformasjon og historiske resultater.

### 4. Lotstyring og læring per lot

Lotter kan registreres og spores for kule, krutt, tennhette og hylse. Dette gjør det mulig å se når en ny lot gir endring i hastighet, ES, SD, presisjon eller trykktegn.

På sikt er dette en av de viktigste forskjellene i programmet: systemet skal ikke bare vite hvilket krutt eller hvilken kule du bruker, men hvilken lot som faktisk ga resultatet.

### 5. Hylse- og kasselogikk

Programmet lagrer hylsedata som antall omladinger, trimlengde, H2O-kapasitet, vekt, målinger og annen læring knyttet til hylsetype og bruk.

Tanken er at hylsene skal fungere som sensordata fra kammeret. Når brukeren registrerer reelle målinger over tid, får programmet et bedre grunnlag for å tolke volum, variasjon, slitasje og konsekvensene dette har for ladningen.

### 6. Kronograf og måleanalyse

Kronografimport og måleanalyse brukes for å verifisere hvordan ladningen faktisk oppfører seg. Programmet kan koble målt hastighet til ladning, våpen, pipe, komponenter, lotter og testøkt.

Dette brukes til å:

- beregne ES, SD og gjennomsnitt
- oppdage avvik mellom simulert og målt resultat
- bygge historikk per våpen og pipe
- forbedre senere anbefalinger og simuleringer

### 7. Samlingsdata og testserier

Programmet støtter strukturert testing som ladder, seating-depth-serier og andre testforløp. Testresultater kan lagres med gruppestørrelse, kommentarer, bilder og tilhørende ladespesifikasjon.

Målet er at programmet skal kunne rangere hvilke kombinasjoner som faktisk fungerer best i det aktuelle våpenet, ikke bare hvilke som ser bra ut på papiret.

### 8. Ballistikk og simulering

Programmet inneholder ballistiske og internballistiske beregninger som brukes til å anslå blant annet hastighet, trykktrender, fyllingsgrad og praktiske konsekvenser av ladningsendringer.

Disse beregningene skal alltid forstås som beslutningsstøtte. Programmet skal derfor vise tydelig hvilket grunnlag som er målt, modellert eller antatt.

### 9. Batch, produksjon og sporbarhet

Når en ladning er klar for praktisk bruk, kan den knyttes til batcher og produksjonsarbeid. Dette gjør det mulig å spore hvilke komponenter, lotter og innstillinger som ble brukt i en bestemt serie.

Dette er nyttig både for hjemmebruk og for mer systematisk kvalitetssikring.

### 10. Historikk, eksport og rapportering

Programmet skal gjøre det lett å gå tilbake og forstå hva som ble gjort, hvorfor det ble gjort, og hva resultatet ble. Data kan brukes til historikk, sammenligning, rapporter og senere PDF-/eksportflyt.

Historikkdelen er viktig fordi ladeutvikling er kumulativ. Verdien i systemet øker jo mer brukeren faktisk registrerer og verifiserer.

### 11. Analysehjelp og beslutningsstøtte

Programmet har også retning mot analysehjelp som kan forklare hva som påvirker resultatet og peke ut neste gode teststeg.

Dette skal ikke erstatte fagkunnskap, men gjøre det enklere å:

- se hvilke data som mangler
- forstå hvilke variabler som trekker opp eller ned tilliten
- se hva som sannsynligvis påvirket resultatet
- velge neste test med høyest verdi

## Hva som gjør programmet unikt

- Det er bygget rundt reelt våpen, reell pipe og reelle komponentlotter.
- Det skal lære av brukerens egne målinger over tid.
- Det skal vise årsak og virkning når brukeren justerer komponenter eller seating.
- Det kombinerer lager, målinger, testhistorikk og simulering i samme arbeidsflate.
- Det er designet som et verktøy for utvikling og forståelse, ikke bare registrering.

## Arbeidsmåte i programmet

Den anbefalte arbeidsflyten er:

1. Velg rifle og aktiv pipe.
2. Velg eller registrer riktig hylse-/brass-grunnlag.
3. Velg kule, krutt, tennhette og lotter.
4. Bygg og vurder ladningen i ladeutviklingsflaten.
5. Test med kronograf og samlingsdata.
6. Bruk målt resultat til å forbedre neste steg.
7. Lås inn gode kombinasjoner som batch- eller produksjonsgrunnlag.

## Viktig avgrensning

Programmet gir beregninger, vurderinger og beslutningsstøtte, men erstatter ikke publiserte ladedata, sikker praksis eller faglig ansvar. All lading og skyting skjer på brukerens eget ansvar og må alltid verifiseres mot trygge og dokumenterte kilder.
