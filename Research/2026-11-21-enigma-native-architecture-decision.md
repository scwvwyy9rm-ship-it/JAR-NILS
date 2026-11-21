# JAR-NILS – ADR-ENC-001: ENIGMA Native Architecture

**Beslutsdatum:** 2026-11-21  
**Beslutsfattare:** Projektledningen, JAR-NILS  
**Status:** **ANTAGET – strategisk forskningsinriktning**  
**Genomförandestatus:** **EJ GODKÄNT** för implementation, modellträning, produktionskoppling, merge, aktivering eller investering  
**Omfattning:** ENIGMA, ENIGMA Core och ENIGMA Neural Core  
**Dokumenttyp:** Arkitekturbeslut (ADR), forskningsmandat – inte implementationsorder

## 1. Beslut

JAR-NILS antar som långsiktig forskningsinriktning att **utveckla en egen förlustfri komprimeringsalgoritm och en egen språkmodellarkitektur som samdesignas från början**. Syftet är att informationsrepresentation, kodning/avkodning, modellens beräkningar, återhämtning av originalkällor och verifiering ska utgöra en sammanhängande teknisk helhet.

Arbetsnamn för algoritmkandidaten är **ENIGMA-CRG (Causal Reference Grammar)**. Arbetsnamn för den gemensamma representationsspecifikationen är **ENIGMA-IR**. De är hypoteser och utvecklingsmål, inte existerande verifierade produkter.

Följande principer beslutas:

1. ENIGMA Core ska utforska en **egen, deterministiskt avkodningsbar codec** för strukturella mönster, kausala referenser och byteexakta förändringar.
2. ENIGMA Neural Core ska på sikt utformas för att **naturligt tolka samma strukturerade informationsmodell**, i stället för att endast konsumera komprimerad prosa.
3. **Förlustfri lagrings-/transportkodning och modellbegriplig representation är olika gränssnitt**. Modellen kan inte antas förstå ett godtyckligt komprimerat bitflöde; när den behöver dolt originalinnehåll ska det kunna återhämtas och verifieras.
4. Informationsidentitet, proveniens, behörigheter och säkerhetsbeslut ska förbli **deterministiska och externa till modellens slutsatser**.
5. Påståenden om vetenskaplig nyhet, bättre kompressionsgrad, minskad träningstid eller lägre energikostnad är **oprövade tills jämförande, reproducerbara experiment visar det**.

**Detta beslut godkänner forskningsriktningen och framtagandet av specifikationer och beslutsunderlag, men INTE att implementation eller experimentkörningar startar utan separat uttryckligt godkännande.**

## 2. Motivation och nuläge

JAR-NILS befintliga ENIGMA-komponenter omfattar bland annat förlustfri Lines-/Delta-/Hybrid-projektion, byteverifierad rekonstruktion och experimentell kontextselektion. Dessa ger en användbar jämförelsegrund, men betyder inte att någon ny generell komprimeringsalgoritm eller egen tränad Neural Core-modell redan har färdigställts.

Dokumenterade lokala A/B-försök för vissa befintliga ENIGMA-varianter har visat minskad prompttokenförbrukning utan nya fel i avgränsade testfall. Andra försök har visat kvalitetsregressioner eller ökad total svarstid. En minskning av antal byte eller prompttokens **bevisar alltså inte** lägre resurskostnad eller bevarad modellförståelse.

ENIGMA Neural Cores tidigare forskning R0–R9 ska behandlas som bindande empiriskt underlag där den är relevant. I forskningsarkivet har bland annat neural VSC fått **NO-GO**, deterministisk VSC **HOLD**, och R8/R9 klassats som arkitekturhypoteser utan nya verifierade prestandamätningar. R7:s syntetiska kostnadsuppskattningar får inte presenteras som produktionsvinster utan metodrättelse och ny verifiering.

Den nya forskningsriktningen får inte återinföra avfärdade idéer under nya namn utan en materiellt ny hypotes och en förhandsregistrerad falsifieringsmetod.

## 3. Gemensam målarkitektur

Den föreslagna arkitekturen skiljer mellan fem logiska funktioner, inte nödvändigtvis fem nya programmoduler:

1. **Original- och evidenslager:** oföränderliga originalobjekt, hashverifiering, revision, upphov, känslighetsklass och tillåten användning. Återanvänd befintlig EvidenceStore och kontrakt där de räcker.
2. **ENIGMA-CRG codec:** förlustfri kodning med en begränsad, kanonisk grammatik och deterministisk avkodare.
3. **ENIGMA-IR:** versionsbunden, typad mellanrepresentation som kan renderas till codec, modellindata och verifierbara källreferenser utan att skapa en parallell sanningskälla.
4. **ENIGMA Neural Core:** forskningsmodeller som lär sig struktur, relationer, relevant uppslagning, när original behöver begäras och när de ska avstå från obelagda slutsatser.
5. **Verifierings-/exekveringsgräns:** rekonstruktion, källuppslag, aktuell behörighet, TaskContract/ScopePolicy och andra befintliga grindar förblir auktoritativa. Modellens utdata är förslag, aldrig bevis eller rättighet.

### 3.1 Föreslagna kodningsoperationer

| Operation | Betydelse | Obligatorisk egenskap |
| --- | --- | --- |
| `RAW(bytes)` | Bevarar originalbyte | Byteexakt återgivning |
| `COPY(cid, span)` | Återanvänder ett exakt källspann | Källan är versions-/hashbunden och åtkomstkontrollerad |
| `PATCH(cid, edits)` | Beskriver exakta förändringar från en tillåten källa | Deterministisk patch och verifierat slutresultat |
| `TEMPLATE(id, slots, residual)` | Kodar gemensam struktur med varierande fält och byteexakta restdata | Inga borttappade kommentarer, mellanslag, värden eller operatorer |

Denna uppsättning är en **kandidathypotes**. Första experimentet får minska eller ändra operationsmängden om baslinjer visar att en operation saknar nettovärde. Den fasta kontraktsgränsen för byteexakt avkodning får däremot inte försvagas.

### 3.2 Oförhandlingsbara korrekthetsvillkor

För ursprungsdata `x`, kodat innehåll `C(x, H)`, avkodare `D` och en tillåten, versionsbunden källmängd `H` gäller:

```text
D(C(x, H), H) == x     # byte för byte
```

Felaktig källhash, förlorad referens, referenscykel, otillåten proveniens, trasig metadata eller överskriden resursbudget ska leda till verifierbart avslag eller explicit oförändrad RAW-fallback där det är tillåtet. Ingen partiell dekodning får utges för att vara ett komplett original.

En kausal kodning får inte referera till framtida eller ej fastställda objekt. Delade mallar och uppslagskedjor ska ha explicita gränser för djup, expansion, minne och CPU-tid. Kryptografiska hashvärden bevisar dataintegritet, inte faktasanning eller användningsbehörighet.

### 3.3 Modellens informationsgräns

ENIGMA Neural Core får lära sig att **föreslå** referenser, strukturoperationer och återhämtningsbehov. Den får inte själv legitimera ett `cid`, deklarera källmaterial betrott eller åsidosätta extern validering. Om en representation döljer innehåll från modellen måste modellen kunna begära behörig återhämtning innan innehållsberoende slutsatser accepteras.

## 4. Forskningshypoteser

**H1 – Strukturell kompression:** Kombinationen av exakta referenser, förändringskodning och strukturella mallar minskar total kodningsstorlek på förregistrerade agent- och kodkorpusar jämfört med befintliga ENIGMA-varianter och etablerade kompressorer.

**H2 – Modellmedveten kostnad:** Ett val mellan RAW/COPY/PATCH/TEMPLATE som tar hänsyn till faktisk tokenizer, prefixcache, avkodning och uppslagning kan sänka end-to-end-kostnad utan att öka kritiska fel.

**H3 – Samdesignad inlärning:** En liten modell som tränas för ENIGMA-IR kan vid jämförbar parameter-, data- och beräkningsbudget lära sig relevanta struktur-/referensuppgifter effektivare än en matchad byte- eller standardtokenbaslinje.

**H4 – Beroendemedveten blockindelning:** Strukturella beroenden, kodoperatorer och förändringsgränser ger en bättre informationsindelning för programmeringsuppgifter än enbart längd, entropi eller vanliga textradgränser.

Alla hypoteser kan motbevisas. Om en enklare deterministisk lösning ger lika bra eller bättre resultat ska den föredras enligt LEAN/5S-principen.

## 5. Kostnadsmodell och rättvisa jämförelser

Algoritmen ska inte enbart minimera komprimerade byte. Mätningen ska skilja på:

- **Lagring/transport:** nyttolast, headers, kodningskartor, ordlistor, residualer och kostnad för externa referensobjekt.
- **Modellindata:** verkliga tokenizer-tokens och antal positioner som modellen bearbetar.
- **Cache:** återanvända respektive omberäknade prompttokens och effekten av förändrade prefix.
- **Beräkning:** codec-CPU, käll-I/O, modellinferens, verifiering, antal anrop, median/p95-sluttid.
- **Energi/minne:** joule per verifierat löst uppgift där instrumentering är tillförlitlig; VRAM/RAM/SSD-I/O redovisas separat.
- **Träning:** tid, datamängd, minne, omkörningar och träningskostnad, tydligt skild från inferenskostnad.
- **Kvalitet:** verifierade lösta uppgifter och regressioner på negationer, radankare, siffervärden, källidentiteter och säkerhetskritiska begränsningar.

**Primär slutlig jämförelse:** total resurskostnad **per verifierat korrekt löst uppgift**, inklusive misslyckade försök och omkörningar. Tokenbesparing och kompressionsgrad är viktiga delmått, men inte tillräckliga produktionsbevis.

Redovisa separat kall-/varmcache och självständig filkomprimering kontra deduplicering där externa objekt redan finns. Ingen vinst får skapas genom att gömma kostnader i en förutsatt gratis extern ordlista eller store.

## 6. Prioriterad genomförandeplan

| Fas | Prioritet | Leverans | Grind för fortsättning |
| --- | --- | --- | --- |
| A. Inventering | P0 | Versionsbunden korsning mot befintlig ENIGMA-kod, EvidenceStore, R0–R9, tidigare NO-GO och offentligt kända liknande algoritmer | Dubbelarbete och påstådd nyhet identifierade |
| B. Formatkontrakt | P0 | Minimal ENIGMA-IR v0 med exakt avkodningssemantik och negativ testdesign | Kontraktsgranskning och uttryckligt prototypbeslut |
| C. Deterministisk codec | P0 | Isolerat CRG-v0-försök, utan produktionsintegration | Förlustfrihet, korrekt källbindning och resursgränser verifierade |
| D. Algoritmjämförelse | P0 | Fryst jämförelse mot RAW, zstd, dagens ENIGMA Lines/Delta/Hybrid och relevant grammatisk baslinje | Reproducerbar nettovinst på definierade korpusar, eller NO-GO/HOLD |
| E. Modellbegriplighet | P1 | A/B på oförändrade lokala modellbindningar och frysta uppgifter | Ingen ny kritisk regression; faktisk resursvinst uppmätt |
| F. Neural Core N0–N2 | P1/P2 | Separata jämförbara modellprototyper med ENIGMA-IR och byte-/tokenbaslinje | Träningsbehörighet, proveniens, hårdvara och separat körgodkännande |
| G. Utökad modellfamilj | P2 | Bedömning av finjustering/destillering och större modeller | Nytt tekniskt/ekonomiskt investeringsbeslut |

**Notering:** Tabellen är en prioriterad beslutsordning, inte ett automatiskt körgodkännande för någon fas.

### 6.1 Modellstrategi och hårdvara

JAR-NILS utvecklingsdator har rapporterad **AMD RX 9060 XT med 16 GB VRAM**. Forskningsskalorna **N0 cirka 5M, N1 cirka 25M och N2 cirka 50M parametrar** används som preliminära jämförelsepunkter, inte produktkrav. Större modeller (exempelvis 0,5–3B för framtida finjustering eller destillering) kräver egen metod-, GPU/backend- och kostnadsbedömning.

Prioritera små, kontrollerade experiment som kan visa om ENIGMA-IR förbättrar inlärning vid **samma modellstorlek, träningsdata, träningsbudget och låsta tester**. Inga siffror om förväntad speedup eller energivinst får presenteras som mätresultat utan faktisk körning.

### 6.2 Minimikrav på benchmark

- Förregistrerad uppgiftsmängd med syntetiskt och licens-/behörighetskontrollerat material; separata tränings-, validerings- och holdout-mängder.
- Identiska uppgifter, verifierbar baslinje, versionsbundna implementationer och fixerade modellparametrar.
- Flera slumpfrön i neurala försök, rapporterade variationer och samtliga misslyckanden.
- Negativa tester för felaktig källidentitet, manipulerad hash, cykliska referenser, ogiltig UTF-8, exakt whitespace, operator-/negationsförväxling, expansionsattacker och budgetöverskridande.
- Dokumentera både kvalitet och kostnad för fullständig lösning, inte enbart andelen komprimerade byte.
- Bevara ursprungliga mätfiler och rätta metodfel i nya revisionsbundna dokument i stället för att skriva över historik.

