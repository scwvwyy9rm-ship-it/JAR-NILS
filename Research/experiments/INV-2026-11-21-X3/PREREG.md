# INV-2026-11-21-X3 – Förhandsregistrering (H5: strukturstyrd beräkningsåteranvändning)

**Registrerad:** 2026-11-21, före all X3-körning.
**Godkännande:** projektledningen ("Jag godkänner", 2026-11-21, som svar på att X3 kräver träningsgodkännande). Godkännandet omfattar inferens och träning av forskningsmodeller (N0-skala, ~5M parametrar) i en isolerad molncontainer på CPU, utan produktionskoppling. Inga modellbindningar i `LocalProgrammer` ändras.

## Förkontroll mot ENC-arkivet (krav i innovationstestet §3.3)

Arkivet har lästs på `LocalProgrammer` branch `deepai/364-enc-research-archive` (PR #365): R5, R6, R7, R8 och R9.

| Tidigare beslut | Förhållande till H5 |
| --- | --- |
| **Neural VSC (R7), NO-GO:** lärd komprimering `C_θ` av sessionstillstånd, slagen av deterministisk extraktiv baslinje | **Inte samma.** H5 lär sig ingen komprimering. Återanvändningen gäller byteexakta COPY-spann ur hashbunden H. |
| **ACE (R5), NO-GO och "återinförs inte" (R8 D.4):** lärd adaptiv beräkningsfördelning (ACT/PonderNet/MoD) | **Delvis överlapp:** båda gäller "förändringsstyrd beräkning". **Skillnad:** H5 har ingen lärd stopp- eller routingpolicy. Vad som återanvänds bestäms deterministiskt av PATCH-strukturen, i linje med E-1:s lärdom att strukturbaserad routing är deterministisk. Den inlärda varianten av H5 (X3b) får **inte** innehålla lärd beräkningsfördelning. |
| **P-COMP (R6):** oetablerad, generell arkitekturfråga | H5 måste visa en ENC-specifik nytta, nämligen återanvändning som styrs av verifierbar COPY/PATCH-struktur. Annars är det en omdöpning av känd teknik. |
| **R7:s metodlärdom:** deterministisk baslinje först, träning bara vid mätt gap | **Tillämpas:** X3 delas i X3a (deterministisk, ingen träning) och X3b (träning), där X3b bara får köras om X3a visar ett gap. |

**Kända föregångare som måste namnges:** CacheBlend (Yao m.fl. 2024: KV-återanvändning utanför prefixet med selektiv omberäkning, utan träning), Block-Attention (Sun m.fl. 2024: finjustering så att block kan KV-kodas oberoende), prompt/prefix caching (RadixAttention, llama.cpp). ENIGMA-anspråket är *inte* att KV-återanvändning är nytt. Anspråket är att **byteexakt, hashbunden PATCH-struktur talar om exakt vad som kan återanvändas**.

**Utfall av förkontrollen:** H5 är **inte en återinförd NO-GO-idé**, med två villkor. (1) Ingen lärd beräkningsfördelning. (2) Den deterministiska nivån prövas först.

## X3a – deterministisk nivå (ingen träning)

**Modeller:** Qwen2.5-Coder-1.5B- och 3B-Instruct Q4_K_M, samma som i X2. **Uppgifter:** samma 40 som i X2 (`../INV-2026-11-21-X2/x2_tasks.json`).
**Gemensamt:** Rubriken och det tidigare lästa utdraget ligger i KV-cachen. Rader tokeniseras radvis i alla armar.

| Arm | Beräknas i den nya turen |
| --- | --- |
| FULL | hela aktuella utdraget + fråga (övre kvalitetsgräns) |
| IR | ENIGMA-IR PATCH-text + fråga |
| REUSE | infogade rader + fråga. KV redigeras på plats: borttagna rader tas bort, kopierade rader flyttas med RoPE-justering och återanvänds utan omberäkning |
| REUSE+NBR | som REUSE, men gamla rader närmast varje ändring (±1 rad) beräknas om |

**Självtest före huvudkörning:** (a) Flytta cache +1000/−1000 → identiska logits. (b) REUSE där alla gamla rader beräknas om → samma argmax som FULL. Om självtestet underkänns stoppas X3a.

**Mått:** korrekta svar (totalt, ändrad, oförändrad), inaktuella svar, beräknade tokens, CPU-s och väggtid per uppgift och per korrekt uppgift.

**Beslutsregel X3a** (per modell; tröskel ±1 uppgift av 40):
1. **H5 fungerar deterministiskt:** REUSE eller REUSE+NBR har ≥ FULL − 1 korrekta och beräknar färre tokens än IR. **Då startas inte X3b.** Enligt R7:s princip behövs ingen träning när den deterministiska lösningen räcker. Det blir H5 **GO (deterministisk)** för vidare arkitekturutredning.
2. **Gap:** både REUSE och REUSE+NBR har < FULL − 1 korrekta, med lägre kostnad än FULL. Då är **X3b motiverad**.
3. **Ingen nytta:** REUSE-armarna kostar inte mindre än IR eller FULL. Det blir H5 **NO-GO**.

Gäller olika regler för de två modellerna blir det **HOLD**, och X3b startas bara om regel 2 gäller för båda.

## X3b – träning (endast om X3a regel 2 gäller)

Två N0-modeller (~5M parametrar, 6 lager, d=256, RoPE, samma tokenizer och data) tränas på syntetiska kopiera/ändra/citera-uppgifter. Tre slumpfrön vardera.
- **N0-std:** tränas bara med fullständig kontext.
- **N0-reuse:** tränas också med KV-återanvända kopierade spann, så att modellen lär sig vara robust mot inaktuellt KV-tillstånd. Den får ingen lärd beräkningsfördelning.

Utvärdering sker med samma fyra armar på en hållen-ut mängd.

**Regel X3b:** **GO** om N0-reuse+REUSE har ≥ N0-std+FULL − 1 pp och bättre korrekthet än N0-std+REUSE med minst 5 pp (medel över frön, utan överlappande min/max). Annars **NO-GO**, och den inlärda delen av H5 avslutas.

Om X3b inte körs bevaras protokollet oförändrat som registrerat men ej utfört.

## Begränsningar

- Citatuppgifterna är enkla. Inaktuellt KV-tillstånd i kopierade rader påverkar dem troligen mindre än uppgifter som kräver resonemang över ändringens konsekvenser. Ett GO i X3a gäller bara denna uppgiftstyp.
- CPU-inferens, så tiderna är relativa.
- KV-redigeringen bygger på llama.cpp:s K-shift för RoPE. Självtestet kontrollerar den.
