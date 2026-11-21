# INV-2026-11-21-X3 – Resultat (X3a körd, X3b inte körd)

**Körd:** 2026-11-21 i en isolerad molncontainer: 4 vCPU, llama-cpp-python 0.3.16 med två KV-sekvenser i en gemensam buffert.
**Protokoll:** [PREREG.md](PREREG.md). Rigg i `run_x3a.py` och självtest i `x3a_selftest_1.5b.json`. Rådata finns i `x3a_res_1.5b.json` och `x3a_res_3b.json`.

## Beslut enligt förhandsregistrerad regel

> **H5 – GO (deterministisk), båda modellerna. X3b startas inte.**
> Regel 1 är uppfylld. REUSE har ≥ FULL − 1 korrekta (1.5B: 36 mot 37; 3B: 40 mot 40) och beräknar färre tokens än IR (118 mot 193 per uppgift).
> Strukturstyrd KV-återanvändning fungerar alltså **utan träning** för den här uppgiftstypen. Enligt R7:s princip finns då inget mätt gap som motiverar att träna N0. Träningsgodkännandet används inte, och X3b står kvar som registrerad men ej utförd.

## Självtest (godkänt före huvudkörningen)

| Kontroll | Resultat |
| --- | --- |
| Omberäkning av alla rader via KV-redigering mot FULL | max |Δlogit| = 0,0, samma argmax |
| Infoga en rad på nytt via parkeringssekvens | max |Δlogit| = 0,0, samma argmax |
| Flytta cache +5 positioner (RoPE K-shift) mot direkt evaluering på +5 | max |Δlogit| ≈ 0,57–0,69, samma argmax. Samma storleksordning som positionsberoendet i sig (0,43–0,69) |

## Resultat (40 uppgifter per modell)

### Qwen2.5-Coder-1.5B-Instruct Q4_K_M

| Arm | Korrekta | Ändrad | Oförändrad | Inaktuella | Beräknade tokens per uppgift | CPU-s per korrekt | Väggtid per korrekt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FULL | 37 | 19 | 18 | 0 | 659 | 20,7 | 5,46 s |
| IR | 30 | 19 | 11 | 0 | 193 | 12,9 | 3,29 s |
| **REUSE** | 36 | 19 | 17 | 0 | **118** | **9,0** | **2,27 s** |
| REUSE+NBR | **37** | 19 | **18** | 0 | 156 | 9,6 | 2,43 s |

Avvikelser mot FULL:
- **IR** missade 7 uppgifter som FULL klarade, alla oförändrade: T011, T014, T019, T030, T031, T033, T034.
- **REUSE** missade 1: T033.
- **REUSE+NBR** missade inga.

### Qwen2.5-Coder-3B-Instruct Q4_K_M

| Arm | Korrekta | Inaktuella | Beräknade tokens per uppgift | CPU-s per korrekt | Väggtid per korrekt |
| --- | ---: | ---: | ---: | ---: | ---: |
| FULL | 40 | 0 | 659 | 34,6 | 9,23 s |
| IR | 40 | 0 | 193 | 15,4 | 3,98 s |
| **REUSE** | 40 | 0 | **118** | **13,5** | **3,40 s** |
| REUSE+NBR | 40 | 0 | 156 | 15,5 | 3,95 s |

## Tolkning

1. **H5 bekräftas deterministiskt.** När den byteexakta PATCH-strukturen styr vilka KV-tillstånd som återanvänds får modellen den aktuella versionen till ungefär 18 % av FULL:s beräknade tokens och 26–44 % av FULL:s CPU-tid per korrekt uppgift.
2. **REUSE är både billigare och robustare än IR.** Med IR måste modellen *tillämpa* patchen själv, och den svagare 1.5B-modellen tappade då 7 av 20 oförändrade uppgifter. Med REUSE *ser* modellen den färdiga aktuella versionen, utan att den behöver beräknas om, och kvaliteten ligger kvar på FULL-nivå.

   **Det här är det tydligaste beviset hittills för ADR-ENC-001:s samdesigntes:** codec-strukturen (PATCH/COPY) och modellens beräkning (KV-cachen) kopplas ihop, i stället för att codec-texten bara skickas som tokens.
3. **Selektiv omberäkning av grannrader** (REUSE+NBR) återvann den enda förlorade uppgiften på 1.5B, till 32 % högre tokenkostnad än REUSE. På 3B gav den ingenting. Den deterministiska motsvarigheten till CacheBlend räcker alltså. Ingen inlärd komponent behövdes.
4. **Inaktuellt KV-tillstånd** i kopierade rader, som beräknades i den gamla kontexten, orsakade inga mätbara fel för den här uppgiftstypen.

## Observation utanför protokollet (ska inte tolkas som resultat)

FULL i X3a (37/40 på 1.5B) gick bättre än B i X2 (31/40). Skillnaden är att X2:s B hade både den gamla *och* den nya versionen i kontexten. Det tyder på att två nästan identiska versioner i samma kontext kan förvirra en liten modell. I så fall är det ytterligare ett argument för att ersätta versioner i stället för att lägga till dem, vilket REUSE gör. Hypotesen är inte förhandsregistrerad. Promptformaten skiljer sig också något, eftersom X3a tokeniserar radvis.

## Begränsningar

- **En uppgiftstyp:** citat av signaturrader. Inaktuellt KV-tillstånd påverkar troligen uppgifter som kräver resonemang om ändringens konsekvenser mer. GO gäller bara denna uppgiftstyp.
- **llama.cpp-specifikt:** KV-redigeringen bygger på K-shift och en parkeringssekvens. Andra backends, och ROCm på RX 9060 XT, är inte prövade.
- CPU-sekunder i en delad molncontainer, inte joule.
- Kopierade rader återanvänds på radnivå. COPY-spann inom rader och mellan olika filer är inte prövade.

## Konsekvenser (förslag, kräver beslut)

- **Neural Core-spåret bör inte träna en modell för KV-robusthet nu.** Den deterministiska mekanismen räcker, i linje med R7.
- **Arkitekturspåret:** KV-återanvändning styrd av ENIGMA PATCH/COPY bör utredas som runtime-funktion, med verifiering mot verkliga agentuppgifter och målhårdvara. Kandidaten är `REUSE+NBR`.
- **Nästa falsifieringsprov för H5:** en uppgiftstyp där ändringen påverkar tolkningen av oförändrade rader, till exempel ett omdöpt namn som används längre ned. Där borde inaktuellt KV-tillstånd synas. Först om det provet visar ett gap blir X3b motiverad.
