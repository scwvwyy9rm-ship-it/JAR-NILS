# Research – JAR-NILS

Det här avsnittet är JAR-NILS löpande forskningslogg för **resurssnåla, lokala AI-agenter**. Varje veckorapport arkiveras som en separat Markdown-fil och kan följas upp med mätbara lokala experiment.

## Omfattning

- Selektiv kontext, kontextkomprimering och ENIGMA Core
- Routing mellan modeller, verktyg och beräkningsvägar
- Kvantisering och minnes-/kvalitetsavvägningar
- CPU/GPU-delning, RAM/VRAM och latens
- Energiförbrukning **per framgångsrikt löst uppgift**, inte bara per token

## Rapporter

Startomgång 21 november 2026. Ordinarie rapporter publiceras på fredagar kl. 17.00 svensk tid. Varje rapport avser **enbart nya artiklar, tekniska rapporter eller benchmarkresultat publicerade under de föregående sju dagarna**. Om inget relevant nytt material hittas ska det framgå uttryckligen.

| Vecka | Rapport |
| --- | --- |
| 2026-11-21 (extra startomgång) | [Första forskningsrapporten](2026-11-21.md) |
| 2026-11-21 (repo-koppling) | [Forskning ↔ befintliga JAR-NILS-spår](2026-11-21-repo-crosswalk.md) |
| 2026-11-21 (innovationstest) | [Veckans forskning mot ENIGMA Native Architecture](2026-11-21-innovationstest-enc.md) |

## Filformat

Spara varje körning i `Research/YYYY-MM-DD.md` (datum i svensk tid). Varje rapport bör innehålla:

1. **Bevakningsperiod** och kort sammanfattning.
2. **Nya fynd**, med publiceringsdatum, direktlänkar till originalkällor, vad som faktiskt mätts och viktiga begränsningar.
3. **Relevans för JAR-NILS/ENIGMA Core**, inklusive kompromisser i uppgiftsframgång, kvalitet, latens, RAM/VRAM, energi och implementationskostnad.
4. **Högst tre experiment att pröva**, prioriterade och med mätvärden, baslinje samt acceptanskriterier.
5. **Osäkerheter**: skilj verifierade mätresultat från preprints, författarpåståenden, tredjepartsbenchmark och egna hypoteser.

Förändra inte produktionskod, modellkonfiguration, hårdvarubeslut eller säkerhetspolicy baserat på forskningsrapporterna. Sådana ändringar kräver separat utvärdering och uttryckligt godkännande.

Rapporterna är forskningsunderlag, **inte** automatiskt godkända tekniska beslut.
