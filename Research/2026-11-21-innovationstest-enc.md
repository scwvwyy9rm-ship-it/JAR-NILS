# JAR-NILS – Innovationstest: veckans forskning mot ENIGMA Native Architecture

**Datum:** 2026-11-21
**Prövas mot:** [ADR-ENC-001 – ENIGMA Native Architecture](https://github.com/scwvwyy9rm-ship-it/JAR-NILS/pull/6) (PR #6, ännu inte sammanslagen), ENIGMA Neural Core (ENC R0–R9, N0–N2) och befintlig ENIGMA Core (Lines/Delta/Hybrid, E1–E3).
**Prövat material:** de fem källorna i [veckorapporten](2026-11-21.md) och [repo-kopplingen](2026-11-21-repo-crosswalk.md).
**Status:** analys och experimentförslag. Ingen kod, körning, träning, merge eller investering är godkänd.

> **Underlagets begränsningar.**
> 1. Originalartiklarna gick inte att läsa: sessionens nätverk når inte arxiv.org. Allt om artiklarna nedan bygger på sammanfattningarna i veckorapporten och repo-kopplingen och är **inte kontrollerat mot källorna**.
> 2. `LocalProgrammer` (befintlig ENIGMA-kod, ENC-arkivet R0–R9, PR #365) har inte lästs. Uppgifter om baslinjer och tidigare NO-GO/HOLD kommer från ADR-ENC-001 och repo-kopplingen.
> 3. Avsnittet om tidigare kända metoder bygger på allmänt känd litteratur fram till mitten av 2026. Den är inte sökt fram eller kontrollerad i den här omgången.

## 1. Testmetod

Varje fynd prövas med visionens tre frågor: **vad upptäcktes, vad missade eller begränsade metoden, och kan insikten ge något mätbart bättre inom JAR-NILS?** Fynden kopplas till ADR-ENC-001:s hypoteser:

- **H1** strukturell kompression
- **H2** modellmedveten kostnad
- **H3** samdesignad inlärning
- **H4** beroendemedveten blockindelning

Varje fynd får ett utfall:

- **ANVÄND:** insikten bör in i en specifikation eller ett experimentförslag.
- **HOLD:** relevant, men kräver ny evidens eller en annan fas.
- **NEJ:** ingen materiell nytta för ENIGMA, eller i konflikt med ADR:ens gränser.

Ett utfall är ett forskningsomdöme, inte ett körgodkännande.

## 2. Resultat i korthet

| Fynd | Viktigaste insikt för ENIGMA | Hypotes | Utfall |
| --- | --- | --- | --- |
| Timeout Cascades | Eskalera **representationen**, inte bara modellen: kompakt ENIGMA-IR först och original endast när verifiering misslyckas eller modellen begär det | H2, ADR §3.3 | **ANVÄND (P1)** |
| CECAR | Samoptimera modellens val med vad som redan ligger i cache. Översatt: välj COPY/PATCH-kodning så att KV-/prefixcachen återanvänds | H2 | **ANVÄND som designprincip (P1)**; själva MoE-offloaden HOLD (P2) |
| EchoMoE | Beräkna på **förändringen** mot ett tidigare tillstånd. Översatt: Neural Core återanvänder aktiveringar för COPY-spann och räknar bara på PATCH-delen | H3, ny H5 | **HOLD**: stark hypotes, kräver R7-kontroll och träningsgodkännande |
| Linglong Agent Service | Bekräftar ADR:ens gräns mellan modell och exekvering. Verktygsutdata och loggar är troligen den mest redundanta datan i agentsessioner | H1 (korpus) | **NEJ** till arkitekturändring; **ANVÄND** som korpusval |
| Energy Cost of Quantized Agents (okt.) | Mätprotokoll för joule per verifierad uppgift | Mätmetod | **ANVÄND** som metodreferens; inte ett nytt fynd |

**Huvudslutsats:** Ingen av de nya källorna gör ENIGMA-CRG överflödig, och ingen av dem bevisar den heller. Den viktigaste gemensamma insikten är att **den verkliga vinsten sitter i beräkning som slipper göras om, inte i byte som sparas**. Tre av fem källor vinner genom att återanvända redan gjort arbete: cache, delta eller den billigare vägen först. Det stödjer visionens krav på modellanpassad effektivitet. Det innebär också att ENIGMA-CRG bör prövas mot **KV-/prefixcache-baslinjer** och inte bara mot zstd.

## 3. Prövning per fynd

### 3.1 Timeout Cascades (18 nov 2026)

- **Vad som upptäcktes:** En liten modell försöker först och en större tar över vid timeout eller misslyckande. Författarna rapporterar upp till 33 % lägre GPU-tid på kodningsuppgifter i sin egen miljö.
- **Begränsningar och förbisedda möjligheter:**
  - Timeout är en grov signal för eskalering. JAR-NILS har bättre, deterministiska signaler: tester som passerar, hashmatchning och att modellen uttryckligen begär källan.
  - Metoden eskalerar bara *modellen*. Kontexten kan eskaleras på samma sätt.
- **Innovation för ENIGMA – representationskaskad:**
  1. Steg 0: kompakt ENIGMA-IR med COPY/PATCH-referenser och modellen ser inte originalet.
  2. Steg 1: om verifieringen misslyckas, eller modellen begär ett `cid`, hämtas de berörda originalspannen behörigt.
  3. Steg 2: fullständig RAW.

  Det gör ADR §3.3 ("modellen ska kunna begära behörig återhämtning") till en mätbar kostnadsmekanism. Felaktig komprimering blir ett kostnadsproblem i stället för ett kvalitetsproblem, eftersom verifieringen fångar felet.
- **Risk:** Om modellen sällan begär original när den borde, slår felen igenom. Antalet *missade* återhämtningar måste därför mätas och inte bara antalet eskaleringar.
- **Utfall: ANVÄND (P1)**, se experiment X2.

### 3.2 CECAR (15 nov 2026)

- **Vad som upptäcktes:** MoE-routing och expertcache optimeras tillsammans. Ibland väljs en sämre men redan inladdad expert. Författarna rapporterar 4,5× snabbare avkodning för Qwen3-30B-A3B på 16 GB VRAM.
- **Begränsningar:**
  - Metoden är förlustbehäftad i förhållande till modellens ordinarie routing.
  - Den är mätt i token/s och inte i verifierade uppgifter.
  - Stöd för AMD/ROCm är inte visat.
- **Förbisedd möjlighet:** Principen gäller inte bara experter. *Indata* kan också väljas utifrån vad som redan är beräknat. En ENIGMA-kodare som vet vad som finns i modellens prefix-/KV-cache kan välja den kodning som ger flest cacheträffar, även om den inte är kortast i byte. Det är H2 i konkret form och skiljer sig från klassisk kompression, som bara minimerar storlek.
- **Gräns mot ADR:** CECAR-liknande förlustbehäftad routing får aldrig ligga i codec-lagret (§3.2). Den får bara finnas på modellsidan och då med mätt kvalitetspåverkan.
- **Neural Core:** N0–N2 (5–50M) är täta modeller, så MoE-offload är inte aktuellt där. Principen om cachemedveten policy är relevant för en framtida större modellfamilj (fas G).
- **Utfall: ANVÄND som designprincip för H2 (P1).** Själva MoE-offloaden är **HOLD (P2)** i hårdvaruspåret med kompatibilitetsgrind, enligt repo-kopplingen.

### 3.3 EchoMoE (17 nov 2026)

- **Vad som upptäcktes:** Mellan acceleratorer skickas komprimerade *förändringar* av aktiveringar i stället för hela aktiveringar. Författarna rapporterar 58 % mindre kommunikation, 22,6 % högre genomströmning och upp till 3,8 procentenheters kvalitetsförlust.
- **Begränsningar:**
  - Metoden är förlustbehäftad och kräver anpassningsträning.
  - Den gäller kommunikation mellan flera GPU:er, inte en enda lokal GPU.
- **Förbisedd möjlighet, och det mest intressanta fyndet för Neural Core:** Samma princip går att tillämpa *inom* modellen och på *indatastruktur*. När ENIGMA-IR säger att ett block är `COPY(cid, span)` av något modellen redan har bearbetat, borde motsvarande KV-tillstånd kunna återanvändas utan omberäkning. När ett block är `PATCH`, räknar modellen bara på förändringen. Det ger en ny hypotes:

  > **H5 – Strukturstyrd beräkningsåteranvändning:** En modell som får ENIGMA-IR med explicita COPY/PATCH-gränser kan återanvända tidigare beräknade tillstånd för kopierade spann. Då minskar FLOPs per uppgift mer än vad tokenbesparingen ensam förklarar, utan någon kvalitetsförlust på förregistrerade uppgifter.

  H5 är det tydligaste sättet att visa att codec och modell verkligen är **samdesignade** och inte bara kopplade efter varandra. Det är den kärnfråga visionen ställer.
- **Kända risker:**
  1. KV-tillstånd beror på position och föregående kontext. Att återanvända dem utanför prefixet är inte exakt, se CacheBlend-liknande arbeten nedan. Det är en *modellfråga* och aldrig en codec-garanti.
  2. H5 måste kontrolleras mot R7 (neural VSC, NO-GO) så att den inte är samma idé under nytt namn. Jag har inte kunnat läsa R7, så den kontrollen återstår.
- **Utfall: HOLD.** Formulera H5 nu, men pröva den först i fas F efter separat träningsgodkännande. Se experiment X3.

### 3.4 Linglong Agent Service (16 nov 2026)

- **Vad som upptäcktes:** En central tjänst för modell och session, med verktygskörning i separata miljöer. Arbetet visar körbara kontrakt men ingen prestandavinst.
- **Begränsningar:** Inga mätningar av effektivitet eller säkerhet.
- **Insikt för ENIGMA:** Arkitekturen bekräftar ADR §3 lager 5 men tillför inget nytt där. Mönstret visar däremot *var redundansen finns* i agentsystem: verktygsutdata, loggar och fil-/diffhistorik skickas om och om igen mellan parterna. Det är rätt korpus för H1 och H4, mer representativt än generell prosa.
- **Utfall: NEJ** till arkitekturändring, en ny tjänst eller en ny sessionstore. **ANVÄND** som motivering till korpusvalet i X1.

### 3.5 Energy Cost of Quantized Agents (23 okt 2026, metodreferens)

- **Vad som är relevant:** Måttet energi per *färdig* agentuppgift i stället för per token.
- **Insikt för ENIGMA:** Kvantisering och ENIGMA-IR kan samverka. En modell med kortare, mer strukturerad indata tål kanske hårdare kvantisering, eller sämre om strukturen gör varje token mer informationstät. Det är en spekulativ hypotes och inget fynd.
- **Utfall: ANVÄND** som mätprotokoll för joule per verifierad uppgift i X2 och X3.

## 4. Originalitetskontroll av ENIGMA-CRG

Visionen kräver att idéer inte ska presenteras som nya under andra namn. ENIGMA-CRG:s operationer har var för sig välkända föregångare. Litteraturen nedan är känd sedan tidigare och inte kontrollerad i den här omgången.

| ENIGMA-CRG | Närmaste kända föregångare | Vad som kan vara nytt för ENIGMA |
| --- | --- | --- |
| `COPY(cid, span)` | LZ77, zstd med långa fönster/ordlistor, deduplicering | Hashbunden, behörighetskontrollerad och kausal referens till *externa versionsobjekt* |
| `PATCH(cid, edits)` | VCDIFF/xdelta, bsdiff, git delta | Patch som modellen kan *läsa* och som styr vilken beräkning modellen gör (H5) |
| `TEMPLATE(id, slots, residual)` | Grammatikkompression (Sequitur, Re-Pair), loggmallar (Drain, CLP/LogZip) | Mallar över kod, loggar och konversation med byteexakt residual och modellinsyn |
| Adaptiv blockindelning (H4) | Innehållsdefinierad chunking (Rabin, FastCDC), AST-baserad tokenisering, Byte Latent Transformer (entropipatchar) | Blockgränser efter *beräkningsberoenden*, inte entropi |
| Modell över komprimerad data (H3) | Lester m.fl. 2024, "Training LLMs over Neurally Compressed Text". Där var aritmetiskt kodad text svår att lära sig, medan "equal-info windows" fungerade men var sämre än subword-tokens vid samma beräkning | Strukturerad IR i stället för entropikodade bitar |
| Återanvändning av beräkning (H2, H5) | Prefixcache (RadixAttention/SGLang, llama.cpp prompt cache), återanvändning av KV-cache utanför prefixet (CacheBlend), prompt lookup decoding | Att codec-strukturen *talar om* för modellen vad som går att återanvända |

**Slutsats:**
- **Operationerna RAW/COPY/PATCH/TEMPLATE är inte nya.** De bör beskrivas som en kanonisk sammansättning av kända primitiver.
- **Det som kan vara originellt** är kombinationen av (a) kausala, verifierbara referenser till externa objekt och (b) att samma struktur styr modellens beräkning, genom cacheval (H2) och återanvändning av tillstånd (H5).
- **Lester m.fl. stödjer ADR-ENC-001 princip 3:** modeller lär sig dåligt över täta, entropikodade strömmar. Lagringskodning och modellindata måste vara olika gränssnitt. H3 bör därför prövas på strukturerad IR och inte på codec-bitflödet.
- **Konsekvens för baslinjerna:** Fas D bör utöver zstd också jämföra mot **xdelta/VCDIFF** för PATCH och en **CLP-/Drain-liknande mallparser** för loggar. Fas E bör jämföra mot **standardtokens med prefixcache**. Annars kan en vinst bero på en för svag baslinje.

## 5. Föreslagna experiment – inga körgodkännanden

Experiment-ID har prefixet `INV-2026-11-21-` för att inte förväxlas med ENIGMA E1–E3 eller veckorapportens `R-2026-11-21-E*`. Tröskelvärdena är förslag som ska förhandsregistreras, inte resultat.

### X1 – Är CRG:s operationer värda sin plats? (P0, fas C/D, deterministisk, ingen modell)

- **Fråga:** Ger COPY/PATCH/TEMPLATE nettovinst mot de bästa *etablerade* alternativen?
- **Korpusar** (frysta, licens- och behörighetskontrollerade): (1) agentsessioners verktygsutdata och loggar, (2) nästan identiska kodfiler och versionskedjor, (3) konversationshistorik.
- **Baslinjer:** RAW, zstd -19 --long med och utan tränad ordlista, xdelta/VCDIFF, en CLP-liknande mallparser och dagens ENIGMA Lines/Delta/Hybrid.
- **Mått:**
  - total kodad storlek *inklusive* ordlistor, mallar och referensobjekt
  - antal tokens med den faktiska tokenizern
  - codec-CPU och minne
  - D(C(x,H),H)==x byte för byte på alla prov
  - negativa tester enligt ADR §6.2
- **Avbrottskriterium:** En operation som inte ger minst 5 % nettovinst mot bästa baslinje på minst 2 av 3 korpusar stryks ur CRG-v0. Klarar ingen operation kravet blir H1 **NO-GO** i nuvarande form.

### X2 – Representationskaskad (P1, fas E, befintliga lokala modeller, ingen träning)

- **Fråga:** Sänker "kompakt först, original vid behov" kostnaden per verifierat löst uppgift?
- **Armar:**
  - A: RAW
  - B: RAW med prefixcache
  - C: dagens ENIGMA Hybrid
  - D: ENIGMA-IR i kaskad, med eskalering vid misslyckad verifiering eller begärt `cid`
- **Lika för alla armar:** modellbindningar, uppgifter, maxantal försök och parametrar. Kontrollera att prompterna faktiskt skiljer sig mellan armarna, eftersom tidigare E1-körningar var ogiltiga av just det skälet.
- **Mått:**
  - verifierat lösta uppgifter
  - joule och median/p95-tid per verifierat löst uppgift, inklusive misslyckade försök
  - andelen cacheträffar
  - antal eskaleringar
  - **missade återhämtningar**: fel som en eskalering hade förhindrat
- **Avbrottskriterium:** D måste slå både B och C i kostnad per verifierad uppgift *utan* lägre antal lösta uppgifter och utan nya kritiska regressioner. Annars **NO-GO** för kaskaden.

### X3 – Strukturstyrd beräkningsåteranvändning, H5 (P2, fas F, kräver träningsgodkännande)

- **Förutsättning:** H5 har kontrollerats mot R7/ENC-arkivet och är inte en återinförd NO-GO-idé.
- **Fråga:** Kan en N0-modell (~5M) som får IR med COPY/PATCH-gränser återanvända KV-tillstånd för kopierade spann och räkna mindre utan kvalitetsförlust?
- **Jämförelse:** samma N0-arkitektur, data och beräkningsbudget med vanliga tokens och prefixcache. Flera slumpfrön.
- **Uppgifter:** syntetiska kopiera/ändra/peka-ut-förändring-uppgifter och små kodredigeringar med exakt verifiering.
- **Mått:** FLOPs och tid per uppgift, verifierad korrekthet samt regressioner på negationer, operatorer och siffervärden.
- **Avbrottskriterium:** Om beräkningsbesparingen inte överstiger vad tokenreduktionen ensam förklarar, eller om korrektheten sjunker, är H5 **NO-GO**.

**Föreslagen ordning:** X1 före X2 före X3. X1 är billig och deterministisk och avgör om CRG-v0 alls ska byggas. X2 kan delvis köras med dagens ENIGMA Hybrid medan X1 pågår.

## 6. Ändringsförslag till ADR-ENC-001 (för projektledningens beslut)

1. **Lägg till H5** (strukturstyrd beräkningsåteranvändning) som den hypotes som tydligast prövar *samdesign*.
2. **Skärp baslinjerna i §6, fas D/E:** lägg till xdelta/VCDIFF, en CLP-/Drain-liknande mallparser och standardtokens med prefixcache.
3. **Formulera nyhetsanspråket försiktigare i §1:** RAW/COPY/PATCH/TEMPLATE är kända primitiver. Det som kan vara nytt är kausal verifierbar referensbindning tillsammans med modellbeteende som styrs av strukturen.
4. **Lägg till representationskaskaden** som konkret mekanism för §3.3, med *missade återhämtningar* som obligatoriskt mått.

## 7. Öppna punkter

- Läs originalartiklarna när arxiv.org går att nå och rätta det här dokumentet i en ny revision om sammanfattningarna visar sig fel.
- Kontrollera H5 och X1–X3 mot befintlig ENIGMA-kod och ENC R0–R9 i `LocalProgrammer`, särskilt R7.
- Gör en systematisk sökning efter tidigare arbeten i fas A, så att tabellen i §4 inte enbart vilar på allmänt känd litteratur.

**Beslutsläge:** Det här dokumentet föreslår hypoteser, baslinjer och experiment. Det ändrar inga beslut, säkerhetsgrindar eller körgodkännanden.
