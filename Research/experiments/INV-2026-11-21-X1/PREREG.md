# INV-2026-11-21-X1 – Förhandsregistrering

**Registrerad:** 2026-11-21, före första körning.
**Godkännande:** projektledningen ("Vi börjar med x1", 2026-11-21). Godkännandet gäller endast X1: deterministiska codec-försök i isolerad miljö, utan modell, träning eller produktionskoppling.
**Fråga:** Ger ENIGMA-CRG:s operationer COPY, PATCH och TEMPLATE nettovinst mot de bästa etablerade alternativen (ADR-ENC-001 H1, fas C/D)?

## Korpusar (frysta)

| ID | Innehåll | Källa och pin |
| --- | --- | --- |
| K1 | Systemloggar, 16 system × 2 000 rader, i objekt om 100 rader (320 objekt) | `logpai/loghub@dd61d09`, endast för forskning och med hänvisning till loghub |
| K2 | Kodversionskedjor: alla `src/click/*.py` vid start och därefter varje ändrad fil efter vart och ett av 100 commits (203 objekt) | `pallets/click`, `565f36d`..`08b803c` (BSD-3) |
| K3 | Simulerad agentsession över samma 100 commits: `git show --stat`, numrerad filläsning, `git diff`, `grep` på def/class och periodvis `ls-tree` (671 objekt) | som K2 |

**Avvikelse från X1-förslaget:** Korpusen "konversationshistorik" ersätts av K3, eftersom licens- och behörighetskontrollerade konversationer saknas i den här miljön. K3 representerar agentsessioner med verktygsutdata, vilket innovationstestet pekade ut som den mest redundanta datan.

## Regimer

- **R2 inkrementell (primär):** Varje objekt kodas givet att mottagaren redan har alla tidigare objekt H, som är kausala, hashbundna och versionsbundna. Det motsvarar agentens situation, där bara det nya ska skickas eller lagras. Måttet är summan av kodade byte över alla objekt.
- **R1 arkiv (sekundär):** Hela korpusen kodas som en självständig ström.

## Armar

**Baslinjer:**
- RAW
- `zstd -19` per objekt
- `zstd -19` med hela tidigare historik som referensprefix (rå innehållsordlista, R2)
- `xdelta3 -9` mot basobjektet (föregående objekt med samma nyckel, R2)
- `zstd -19 --long=27` och `xz -9e` (R1)
- CLP-/Drain-liknande mallkodning följd av zstd (TPL-baslinje)

**Baslinje som inte är tillgänglig:** ENIGMA Lines/Delta/Hybrid. Koden finns i `LocalProgrammer`, som inte har granskats. Resultatet blir därför **preliminärt** för den jämförelsen.

**ENIGMA-CRG v0:** Alla varianter ger en binär operationsström som sedan entropikodas med zstd -19, så att varianterna jämförs på lika villkor.

| Variant | Operationer |
| --- | --- |
| `CRG{COPY}` | RAW + COPY (byteexakta spann ur valfritt tidigare objekt, minst 32 byte) |
| `CRG{PATCH}` | RAW + PATCH (radvis redigering mot basobjektet) |
| `CRG{TEMPLATE}` | RAW + TEMPLATE (radmallar med variabla fält) |
| `CRG{ALL}` | per objekt den minsta av ovanstående |

Varje refererat objekt binds med full SHA-256. Kostnaden för hashar, malltabeller och operationshuvuden räknas in.

## Mått

1. Total kodad storlek per korpus och regim, inklusive allt metadata.
2. **Förlustfrihet:** `D(C(x,H),H) == x` byte för byte för alla objekt i alla CRG-varianter. Ett enda fel underkänner varianten.
3. **Negativa tester:** manipulerad hash, saknad referens, framåtreferens/cykel, trunkerad ström, okänd operation, expansionsbudget överskriden, COPY utanför källans gränser. Samtliga ska ge verifierbart avslag.
4. Kodnings- och avkodningstid (CPU, enkeltråd, Python-prototyp, endast indikativ).
5. Sekundärt: antal Qwen2-tokens för RAW respektive en textrendering av CRG{ALL} (förhandsindikator för X2).

## Beslutsregel (från innovationstestet, §5 X1)

En operation behålls i CRG-v0 om dess enskilda variant `CRG{op}` ger **minst 5 % lägre total storlek än bästa baslinje i R2** på **minst 2 av 3 korpusar**. Övriga stryks.

- Klarar ingen operation kravet: **H1 NO-GO** i nuvarande form, med reservation för den saknade ENIGMA-baslinjen.
- Klarar minst en operation kravet: **H1 HOLD → vidare**. En vinst mot ENIGMA Hybrid är inte visad förrän den baslinjen har körts.
- R1 redovisas men avgör inte.

## Kända begränsningar

- Python-prototyp, så tiderna är inte jämförbara med zstd i C.
- Ingen modellmätning. Tokenantal är inte modellförståelse.
- CRG v0 blandar inte operationer inom ett objekt (till exempel TEMPLATE-rader med COPY). Det kan underskatta CRG.
- Resultaten avser bara dessa tre korpusar.
