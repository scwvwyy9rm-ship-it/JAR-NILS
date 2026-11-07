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

## ENIGMA and memory research

ENIGMA remains JAR-NILS' own research and architecture track for structured, bounded context between local models and supporting system components. The existing implementation has gained an **opt-in** hybrid context path and a bounded WEB excerpt bridge; both are **off by default**. This is not a claim that JAR-NILS has completed training an original language model, nor proof of general performance or energy gains.

Related draft work explores source-linked chat/project working memory and a larger frozen routing evaluation suite. Those experiments are **not yet active product capabilities**.

## Why it matters

JAR-NILS is being built around **digital agency**: useful AI on a user's own machine, clearer control of data and permissions, and verifiable, reversible actions wherever the underlying workflow supports them.

The near-term goal is straightforward: an external user should be able to **install, understand, use and evaluate** a focused local programming assistant. Product validation and real user feedback come before claims of commercial readiness.

**Project:** [JAR-NILS](https://github.com/scwvwyy9rm-ship-it/JAR-NILS) · **Founder:** Christoffer Runnholm  
**Voluntary support:** [Ko-fi](https://ko-fi.com/jarnils) · [Buy Me a Coffee](https://www.buymeacoffee.com/jarnils)

*This public repository is the project overview; the implementation source is maintained separately. No public release, finished product or general security guarantee is implied.* 
