# PM: Web Interaction Runtime (WIR) — stegvis utveckling enligt Lean och 5S

**Datum:** 2026-11-03  
**Status:** Förslag för granskning, ej implementeringsbeslut  
**Omfattning:** JAR-NILS, EYES, WEB, HANDS, AgentLoop, TaskContract, ScopePolicy, minne och framtida lokala modeller  
**Grundprincip:** Återanvänd före utbyggnad. Mät före optimering. Verifiera före aktivering.

## 1. Syfte och avgränsning

JAR-NILS ska kunna läsa, förstå och, efter uttryckligt godkännande inom rätt behörighetsgränser, interagera med webbplatser och webbapplikationer. Målet är ett tunt **Web Interaction Runtime (WIR)**, inte en parallell agentstack. WIR ska kunna välja mellan godkänd API-integration, strukturell webbläsarstyrning (DOM/tillgänglighetsträd) och visuell interaktion (EYES + HANDS).

WIR är ett *föreslaget* namn och en *föreslagen* komponent. Det finns ingen verifierad implementation i detta PM. Befintliga komponenters faktiska API:er, teststatus och kopplingar måste inventeras på aktuell kodrevision innan implementation.

**Icke-mål i första versionen:** obegränsad autonomi, automatisk kringgång av inloggning eller CAPTCHA, hemlig bakgrundsaktivitet, självmodifierande policyer, godtyckliga externa skrivoperationer, automatisk aktivering av destillerade färdigheter.

## 2. Lean och 5S gäller även hur vi bygger

Lean innebär här att optimera **verifierat värde per kostnad och risk**, inte att minimera kodrader på bekostnad av begriplighet eller säkerhet. 5S används både på runtime och i utvecklingsprocessen:

| 5S | Utvecklingsarbete | Runtime |
| --- | --- | --- |
| **Sortera** | Inventera och klassificera befintliga moduler, beroenden, tester och dokument. Ta inte bort något utan verifierad användningsanalys. | Filtrera bort irrelevanta DOM-noder, skärmbilder och observationer utan att tappa nödvändig evidens. |
| **Systematisera** | En tydlig ägare per ansvar; stabila kontrakt; namngivning och återanvändbara testfixturer. | Normaliserade elementreferenser, action/result-kontrakt och avgränsade sessioner. |
| **Städa** | Eliminera duplicerade adaptrar, överflödiga modellrop, döda grenar och inaktuella artefakter först efter test. | Rensa utgångna sessionstillstånd, cacheposter och temporär data med spårbar retention. |
| **Standardisera** | Gemensam Definition of Done, testmatris, kodgranskning, mätning och dokumentationsmall. | Gemensamma felkoder, policykontroller, verifiering, återhämtning och auditlogg. |
| **Skapa vana** | Kontinuerlig förbättring vid varje slice, regressionskontroll och återkommande uppföljning av slöseri. | Mät drift, upptäck regressioner, invalidera gamla procedurer och förbättra endast efter evidens. |

**Regel per ändring:** Beskriv problem → befintlig lösning → föreslagen minsta ändring → risk → test → mätvärde → rollback. Om en enklare återanvändning räcker ska ingen ny abstraktion införas.

**Kodradnivå:** Granska onödiga kopior, allokeringar, serialiseringar, kontextöverföringar, modellrop, upprepade observationer, synkrona väntetider och cachemissar där de faktiskt har betydelse. Ingen mekanisk mikrooptimering utan profileringsstöd. Säkerhet, determinism och läsbarhet är hårda krav.

## 3. Arkitektur och ansvar

```text
JAR-NILS Core / TaskContract
          |
      ScopePolicy
          |
   WIR (tunn orkestrering)
      /      |       \
 API/WEB   DOM/CDP   EYES
      \      |       /
      BrowserAdapter
          |
 HANDS (endast tillåtna handlingar)
          |
 Resultat + evidens + AgentLoop-verifiering
          |
 Befintligt minneslager / godkänd procedurdestillering
```

- **Core** definierar mål och beslut som kräver högre resonemang.
- **TaskContract** begränsar uppgift, ursprung, operationer, tid och steg.
- **ScopePolicy** är obligatorisk kontrollpunkt före varje effektfull handling.
- **WIR** väljer metod, hanterar webbtillstånd och rapporterar; ingen egen obegränsad beslutsauktoritet.
- **WEB** använder godkända API:er och befintlig webbfunktionalitet där lämpligt.
- **BrowserAdapter** sköter webbläsarsession, DOM, tillgänglighetsträd och navigation.
- **EYES** tolkar visuellt gränssnitt vid behov.
- **HANDS** utför enbart explicit tillåtna interaktioner; befintliga låsningar kringgås aldrig.
- **AgentLoop** verifierar målutfall, hanterar begränsade omförsök och avbryter vid osäkerhet.
- **Minne/destillering** sparar endast godkända, versionsbundna och spårbara procedurer.

