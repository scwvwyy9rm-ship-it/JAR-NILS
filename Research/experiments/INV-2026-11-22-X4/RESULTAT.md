# INV-2026-11-22-X4 – Resultat

**Körd:** 2026-11-22 i en isolerad molncontainer: 4 vCPU, llama-cpp-python 0.3.16, 4 trådar, en körning i taget.
**Protokoll:** [PREREG.md](PREREG.md), committat före huvudkörningen. Riggen (`run_x4.py`) är oförändrad mot den registrerade versionen. Rådata finns i `x4_res_1.5b.json` och `x4_res_3b.json`.

## Beslut enligt förhandsregistrerade regler

> **Regel 1: H5 håller på båda modellerna.** Återanvänd KV-cache (REUSE) behåller FULL-kvalitet även när ändringen påverkar tolkningen av oförändrade rader.
> - 1.5B: REUSE har 52 korrekta mot FULL:s 53 och 2 inaktuella svar mot 1.
> - 3B: REUSE har 36 korrekta mot 34 och 0 inaktuella mot 0.
>
> X3b, som skulle träna modellen att tåla inaktuellt KV-tillstånd, behövs fortfarande inte.
>
> **Regel 3: vinnaren är REUSE+HINT**, korsningen X2 × X3a. Den har lägst CPU-s per korrekt uppgift på båda modellerna bland de armar som når minst FULL − 2 korrekta:
> - 1.5B: 33,5 mot FULL:s 40,3, det vill säga −17 %.
> - 3B: 100,1 mot FULL:s 150,3, det vill säga −33 %. Här löste den också 41 uppgifter mot FULL:s 34.
>
> **IR faller på uppgiftstypen.** Den klarade 0 av 13 operatorändringar på båda modellerna och gav 14 respektive 11 inaktuella svar.

## Resultat (60 uppgifter per modell: 40 som påverkar utskriften och 20 kontroller)

### Qwen2.5-Coder-1.5B-Instruct Q4_K_M

| Arm | Korrekta | const/14 | op/13 | default/13 | kontroll/20 | Inaktuella | Prompttokens | Genererade tokens | CPU-s per korrekt | Väggtid per korrekt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FULL | 53 | 12 | 13 | 10 | 18 | 1 | 358 | 147 | 40,3 | 10,2 s |
| IR | 41 | 12 | **0** | 10 | 19 | **14** | 95 | 146 | 45,0 | 11,4 s |
| REUSE | 52 | 11 | 13 | 10 | 18 | 2 | **46** | 149 | 35,6 | 9,0 s |
| REUSE+NBR | 52 | 11 | 13 | 10 | 18 | 1 | 56 | 147 | 35,5 | 9,0 s |
| REUSE+DEP | 53 | 12 | 13 | 10 | 18 | 1 | 65 | 147 | 35,1 | 8,8 s |
| **REUSE+HINT** | 53 | 12 | 13 | 9 | 19 | 1 | 70 | 141 | **33,5** | **8,4 s** |

Avvikelser mot FULL:

| Arm | Tappade | Vann |
| --- | --- | --- |
| IR | 15 (alla op-ändringar plus två till) | P030, P034, P041 |
| REUSE | P038 | – |
| REUSE+NBR | P000 | – |
| REUSE+DEP | **inga** | – |
| REUSE+HINT | P033, P043 | P030, P034 |

### Qwen2.5-Coder-3B-Instruct Q4_K_M

| Arm | Korrekta | const/14 | op/13 | default/13 | kontroll/20 | Inaktuella | Prompttokens | Genererade tokens | Avklippta vid 256 | CPU-s per korrekt | Väggtid per korrekt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FULL | 34 | 7 | 6 | 5 | 16 | 0 | 358 | 179 | 23 | 150,3 | 38,6 s |
| IR | 32 | 10 | **0** | 8 | 14 | **11** | 95 | 166 | 12 | 130,2 | 33,0 s |
| REUSE | 36 | 8 | 9 | 4 | 15 | 0 | **46** | 180 | 23 | 124,6 | 31,6 s |
| REUSE+NBR | 36 | 8 | 7 | 6 | 15 | 0 | 56 | 179 | 23 | 124,6 | 31,6 s |
| REUSE+DEP | 35 | 8 | 6 | 5 | 16 | 0 | 65 | 179 | 23 | 130,7 | 33,2 s |
| **REUSE+HINT** | **41** | 10 | 10 | 4 | 17 | 0 | 70 | **161** | **17** | **100,1** | **25,4 s** |

Korrekta bland svar som *inte* klipptes av:

| Arm | Korrekta | Andel |
| --- | ---: | ---: |
| FULL | 33/37 | 89 % |
| IR | 31/48 | 65 % |
| REUSE | 35/37 | 95 % |
| REUSE+NBR | 35/37 | 95 % |
| REUSE+DEP | 34/37 | 92 % |
| REUSE+HINT | 41/43 | 95 % |

## Tolkning

