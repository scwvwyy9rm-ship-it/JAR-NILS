# JAR-NILS Workspace — terminal UI and product development

**Development update · 7 November 2026**  
**Status: active development, not a software release**

JAR-NILS is moving from a collection of local AI and agent capabilities toward a coherent desktop product. The immediate priority is **Local Developer**: a local-first programming assistant whose work remains bounded by task contracts, operator decisions and verifiable checks.

## Native Workspace UI v0.4

The new **Terminal Design System** has been implemented on a development branch of the native Tkinter Workspace ([private implementation PR #335; details summarized here publicly]). Actual UI test screenshots were captured on 7 November. These are **real screenshots of implemented interface code**, not AI-generated concept art.

The Workspace now has five visual themes: **Terminal Green** (default), **Amber**, **Nordic Light**, **Midnight Purple** and **Teal**. It uses a consistent monospace visual language, revised three-column layout, a numbered main menu with Alt+1…7 shortcuts, improved tab/button states and a status strip.

The screenshots were captured with **Demo/Mock** data. That describes the task, model and capability *data shown inside the interface*; it does not mean the UI itself is a concept mockup. The interface implementation and its connection to all live workflows are separate milestones.

**Verification reported for the UI branch:** 155 targeted tests passed; the wider test run reported no new failures compared with the same Linux baseline. Windows acceptance, display scaling and CI were still outstanding at this checkpoint. The UI PR was **open and in draft** when this update was prepared.

> **Screenshot publication:** Six original PNG screenshots (five themes, plus a compact 1024×680 Terminal Green capture) are ready for publication. The image files will be added to this public repository separately; the descriptions in this document do not imply that the image assets are already hosted here.

## Product development: Local Developer

Recent changes merged into the private implementation's main branch include:

- A **metadata-based verification receipt** for Local Developer runs: a step toward reporting *what was tested and against which change*, rather than trusting the model's self-assessment.
- A clearer **native startup readiness view** for the local model and environment.
- A **passive Resume preview**: viewing a saved checkpoint does not itself grant permission to resume or change files.
- Consistent user-visible **JAR-NILS** naming.

Further work remains in development branches, including a native tab to display Local Developer runs and receipts, a read-only task card reviewed before starting work, and cooperative stop handling. These should **not** be presented as shipped or fully integrated features.

## ENIGMA: implementation, research and measured results

ENIGMA is JAR-NILS' own architecture and research direction for structured, bounded information exchange between local models and supporting tools. It is separate from the longer-term exploration of training an original small language model. **No JAR-NILS-native language model has yet been trained and validated.**

### Implemented in the private development main branch

On **6 November 2026**, an **opt-in** hybrid projection for chat and a bounded WEB context bridge for `/agent` were merged. The bridge lets the agent use a size-limited, source-bound excerpt after a current-run WEB fetch and requires citations to the verified original source. These paths retain existing permissions and security checks. **ENIGMA is off by default** and these merges do not amount to a finished commercial feature or a general performance improvement.

### Research results: useful evidence, not yet a proven speedup

A separate, **unmerged research draft** (EV1-M-HR) removed three redundant outer metadata copies from WEB context serialization while retaining the underlying provenance and citation checks. Across 12 offline baseline/candidate pairs, the measured serialized request size fell by **369 bytes per WEB source** (738 bytes with two sources). This measures **serialized JSON size only**, not model tokens, network traffic, latency, GPU load or energy use.

Another **unmerged**, real-local-model experiment comparing the earlier ENIGMA WEB candidate with raw context on small fact-retrieval tasks found **slower** median execution with ENIGMA: approximately **58% slower for short** and **32% slower for long** fixtures. Its reported model prompt-token totals were also higher in those tests. These findings do not establish general results for other tasks, but **they do not support claiming a resource advantage at this stage**. The newer metadata-size experiment did not demonstrate that this regression was resolved.

### Forward research: ENIGMA Evolution and Native Model N0

A **draft documentation handoff** outlines two separate first steps:

- **ENIGMA Evolution EV0:** catalogue existing components, examine metadata/context overhead, reuse available selectors and decide on bounded deterministic optimization experiments.
- **Native Model N0-F0:** draft a protocol, map it to the existing planner/decision schema and design simulator, dataset, small-model and training-environment options before authorizing training.

These are **research/design proposals**, not new active product features, validated savings or approval to train a model.

Related development includes a source-linked chat/project memory validator and an expanded frozen routing evaluation suite (**339 generated cases**); both were still in separate, unmerged development work as of **7 November 2026**.

**Bottom line:** ENIGMA's implementation has advanced, and the experiments are becoming more measurable. The near-term product remains Local Developer; research results are evaluated separately rather than presented as proven commercial capabilities.

## Why it matters

JAR-NILS is being built around **digital agency**: useful AI on a user's own machine, clearer control of data and permissions, and verifiable, reversible actions wherever the underlying workflow supports them.

The near-term goal is straightforward: an external user should be able to **install, understand, use and evaluate** a focused local programming assistant. Product validation and real user feedback come before claims of commercial readiness.

**Project:** [JAR-NILS](https://github.com/scwvwyy9rm-ship-it/JAR-NILS) · **Founder:** Christoffer Runnholm  
**Voluntary support:** [Ko-fi](https://ko-fi.com/jarnils) · [Buy Me a Coffee](https://www.buymeacoffee.com/jarnils)

*This public repository is the project overview; the implementation source is maintained separately. No public release, finished product or general security guarantee is implied.* 