API först **när en dokumenterad, behörig integration finns**; annars stabil DOM/tillgänglighetsstyrning; visuell styrning som reserv. Metodval måste baseras på tillförlitlighet, risk och mätt kostnad, inte en absolut regel.

## 4. Prioriterad genomförandeplan

### Fas 0 — Kodinventering och baslinje (P0, obligatorisk grind)

1. Frys och dokumentera granskad commit-SHA och Windows/testmiljö.
2. Kartlägg EYES, WEB, HANDS, AgentLoop, TaskContract, ScopePolicy, routing, minne och deras faktiska gränssnitt.
3. Sök efter befintlig Playwright/Selenium/CDP/browser-funktionalitet, sessionshantering och testfixturer.
4. Klassificera varje behov: **återanvänd direkt / utöka befintligt / bygg nytt / avstå**.
5. Etablera baslinje: testutfall, svarstid, modellrop, token, CPU/GPU-minne, fel och återhämtning. Markera om ett mått ännu inte kan mätas.
6. Dokumentera risker och beroenden till andra pågående PR:er.

**Exit:** Inventeringsmatris med filreferenser, beslut och mätbar baslinje. Inga arkitekturantaganden behandlas som verifierad kod.

### Fas 1 — Läsbar BrowserAdapter (P0)

1. Välj minsta möjliga webbläsargränssnitt efter inventeringen; föredra befintligt beroende.
2. Inför isolerad testprofil, navigation, DOM-/tillgänglighetsobservation och stabila elementreferenser.
3. Normalisera observationer och fel; behåll proveniens och möjlighet att återskapa resultat.
4. Bygg lokal testwebbapp med formulär, dynamiska element, popup och förändrad DOM.
5. Implementera enbart läs- och navigeringsoperationer.

**Exit:** Reproducerbara lästester, inga externa skrivningar, inga hemligheter i loggar.

### Fas 2 — Policykopplad interaktion (P0)

1. Definiera typade WebTask/WebAction/WebResult-kontrakt med tillåtna origins, operationer, timeout, maxsteg och evidens.
2. Koppla varje handling till befintlig ScopePolicy och TaskContract; neka vid saknad behörighet.
3. Lägg till fill/click/scroll endast mot lokal testapp och med uttryckligt godkännande där det behövs.
4. Verifiera *resultatets tillstånd*, inte bara lyckad klick- eller tangentbordshändelse.
5. Testa avbrott, timeout, felaktigt mål, domänbyte och omförsök.

**Exit:** Policy- och fail-closed-tester gröna; ingen generell upplåsning av HANDS.

### Fas 3 — EYES/HANDS-fallback och mini-exekvering (P1)

1. Inför visuell observation endast när struktur/API inte räcker eller vid verifieringsbehov.
2. Begränsa miniagentens uppgift, steg, tid, kontext och verktygsrättigheter.
3. Återanvänd AgentLoop i stället för en andra obegränsad loop.
4. Testa popup, canvas-liknande gränssnitt, förflyttade element och osäkra koordinater.
5. Avbryt eller begär beslut när tillförlitlig elementidentifiering saknas.

**Exit:** Sammanhängande lokal webbuppgift klaras med verifierat utfall och kontrollerad fallback.

### Fas 4 — Lean-optimering och procedurminne (P1)

1. Profilera var tid, token, observationer och minne faktiskt går åt.
2. Inför selektiv DOM-filtrering, differensobservationer och cache endast där mätning motiverar det.
3. Destillera verifierade procedurer till versionsbundna färdigheter med proveniens, giltighetsvillkor och test.
4. Invalidera vid DOM-/versionsdrift, ändrade behörigheter eller verifieringsfel.
5. Återanvänd befintligt minne/ENIGMA där kontrakten passar; undvik parallell lagring.
6. Kräv separat godkännande innan ny destillerad procedur får användas för effektfull handling.

**Exit:** Dokumenterad förbättring jämfört med fas 0 utan sämre korrekthet, säkerhet eller spårbarhet.

### Fas 5 — Adaptiv lokal modell och bredare UI (P2)

