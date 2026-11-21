# INV-2026-11-21-X1 – Resultat

**Körd:** 2026-11-21 i en isolerad molncontainer (4 vCPU, Python 3.13, zstd 1.5.5, xdelta3 3.0.11, xz/liblzma).
**Protokoll:** [PREREG.md](PREREG.md), committat före körningen. Rådata finns i [results.json](results.json), negativa tester i [negativa-tester.json](negativa-tester.json), och codec och rigg i `crg.py`, `run_x1.py`, `neg_tests.py` och `build_corpora.py`.

## Beslut enligt förhandsregistrerad regel

> **H1 – NO-GO för ENIGMA-CRG v0 som lagrings-/transportcodec.** Ingen av operationerna COPY, PATCH eller TEMPLATE ger ≥ 5 % lägre storlek än bästa baslinje i R2 på någon korpus. Alla tre stryks ur CRG-v0 som *lagringsformat*.
> **Reservation:** Den förhandsregistrerade baslinjen ENIGMA Lines/Delta/Hybrid kunde inte köras, eftersom `LocalProgrammer` inte var tillgängligt. NO-GO gäller jämfört med etablerade kompressorer. Huruvida CRG v0 är bättre eller sämre än dagens ENIGMA är **inte prövat**.

## Korrekthet (godkänd)

- **Byteexakt rundtur:** 320 + 203 + 671 = 1 194 objekt × 4 varianter. Alla `D(C(x,H),H) == x`.
- **Negativa tester:** 13/13 avvisades med verifierbart fel: manipulerad H-hash, saknad eller framtida referens, cykel via eget cid, trunkering, manipulerad nyttolast, fel magic, okänd operation, COPY utanför källa, självkopia framåt, två expansionsbudgetfall, felaktig PATCH-täckning och okänd mall.
- **Exakta rundturer** med whitespace/CRLF, ogiltig UTF-8, negation och NUL-byte: godkända för alla operationer.
- **Fel som verifieringen fångade under utvecklingen:** Den första avkodaren avvisade giltiga överlappande självkopior, och röktestet stoppade körningen. Felet rättades till standardsemantiken för LZ77-överlapp innan huvudkörningen.

## R2 inkrementell (primär): byte för att lägga till nya objekt givet H

Procent anger skillnad mot bästa baslinje; lägre är bättre.

| Arm | K1 loggar (4,46 MB) | K2 kodversioner (10,20 MB) | K3 agentsession (12,39 MB) |
| --- | ---: | ---: | ---: |
| **zstd19 + historik som ordlista** | **348 852 (bäst)** | **124 613 (bäst)** | **457 683 (bäst)** |
| xdelta3 mot bas | 608 227 (+74 %) | 184 747 (+48 %) | 976 761 (+113 %) |
| TPL-kolumn (CLP-lik) | 451 123 (+29 %) | 587 507 (+371 %) | 1 087 311 (+138 %) |
| zstd19 per objekt | 536 436 (+54 %) | 2 392 858 (+1 820 %) | 3 259 548 (+612 %) |
| CRG{COPY} | 638 307 (+83 %) | 215 947 (+73 %) | 1 399 726 (+206 %) |
| CRG{PATCH} | 576 253 (+65 %) | 186 333 (+50 %) | 1 909 192 (+317 %) |
| CRG{TEMPLATE} | 500 780 (+44 %) | 696 996 (+459 %) | 1 337 213 (+192 %) |
| CRG{ALL} | 502 629 (+44 %) | 184 795 (+48 %) | 1 373 578 (+200 %) |

## R1 arkiv (sekundär, avgör inte)

| Arm | K1 | K2 | K3 |
| --- | ---: | ---: | ---: |
| xz -9e | **303 960** | **113 228** | 388 224 (+43 %) |
| zstd19 --long=27 | 330 635 (+9 %) | 118 189 (+4 %) | 437 171 (+61 %) |
| TPL-kolumn (CLP-lik) | 329 400 (+8 %) | 141 187 (+25 %) | **272 060** |
| CRG{PATCH} | 354 139 (+17 %) | 122 417 (+8 %) | 520 911 (+91 %) |
| CRG{ALL} | 381 163 (+25 %) | 122 976 (+9 %) | 846 381 (+211 %) |

## Sekundärt: modellsynliga tokens (Qwen2-tokenizer, textrendering av CRG{ALL})

| | K1 | K2 | K3 |
| --- | ---: | ---: | ---: |
| RAW | 2 355 972 | 2 242 506 | 3 856 372 |
| CRG{ALL}-rendering | 2 084 761 (−12 %) | **136 801 (−94 %)** | 2 523 330 (−35 %) |

Tokenantal är **inte** modellförståelse. Det är just det som X2 prövar.

## Tolkning

1. **CRG v0 slår inte zstd med historik.** COPY och PATCH tar bort långa upprepningar, men det kvarvarande entropikodas utan historikkontext. zstd med historik som ordlista gör båda delarna i ett steg. Att explicit återuppfinna LZ77 eller delta-kodning ovanpå zstd ger ingen lagringsvinst här.
2. **Den bästa kända principen för agentdata är kolumnär mallkodning, alltså CLP-liknande.** I R1 på K3 slog den xz med 30 %. Det är etablerad teknik och inte en ENIGMA-innovation. Om ENIGMA behöver ett lagringsformat för verktygsutdata och loggar bör man börja där.
3. **Presentation förstör struktur.** PATCH blev mycket sämre på K3 (+317 %) eftersom numrerade filläsningar ändrar *varje* radnummer när en rad infogas. Det bekräftar radankarproblemet från tidigare ENIGMA-arbete. **Designinsikt:** lagra innehållet utan presentationsartefakter och rendera radnummer vid utläsning.
4. **Det verkliga signalvärdet finns på modellsidan.** Som modellindata krymper kodversioner 94 % i tokens med exakt verifierbar rekonstruktion. Om modeller kan använda den representationen korrekt, vilket X2 prövar, kan kostnadsvinsten ligga där och inte i byte. Det överensstämmer med ADR-ENC-001 princip 3: lagringskodning och modellbegriplig representation är olika gränssnitt.

## Konsekvens för ENIGMA-forskningen (förslag, kräver beslut)

- **Stryk CRG v0 som eget lagringsformat.** Använd etablerade kompressorer (zstd med historik, CLP-lik kolumnkodning) för lagring och transport.
- **Behåll COPY/PATCH som modellrepresentation** (ENIGMA-IR), med X2 som avgörande prov.
- **Ej förregistrerad följdhypotes:** CRG-operationer följda av zstd *med historik* kan kombinera båda fördelarna. Det ska förhandsregistreras separat innan det prövas.
- Kör ENIGMA Lines/Delta/Hybrid-baslinjen när `LocalProgrammer` är tillgängligt, så att reservationen kan stängas.

## Begränsningar

- Python-prototyp. Codec-tiderna (CRG{ALL}: 5–14 s kodning, ≤ 0,5 s avkodning per korpus) är inte jämförbara med zstd/xz i C.
- Tre korpusar, varav K3 är simulerad. Konversationskorpus saknas, se avvikelsen i PREREG.
- CRG v0 blandar inte operationer inom ett objekt, och kodaren väljer giriga matchningar. En bättre kodare kan minska skillnaden, men skillnaderna i R2 (+44 % till +200 % för CRG{ALL}) är större än vad det rimligen förklarar.
