# JAR-NILS – forskningskoppling till befintliga utvecklingsspår

**Datum:** 2026-11-21 (extra granskning efter [veckans forskningsrapport](2026-11-21.md))  
**Källläge:** utvecklingsrepo `scwvwyy9rm-ship-it/LocalProgrammer`, senaste kontrollerade `main@cc4509450bf5e1d3511c3fd24f6db971308a2cc9` (19 november 2026).  
**Status:** analys och prioriteringsförslag – ingen kod, merge, träning, modellaktivering eller investering godkänd.

> **Avgränsning:** Detta är en övergripande, delbar spårkarta. Känsliga implementationer, detaljer i säkerhetsgranskningar, privat data och opublicerade artefakter från utvecklingsrepot återpubliceras inte här. Länkar till det privata repot kan kräva behörighet. Forskningens siffror är författarrapporterade, inte oberoende reproducerade på JAR-NILS.

## Bekräftat nuläge

- På `main` finns **ENIGMA hybrid** som *opt-in* för förlustfri, byteverifierad projektion. E1/E2 Context Compiler är behörighetsneutral och förblir under existerande admission. Fristående E3-dokumentselektion och shadow-armar finns som experiment, **inte automatiskt aktiverad produktion**.
- **Compact Ensemble v0** har definierade modell-/rollbindningar; offline-A/B och shadow-mätningar är egna experiment. En tidigare E1-körning med identiska prompts i båda armarna kan inte användas för kausal kvalitetsjämförelse.
- **ENIGMA Neural Core (ENC-R0–R9)** är ett separat, parkerat forskningsspår. Forskningsarkivet dokumenteras i **draft PR #365**, ännu inte sammanslaget på `main`. Neural VSC har NO-GO; deterministisk VSC är HOLD. R7:s syntetiska kostnadstal saknar godkänd reproducerbar metodrättelse; R8/R9 är hypoteser, inte implementationsresultat.
- Aktuella produkt-/säkerhetsspår kring verifiering, isolering och release har egna gransknings- och operatörsgrindar. Forskningsförslag får **inte** bredda behörigheter, kringgå dessa grindar eller ersätta dem.
- Skillnad på status: dokumenterat, mätt i författares miljö, observerat i projektets experiment, godkänt för produkt, respektive sammanslaget till `main`.

## Kopplingsmatris (21 november)