1. **H5 klarar det svårare falsifieringsprovet.** X3a:s begränsning var att uppgiften bara krävde citat. Nu kräver uppgiften resonemang om hur en ändring påverkar oförändrade rader, och KV-tillstånden för dessa rader beräknades i den gamla kontexten.
   - Inaktuellt KV-tillstånd ger ändå högst +1 inaktuellt svar.
   - Det slår inte heller mätbart på kvaliteten, varken på 1.5B eller 3B.
   - Genom kvarvarande rader i cachen ser modellen ändringen via uppmärksamheten.
2. **IR (att modellen själv tillämpar en PATCH) faller när ändringen är semantisk.** Operatorändringar gav 0 av 26 korrekta över båda modellerna, och svaret var nästan alltid den gamla versionens utskrift. Det skärper X2:s slutsats:
   - ENIGMA-IR som *modellindata* fungerar för lokalisering och citat.
   - Den fungerar inte när modellen måste resonera över den ändrade koden.
   - Den hållbara samdesignen är att codec-strukturen styr *beräkningen*, alltså vilka KV-tillstånd som återanvänds, i stället för att codec-texten läses som tokens.
3. **Båda korsningarna fungerar, men på olika sätt.**
   - **REUSE+DEP (H4 × H5)** är den mest *konservativa* armen. Den tappade inte en enda uppgift som FULL klarade på 1.5B och hade 0 inaktuella svar på 3B. Den deterministiska beroendeanalysen gör alltså det den ska. Men den kostar lite mer än REUSE och gav inte fler korrekta svar.
   - **REUSE+HINT (X2 × X3a)** ger *mest vinst*. Den återanvänder KV-tillstånden *och* ger modellen en kort deterministisk notis om vad som ändrats. Det har två effekter:
     - **Bättre fokus:** 3B löste 41 uppgifter mot FULL:s 34.
     - **Kortare genererad text:** 161 tokens mot 179 på 3B, och färre spårningar klipptes av.
   - Ändringsnotisen ersätter en del av modellens eget sökande efter vad som skiljer versionerna åt. **Det är det första fyndet i serien där ENIGMA-strukturen minskar *genereringen* och inte bara prompten.**
4. **Genereringen dominerar nu kostnaden.** Prompten krymper från 358 till 46–70 tokens, men CPU-vinsten stannar vid 12–33 %, eftersom 140–180 genererade spårningstokens är en fast kostnad. Nästa stora vinst ligger alltså i att korta ned eller strukturera utdata, inte i att komprimera indata ytterligare.

## Avvikelse och begränsningar

- **Taket på 256 genererade tokens slog igenom på 3B.** Taket var förhandsregistrerat (`max_new=256`). 3B skriver längre spårningar och klipptes av i 23 av 60 FULL-svar, så nästan alla de svaren blev fel.
  - De absoluta 3B-talen är därför lägre än modellens förmåga, och FULL drabbas lika hårt som REUSE-armarna.
  - Beslutet påverkas inte. Bland svar som inte klipptes av ligger REUSE-armarna i nivå med eller över FULL.
  - En del av HINT-fördelen på 3B kommer av att HINT ger kortare spårningar och därmed färre avklippta svar. Även bland svar som inte klipptes av är HINT i nivå med de bästa armarna, 95 %.
  - 1.5B klipptes inte av (0 av 60 för FULL), så de talen är rena.
- Syntetiska program och en uppgiftsfamilj. Skillnader på 1–2 uppgifter av 60 ligger inom bruset. HINT:s +7 på 3B är det enda stora utslaget, och det är delvis sammanflätat med trunkeringen.
- CPU-sekunder i en delad molncontainer, inte joule. Bara llama.cpp, och KV-redigeringen bygger på K-shift och parkeringssekvens. Målhårdvaran RX 9060 XT är inte prövad.
- Facit kommer från körning. I en verklig agent är körningen själv det billigaste och exakta svaret (LEAN). Testet mäter modellförståelse under förändring.

## Konsekvenser (förslag, kräver beslut)

- **Runtime-kandidaten uppdateras från `REUSE+NBR` (X3a) till `REUSE+HINT`.**
  - Ändringsnotisen härleds deterministiskt ur PATCH-operationerna och kräver ingen modell.
  - `REUSE+DEP` behålls som konservativt läge för ändringar där fel svar är dyra.
- **ENIGMA-IR som modellindata bör begränsas** till lokaliserings- och citatuppgifter. Den ska inte användas när modellen ska resonera över ändringens konsekvenser.
- **Föreslagna nästa experiment:**
  - **X4b:** 3B med `max_new=512`, registrerad som separat körning, för att få rena 3B-tal.
  - **X5:** riktar in sig på den genererade texten, som nu är den dominerande kostnaden. Hypotesen är att strukturerad eller inkrementell spårning minskar genereringen utan att kvaliteten tappar. Exempel:
    - spåra bara funktioner som berörs av ändringen
    - återanvända den gamla versionens spårning och bara räkna om de steg som berörs
  - Ingen träning är motiverad av X4 enligt R7.