1. Jämför deterministisk styrning med liten lokal modell för tvetydiga UI-fall.
2. Routa efter observerad osäkerhet, kostnad och risk; större modell endast vid behov.
3. Utvärdera om BrowserAdapter kan bli en adapter under ett generellt Interaction Runtime för Windows/Godot/Electron.
4. Utvidga först efter separat designbeslut, regressionstest och prestandaevidens.

**Exit:** Beslut baserat på faktiska mätvärden, inte antagna vinster.

## 5. Arbetsmetod för varje utvecklingsslice

1. **Sortera:** identifiera exakta filer, befintliga lösningar och berörda tester.
2. **Systematisera:** formulera ett smalt kontrakt och en isolerad ändring med tydligt ägarskap.
3. **Städa:** ta bort verifierad duplicering och onödig dataöverföring inom ändringens scope.
4. **Standardisera:** lägg till positiva, negativa, säkerhets- och regressionstester.
5. **Skapa vana:** registrera före/efter-mått, lärdomar, kvarstående risker och nästa förbättring.

Varje slice ska vara liten nog att granskas separat och kunna återställas. Håll WIP låg: en huvudförändring per slice, inga orelaterade refaktoreringar. PR ska visa syfte, berörda filer, tester, mätning, risk och rollback. Ingen merge på enbart gröna enhetstester om säkerhetsgrind eller integrationstest saknas.

## 6. Mätetal och kvalitetsspärrar

**Korrekthet:** andel fullföljda uppgifter med verifierat rätt resultat; falskt positiva verifieringar; felaktiga klick; återhämtningsgrad.

**Resursåtgång:** modellrop, input/output-token, antal DOM-/skärmobservationer, cacheträffar, total tid, CPU/RAM/VRAM och energi där tillförlitlig mätning finns.

**Utvecklingsflöde:** ändringens ledtid, WIP, duplicerade implementationer, regressionsfel, testflakighet och rollback-tid.

**Säkerhet:** otillåtna handlingar ska nekas; domänbyte och prompt injection från sidinnehåll ska inte ändra policy; inga credentials, cookies eller tokens i modellkontext eller vanliga loggar; tydliga användargodkännanden för externa effektfulla åtgärder.

Måltal fastställs först efter baslinjen. Påstå aldrig uppmätta besparingar utan reproducerbar jämförelse.

## 7. Säkerhet, data och återhämtning

- Webbplatsinnehåll är **opålitlig indata**, aldrig instruktioner med rätt att ändra uppdrag eller behörigheter.
- Isolerade webbläsarprofiler och skyddade sessioner; inga hemligheter i modellpromptar, procedurminne eller diagnostik.
- Explicit tillåtna domäner och åtgärder; verifiera redirect och iframe-origin.
- Skrivningar, publicering, köp, radering och externa meddelanden kräver lämplig explicit auktorisation; ingen automatisk policyeskalering.
- Begränsade omförsök med idempotenskontroll; undvik dubbelpublicering och dubbelinskick.
- Logga beslut och evidens med sekretessfilter och fastställd retention.
- Stöd avbryt, sessionsterminering och rollback där operationen faktiskt kan återställas. Påstå inte rollback för irreversibla externa handlingar.

## 8. Definition of Done

En fas är inte klar förrän:
- Funktionalitet och berörda befintliga gränssnitt är verifierade på angiven commit.
- Tester täcker lyckad väg, fel, policyavslag, timeout och relevant regression.
- Resursmått finns eller är tydligt markerade som ej mätta.
- Dokumentation och ägarskap är uppdaterade utan dubblerad källa till sanning.
- Ingen ny säkerhetsväg kringgår TaskContract/ScopePolicy/HANDS-låsningar.
- Diff är avgränsad, granskad och möjlig att återställa.
- Resultat, begränsningar och kvarvarande arbete rapporteras utan att överdriva status.

## 9. Första konkreta arbetsorder

**Utför endast fas 0 först.** Leverera en kodanknuten inventeringsrapport med:
1. Komponent → fil/modul → faktiskt API → befintliga tester → verifierad status.
2. Gap för BrowserAdapter, sessioner, policykoppling, verifiering och procedurminne.
3. Klassificering återanvänd/utöka/ny/avstå med kort motivering.
4. Minimal första implementation-slice och dess acceptanstester.
5. Risk- och regressionsmatris samt före-mätning.

Ingen implementation eller upplåsning av HANDS följer automatiskt av detta PM.

---
**Beslutsprincip:** Den bästa komponenten är den vi inte behöver bygga. Den bästa optimeringen är den som bevisligen sparar resurser utan att försvaga verifierbarhet, säkerhet eller användarens kontroll.