## 7. Skyddade gränser och tidigare blockerare

- Befintliga **TaskContract, ScopePolicy, FLOW_POLICY, handlingsgodkännanden, audit, proveniens och verifieringsgrindar** får inte försvagas av en codec eller modell.
- Modellgenererade referenser och sannolikheter får inte utgöra auktorisationsbeslut eller verifierad evidens.
- Befintliga negativa ENIGMA/ENC-experiment kvarstår som historiska resultat. R7:s neural VSC är fortsatt NO-GO i den prövade formen; deterministisk VSC är HOLD. R8/R9 är hypoteser, inte implementationer.
- Öppna frågor kring träningsdata som tillåten mottagare i flödespolicy, reproducerbar träningsproveniens, förfrågningsidentitet, aktuella etiketter och säker återkallelse ska lösas enligt sina egna spår innan berörd körning tillåts.
- Ingen ny parallell EvidenceStore, säkerhetsauktoritet, journal eller generell kompressionsmotor ska införas utan demonstrerad nödvändighet och separat arkitekturbeslut.
- Detta ADR ändrar inte tidigare säkerhetskontrakt och är inte godkännande av neural självförbättring i drift.

## 8. Besluts- och evidensstatus

| Post | Status per 2026-11-21 |
| --- | --- |
| ENIGMA Native Architecture som forskningsmål | **ANTAGET** |
| ENIGMA-CRG:s algoritmiska nyhet / överlägsenhet | **HYPOTES – EJ VERIFIERAD** |
| ENIGMA-IR v0 som formellt kontrakt | **FÖRESLAGET – EJ GRANSKAT** |
| ENIGMA-CRG kod och benchmark | **EJ IMPLEMENTERAT / NOT RUN** |
| N0–N2 med ny representation | **PLANERAD FORSKNING – INGEN TRÄNING GODKÄND** |
| Produktionsaktivering, modellbyte, merge, release | **NO-GO UTAN NYTT UTTRYCKLIGT GODKÄNNANDE** |
| Nya inköp, externa driftåtaganden och utökad budget | **EJ GODKÄNDA** |

**Ansvar:** Forskningsansvarig tar fram falsifierbara hypoteser och källförankrade specifikationer. Kodansvarig granskar konkret återanvändning och tekniska beroenden utan att aktivera något. Budgetfunktionen granskar tids-, energi- och investeringskonsekvenser. Projektledningen ensam tar konsekvensbeslut.

## 9. Veckovis forskningsuppföljning

En separat veckosondering av `JAR-NILS/Research` är beslutad till **fredagar kl. 18.00 Europe/Stockholm**, med första ordinarie tillfälle **2026-11-27**. Den ska bevaka relevant ny forskning, nytt eller ändrat GitHub-underlag, motsägelser till hypoteserna och högst tre prioriterade förslag på små falsifierbara experiment.

Den ordinarie bredare forskningsrapporten kl. 17.00 är en separat bevakning. **Schemalagd granskning innebär inte automatiskt att dokument publiceras, kod ändras, experiment körs eller beslut verkställs.**

## 10. Referensunderlag

- [JAR-NILS Research – index](README.md), [veckorapport 2026-11-21](2026-11-21.md) och [forskningskoppling 2026-11-21](2026-11-21-repo-crosswalk.md).
- [LocalProgrammer – ENIGMA-arbete, issue #240](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/240); [modellbunden A/B, PR #341](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/pull/341).
- [LocalProgrammer – ENIGMA Neural Core, issue #355](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/355); [forskningsarkiv, draft PR #365](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/pull/365).
- Publicerad extern forskning och relevanta originalkällor ska fortlöpande länkas i respektive veckorapport och i experimentens egna beslutsunderlag. Inga externa författarsiffror återanvänds här som JAR-NILS-resultat.

## 11. Slutligt beslut och nästa beslutspunkt

**ANTAGET:** Utveckla ENIGMA som en potentiellt egen, förlustfri och strukturellt medveten komprimeringsprincip, samdesignad med framtida ENIGMA Neural Core och underställd verifierbarhet, LEAN/5S och lokal resurseffektivitet.

**NÄSTA BESLUTSPUNKT:** Separat godkännande av en minimal ENIGMA-IR/CRG-experimentdefinition med frysta baslinjer, negativtest, tydlig resursbudget och redovisad återanvändning av befintlig kod. Varken implementation eller träning får starta genom detta ADR.