| Prioritet | Ny forskning eller metod | Redan befintligt spår | Vad som bör göras – och inte göras |
| --- | --- | --- | --- |
| **P1** | [Timeout Cascades](https://arxiv.org/abs/2611.24324) (18 nov 2026): liten modell först, större modell vid behov; författarna rapporterar upp till 33 % lägre GPU-tidskostnad på coding tasks i sin miljö | Compact Ensemble, routing och befintligt A/B-harness | **Testa en enkel eskaleringspolicy i isolerad mätmiljö först.** Samma uppgifter, total sluttid, verifierade lösningar, antal modell-/verktygsanrop och energi; ingen ny inlärd router eller bindningsändring behövs för hypotesprövningen. |
| **P1** | Selektiv kontext och källåterhämtning, i första hand befintliga ENIGMA-resultat | ENIGMA E3, shadow/anchored, modellbunden A/B, kod- och evidensåterhämtning | **Mät kvalitetsförlust per modell, särskilt negationer, radankare och oförändrade värden.** Undvik ny generell komprimeringsmotor. E1-körning med identiska prompts är metodologiskt ogiltig. |
| **P1** | [Energy Cost of Quantized Agents](https://arxiv.org/abs/2610.32417) (23 okt 2026; **äldre metodreferens, inte nyhetsfynd**) | Befintliga benchmark- och verifieringskvitton | Definiera primärmåttet **joule per verifierat löst uppgift**, med totalt antal försök och misslyckanden. Token/s, token/J eller VRAM ensamma är otillräckliga. Rapportera mätutrustning och CPU/GPU/övrig systemenergi separat. |
| **P2** | [CECAR](https://arxiv.org/abs/2611.20119) (15 nov 2026): expertcache och routing vid SSD-offload | Hårdvaruforskning CPU/RAM/GPU och modellresidens | Kompatibilitetsgranska RX 9060 XT/16 GB och faktisk backend. Först om stöd finns: jämför med dagens oförändrade baslinje, samma modell och kvantisering, mät uppgiftskvalitet, SSD-I/O, VRAM, RAM och total tid. Ingen påstådd AMD-vinst utan mätning. |
| **P2** | [Linglong Agent Service](https://arxiv.org/abs/2611.21129) (16 nov 2026): separerad agentorkestrering och körmiljö | Befintliga TaskContract/ScopePolicy/HANDS, isolering, operatörsgodkännande | **Gör endast gap-analys.** Återanvänd befintliga gränser; en extra HTTP-tjänst eller duplicerad sessionstore är inte motiverad utan tydlig mätbar fördel. |
| **P3** | [EchoMoE](https://arxiv.org/abs/2611.22215) (17 nov 2026): kommunicera komprimerade aktiveringsförändringar i expertparallell MoE | Eventuell framtida fler-GPU-/serverforskning, ENIGMA Core endast som arkitekturjämförelse | **Parkera.** Handlar om kommunikation mellan acceleratorer, inte textprompt/ENIGMA och inte nuvarande en-GPU-konfiguration. |

## Föreslagen testordning – inga körgodkännanden

1. **P1 – Modellbunden kontextkvalitet:** återanvänd frysta ENIGMA-sviter, verifiera att faktiskt insända prompts skiljer sig, mät kvalitetsfall och uppgiftsframgång per modell. *Avbryt vid ny säkerhetsavvikelse; aktivera inte en svagare representation automatiskt.* Mål för vidare utredning: inga ytterligare regressionsfall på förregistrerad kritisk uppgiftsmängd och mätbar minskning av total resurskostnad.
2. **P1 – Liten-modell-först-eskalering:** jämför aktuell fasta modellväg med en experimentell tids-/verifieringsbaserad kaskad; lås samma uppgifter, maxantal försök och modellparametrar. Mät **verifierade godkännanden per timme och joule**, inklusive omkörningar och felslagna fall. Förhandsregistrera stopp/eskalering; ingen ändring i operativa rättigheter.
3. **P2 – AMD-offload, endast om tekniskt möjligt:** kompatibilitetsgrind före inferens. Ingen överflyttning av CECAR:s NVIDIA-/annan hårdvarumätning till AMD. Samma precision och kvalitetsgrind för jämförelser.

## ENIGMA Core – skydda slutsatserna från tidigare forskning

- Neural VSC är stängd som spår i prövad form; deterministisk VSC behöver först verklig behovsmätning och metodrättelse.
- Arkitekturhypoteser i R8/R9 är inte empiriskt verifierade. Ny neural representation får inte utges för att vara byteexakt evidens, behörighetskälla eller färdig minneslösning.
- Negativa experiment och reproducerbarhetsbrister ska kopplas direkt till varje ny forskningshypotes, **så att samma idé inte presenteras som ny under nytt namn**.
- Separata beslut krävs före träning, GPU-test, produktionskoppling, merge och modellbyte.

## Länkar för intern spårbarhet

Utvecklingsrepo (åtkomst kan krävas): [ENIGMA #240](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/240), [Compact Ensemble #340](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/340), [ENIGMA quality backlog #344](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/344), [hårdvara #352](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/352), [ENC #355](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/issues/355), [ENC-arkiv PR #365](https://github.com/scwvwyy9rm-ship-it/LocalProgrammer/pull/365).

**Beslutsläge:** Detta dokument föreslår kopplingar och experiment. Det ändrar inga existerande beslut eller säkerhetsgrindar.
