# INV-2026-11-22-X4 – Förhandsregistrering: inaktuellt KV-tillstånd och korsade armar

**Registrerad:** 2026-11-22, efter röktest på 4 uppgifter och före huvudkörningen.
**Godkännande:** projektledningen 2026-11-22: "börja nästa test … vi ska vara experimentella … korsa experimentformer … det som ger mest vinst i tid, tokens, resultat tar vi". Godkännandet gäller inferens med samma öppna modeller som i X2 och X3, i en isolerad molncontainer. Ingen träning.
**Fråga:** Håller H5 (X3a: GO) när ändringen påverkar tolkningen av *oförändrade* rader, där kopierade KV-tillstånd är beräknade i den gamla kontexten? Vilken korsning av representation (IR, X2), återanvändning (REUSE, X3a) och beroendeanalys (H4) ger mest vinst?

## Uppgifter (frysta)

`x4_tasks.json` innehåller 60 syntetiska Python-program (~55 rader, slumpfrö 20261122) från `build_x4_tasks.py`.
- **Facit** tas fram genom att köra den aktuella versionen.
- **Ändringar som påverkar utskriften (40):**
  - `const` (14): en konstant högst upp, som används av en hjälpfunktion som `main` anropar.
  - `op` (13): en operator i en hjälpfunktion.
  - `default` (13): ett standardargument som den oförändrade anroparen förlitar sig på.
- **Kontroll (20):** ändring i en distraktorfunktion som inte anropas, så utskriften är oförändrad.

Uppgiften är: "What does the CURRENT version print?" Modellen ska spåra `main()` rad för rad och avsluta med `ANSWER: <int>`. Prompten är på engelska, och svaret förfylls med `Trace:`. Röktestet visade att direkta svar utan spårning var gissningar även i FULL.

## Armar

Gemensamt: rubriken och den tidigare lästa versionen ligger i KV-cachen, och raderna tokeniseras radvis.

| Arm | Ursprung | Beräknas i den nya turen |
| --- | --- | --- |
| FULL | övre gräns | hela aktuella versionen + fråga |
| IR | X2 C | ENIGMA-IR PATCH-text + fråga |
| REUSE | X3a | infogade rader + fråga. Kopierade rader återanvänds i KV |
| REUSE+NBR | X3a | som REUSE, men ±1 grannrad runt varje ändring räknas om |
| **REUSE+DEP** | **ny: H4 × H5** | som REUSE, men gamla rader räknas om om de refererar en identifierare i ändrade rader eller anropar en funktion som innehåller en ändrad eller omräknad rad. Urvalet görs med deterministisk statisk analys (fixpunkt, högst 4 varv) |
| **REUSE+HINT** | **ny: X2 × X3a** | som REUSE, plus en kort ändringsnotis `⟦CHANGED: \`gammal\` → \`ny\`⟧` före frågan |

## Mått

Per arm och modell:
- korrekta svar, totalt och per ändringstyp
- **inaktuella svar** (svaret är lika med den gamla versionens utskrift, för de 40 icke-kontrollerna)
- beräknade prompttokens, genererade tokens och CPU-s/väggtid per korrekt uppgift

## Beslutsregler (per modell, tröskel ±2 uppgifter av 60)

1. **H5 håller** om REUSE ≥ FULL − 2 korrekta *och* inte har fler än 2 inaktuella svar än FULL.
2. **H5 faller för den här uppgiftstypen** om REUSE < FULL − 2 *eller* har > 2 inaktuella svar mer än FULL. Då prövas om REUSE+DEP eller REUSE+NBR återställer kvaliteten (≥ FULL − 2). Gör de det, blir det **deterministisk lösning → X3b behövs inte**. Gör ingen av dem det, är **X3b motiverad**.
3. **Vinnare för produktion**, enligt projektledningens kriterium att det som ger mest vinst tas: den arm som har lägst CPU-s per korrekt uppgift bland armarna med ≥ FULL − 2 korrekta på *båda* modellerna.

## Kända begränsningar

- Syntetiska program, en uppgiftsfamilj.
- Spårningssteget gör att genereringen dominerar kostnaden (~120–160 tokens). Skillnader i prompttokens slår därför igenom mindre på CPU-tid än i X2 och X3a.
- Facit kommer från körning. I en verklig agent skulle körningen *själv* vara billigast och exakt (LEAN-principen). Testet mäter modellförståelse under förändring, inte det bästa sättet att få fram utskriften.
