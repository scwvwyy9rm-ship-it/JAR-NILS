# INV-2026-11-21-X2 – Resultat

**Körd:** 2026-11-21 i en isolerad molncontainer: 4 vCPU, llama-cpp-python 0.3.16, 4 trådar, en körning i taget.
**Protokoll:** [PREREG.md](PREREG.md), committat före huvudkörningen. Rådata finns i `x2_res_1.5b.json` och `x2_res_3b.json`, riggen i `run_x2.py` och uppgifterna i `x2_tasks.json`.

## Beslut enligt förhandsregistrerad regel

> **Representationskaskaden (D): GO för fortsatt utredning, båda modellerna.**
> 1. D har lägre CPU-s per korrekt uppgift än A och B: 1.5B 20,2 mot 49,1 / 27,4; 3B 15,8 mot 71,9 / 39,4.
> 2. D löser lika många uppgifter som B (31 = 31; 40 = 40) och har **noll** inaktuella svar.
>
> **Viktigare fynd:** Det är **ENIGMA-IR i sig** (arm C) som ger vinsten, inte kaskaden. På 1.5B gjorde eskaleringen D dyrare än C utan att rätta ett enda fel.

## Resultat (40 uppgifter per modell, 20 ändrade, 20 oförändrade)

### Qwen2.5-Coder-1.5B-Instruct Q4_K_M

| Arm | Korrekta | Ändrad | Oförändrad | Inaktuella | Beräknade tokens per uppgift | CPU-s per korrekt | Väggtid per korrekt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A RAW, ingen cache | 31 | 18 | 13 | 0 | 1 414 | 49,1 | 12,9 s |
| B RAW + cache | 31 | 18 | 13 | 0 | 657 | 27,4 | 7,1 s |
| **C ENIGMA-IR + cache** | 31 | **19** | 12 | 0 | **187** | **12,2** | **3,1 s** |
| D kaskad | 31 | 19 | 12 | 0 | 350 | 20,2 | 5,2 s |

Kaskaden eskalerade 9 gånger. Ingen eskalering rättade svaret, eftersom samma uppgifter också misslyckades i RAW-armarna: felen beror på modellen och inte på representationen. Missade återhämtningar: 0.

Uppgifter med olika utfall mellan B och C/D:
- **T015** (ändrad): rätt med IR, fel med RAW.
- **T031** (oförändrad): rätt med RAW, men med IR svarade modellen med hela flerradssignaturen ihopslagen på en rad, så svaret räknades som fel. Svaret var inte inaktuellt.

### Qwen2.5-Coder-3B-Instruct Q4_K_M

| Arm | Korrekta | Ändrad | Oförändrad | Inaktuella | Beräknade tokens per uppgift | CPU-s per korrekt | Väggtid per korrekt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A RAW, ingen cache | 40 | 20 | 20 | 0 | 1 414 | 71,9 | 19,2 s |
| B RAW + cache | 40 | 20 | 20 | 0 | 657 | 39,4 | 10,4 s |
| **C ENIGMA-IR + cache** | 40 | 20 | 20 | 0 | **187** | **15,8** | **4,1 s** |
| D kaskad | 40 | 20 | 20 | 0 | 187 | 15,8 | 4,1 s |

Kaskaden eskalerade aldrig. Missade återhämtningar: 0.

## Tolkning

1. **ENIGMA-IR (PATCH mot en cachad tidigare version) är ungefär 2,2–2,5 gånger billigare per korrekt löst uppgift än den skarpa baslinjen B, utan uppmätt kvalitetsförlust.** Modellerna är inte tränade på formatet. De fick bara en tre raders förklaring i systemprompten.
2. **Kvoten mellan beräknade tokens (3,5×) och CPU-tid (2,2–2,5×) skiljer sig,** eftersom genereringen och frågan är fasta kostnader. Vinsten bör växa med större utdrag och mindre ändringar.
3. **Kaskaden ger en garanti men ingen kostnadsvinst här.** Den kostar bara något när modellen redan är osäker. Värdet ligger i att fel som beror på representationen kan återhämtas. Den här uppgiftstypen producerade inga sådana fel, så den nyttan är **inte prövad**.
4. **Inga inaktuella svar** i någon arm. Risken att modellen citerar den gamla raden efter en PATCH syntes inte i den här uppgiftstypen.

## Begränsningar som begränsar slutsatsen

- **En enda, enkel uppgiftstyp** (citera en signaturrad). Verifieraren är nästan lika stark som facit. Resultatet säger inget om uppgifter som kräver resonemang om ändringens konsekvenser.
- **Inte joule.** CPU-sekunder på delad moln-CPU. Ingen överföring till RX 9060 XT eller till Compact Ensemble-bindningarna.
- **ENIGMA Hybrid-armen saknas.** Den kördes inte, trots att `LocalProgrammer` nu är tillgängligt i sessionen, eftersom protokollet låstes utan den.
- 40 uppgifter per modell. Skillnader på 1–2 uppgifter är inom bruset.

## Rekommendation (kräver beslut)

- Pröva ENIGMA-IR PATCH som **modellindata** mot cachad tidigare version på verkliga agentuppgifter med testbaserad verifiering, och på målhårdvaran med energimätning.
- Lägg till ENIGMA Hybrid som arm och en uppgiftstyp med resonemang över ändringar, där kaskadens återhämtningsvärde faktiskt kan prövas.
