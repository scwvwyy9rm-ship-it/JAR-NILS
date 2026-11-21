# INV-2026-11-21-X2 – Förhandsregistrering

**Registrerad:** 2026-11-21, efter röktest på 3 uppgifter och före huvudkörningen.
**Godkännande:** projektledningen ("Kör vidare med X2 när K3 är klar", 2026-11-21). Godkännandet omfattar bara inferens med öppna förtränade modeller i en isolerad molncontainer. Ingen träning, ingen produktionskoppling och inga ändrade modellbindningar.
**Fråga:** Sänker representationskaskaden ("kompakt ENIGMA-IR först, verifierat original vid behov") kostnaden per verifierat korrekt löst uppgift utan att antalet korrekt lösta uppgifter minskar?

## Avvikelser från X2-förslaget i innovationstestet

| Förslag | Faktiskt | Skäl |
| --- | --- | --- |
| Befintliga lokala modellbindningar (Compact Ensemble) | Qwen2.5-Coder-1.5B-Instruct och -3B-Instruct, Q4_K_M (GGUF), llama.cpp 0.3.16 (llama-cpp-python) på 4 CPU-kärnor | `LocalProgrammer` och utvecklingsdatorn är inte tillgängliga |
| Joule per verifierad uppgift | **CPU-sekunder och väggtid** som energiproxy | Ingen energimätning finns i containern. Det är inte joule och ska inte redovisas som joule |
| Arm C: dagens ENIGMA Hybrid | Inte tillgänglig och utgår | Koden finns i `LocalProgrammer` |
| Verkliga agentuppgifter | Syntetiska citatuppgifter ur K2 (se nedan) | Kräver deterministiskt facit och en verifierare som körmiljön kan använda utan facit |

Modellfilernas SHA-256:
- 1.5B: `cc324af070c2ecbfd324a30884d2f951a7ff756aba85cb811a6ec436933bb046`
- 3B: `724fb256bec1ff062b2f65e4569e871ad2e95ab2a3989723d1769c54294730b7`

## Uppgifter (frysta)

`x2_tasks.json` innehåller 40 uppgifter ur K2 (click-versionskedjor), slumpfrö 20261121.
- **Ändrad (20):** funktionens signaturrad ändrades mellan tidigare och aktuell version.
- **Oförändrad (20):** funktionen ligger i ett ändrat område, men signaturraden är oförändrad. Det testar att modellen bevarar oförändrade värden.

Modellen har tidigare läst ett utdrag (±40 rader) av den gamla versionen. Filen har sedan ändrats. Uppgiften är att citera signaturraden `def F(` i den **aktuella** versionen.

## Armar

Den tidigare lästa versionen motsvarar en tidigare tur och antas ligga i KV-cachen i arm B–D. Den evalueras otidsatt före varje tidsmätning.

| Arm | Indata för den nya turen | Cache |
| --- | --- | --- |
| A RAW | tidigare version + aktuell version (RAW) + fråga | ingen, allt räknas |
| B RAW+cache | aktuell version (RAW) + fråga | tidigare version cachad |
| C IR+cache | ENIGMA-IR PATCH mot tidigare version + fråga | tidigare version cachad |
| D kaskad | som C. Om svaret inte klarar verifieringen återhämtas och hashverifieras originalet, som ges RAW i en ny fråga | tidigare version och C-turen cachade |

**Verifierare (D):** Körmiljön avkodar PATCH mot H och kontrollerar att svaret är en exakt rad i den aktuella versionen (bortsett från inledande och avslutande blanktecken) och att raden definierar `F`. Verifieraren använder inte facit.

**Förbehåll:** För citatuppgifter är verifieraren nästan lika stark som facit. Riktiga agentuppgifter har svagare verifierare, till exempel tester. Resultatet för D är därför en **övre gräns** för kaskadens nytta.

**Svarstolkning (låst):** Kodstaket och omslutande backticks tas bort, och den första raden som innehåller `def ` väljs. Ett svar är korrekt om det är lika med facit efter strip(). Generering sker deterministiskt (temp 0, top_k 1), med högst 96 tokens.

## Mått

Per arm och modell:
1. Antal korrekta uppgifter, totalt och för ändrad respektive oförändrad.
2. **Inaktuella svar:** antal ändrade uppgifter där svaret är lika med den gamla raden.
3. Nya prompttokens, CPU-sekunder och väggtid per uppgift.
4. **CPU-sekunder per korrekt löst uppgift**, det primära måttet, inklusive misslyckade försök.
5. För D: antal eskaleringar och **missade återhämtningar** (inte eskalerad och fel).

## Beslutsregel (från innovationstestet §5 X2, anpassad)

Kaskaden (D) är **GO för fortsatt utredning** om båda villkoren gäller för **båda** modellerna:
1. D har lägre CPU-sekunder per korrekt löst uppgift än både A och B (B är den skarpa baslinjen).
2. D löser minst lika många uppgifter som B, och inga ändrade uppgifter får inaktuella svar där B svarade rätt (inga nya kritiska regressioner).

Annars blir det **NO-GO** för kaskaden i den här formen. Gäller villkoren bara för en modell blir det **HOLD**. Utfallet arm C ensam redovisas, men avgör inte.

## Kända begränsningar

- 40 uppgifter av en enda uppgiftstyp, så de statistiska slutsatserna blir svaga. Skillnader på 1–2 uppgifter ska inte övertolkas.
- CPU-inferens i en delad molncontainer. Tiderna är relativa mellan armarna och inte överförbara till RX 9060 XT.
- Modellen har fått en kort förklaring av PATCH-formatet i systemprompten, som är identisk i alla armar. Ingen modell har tränats på ENIGMA-IR.
