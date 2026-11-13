# JAR-NILS — verified work, smaller-model research and Linux groundwork

**Development and research update · 13 November 2026**  
**Status: active development. No public release or original JAR-NILS language model.**

JAR-NILS is an independent local-first AI programming project. The immediate product goal is a programming assistant that can inspect projects, propose and test bounded changes, and show the operator what actually happened. In parallel, ENIGMA research explores efficient representations of context, model-specific behaviour and, longer term, a small specialist model.

This is a public progress report, **not** a release announcement. Results below are based on documented development runs and code/research reviews; experiment branches and locally integrated work should not be confused with merged, generally available features.

## Product development: evidence before approval

Local Developer's verification receipts, clearer model-startup feedback and passive Resume preview were merged into the private implementation main branch on **6 November**. The receipts distinguish tested changes and recorded outcomes from model assertions; they do not grant approval to merge or run code.

A more recent **local, uncommitted integration** combines a fail-to-pass *proof* mechanism with an operator stop path. In the reported development run:

- **186 targeted tests passed** for proof, task, profile, bundle and run behaviour.
- A broader Developer/boundary/model run reported **234 passed, 8 skipped**.
- The full Linux-side run reported **7,054 passed, 126 failed, 205 skipped** versus **7,038 passed, 125 failed, 205 skipped** on its baseline. One additional failure was in an existing clipboard/UI test, outside the changed Developer modules; that does **not** make the full suite green or establish all baseline failures as harmless.
- A task without proof retains its previous digest. `UNPROVEN` and `OPERATOR_STOPPED` do not become `ready_for_review`; proof results remain separate from ordinary test-profile results.

This proof/stop work is **not yet committed, merged or activated**. Further product work must make these checks understandable and accessible to end users, without weakening operator approval and file-scope controls. CI has also had reported startup failures, so local tests must not be described as green GitHub Actions.

## ENIGMA: useful compression, model-specific limits

ENIGMA already has lossless **Lines, Delta and Hybrid** context representation, SHA-256 checks and original-content reconstruction. An opt-in hybrid chat path and bounded, original-source-bound WEB context bridge were merged into the private main branch on **6 November**. **Off remains the default.**

The current compact-model experiments are isolated from the product:

- In a local **11-case × 3-repeat** comparison, `readable_user_v1` used **27–28% fewer prompt tokens** with no loss of previously correct answers for either tested compact model. The unmodified baselines were **24/33** correct for Qwen3.5 9B and **27/33** for Gemma 4 12B.
- `lines_user_v1` and `hybrid_user_v1` each lost three correct answers per model, reproducibly on a line-reference case. Compression can remove context that a model needs to answer correctly.
- A separately reported `anchored_user_v3` comparison found **no regressions for Gemma 4 12B and the 30B reference across 470 comparisons**, with approximately **15–18% less prompt data in bytes**; Qwen3.5 9B lost ten answers. These are bounded measurements, **not** a universal model ranking or end-to-end speedup.
- A proposed **shadow-only** mode would calculate and validate an ENIGMA projection while still sending the original request to the model. It remains a draft, not an active replacement for the product path.

Earlier real-model WEB-agent comparisons also showed **higher** total latency and prompt-token use with one ENIGMA candidate on small fact-finding tasks. That negative result is retained: **smaller representation does not automatically mean a cheaper or better complete agent run**.

## Enigma Core: a small specialist model is a research direction

The longer-term Enigma Core direction is **not** to claim a trained general-purpose model today. It asks whether a **small, specialised model**, combined with deterministic software, can handle narrow tasks such as structured interpretation, routing proposals, reference selection or error categorisation.

The existing implementation already provides useful foundations:

- A content-addressed, append-only **EvidenceStore** with SHA-256 verification and session-only handling of secret evidence.
- Immutable **evidence records** that preserve source lineage, trust and sensitivity; evidence cannot grant execution authority.
- ENIGMA's existing reversible representations and source-bound checks.

The aim is to **reuse these components**, not build a parallel evidence or memory system.

New **parked research proposals**, with **no training, implementation or activation authorised**, include:

1. **ENIGMA Language Bridge** — evaluate Swedish/English and eventually other Nordic-language instructions, tokenisation costs, negation and meaning preservation. Any language interpretation stays distinct from the exact original and cannot change TaskContract or ScopePolicy permissions.
2. **Lossless storage and entropy coding** — compare established compression methods with current ENIGMA, while distinguishing disk/network bytes from actual language-model tokens. Compression of a bitstream alone does not make it intelligible to an existing model.
3. **Versioning, source integrity and specialist-model experiments** — assess Merkle-style checkpoints and base-version-bound diffs only where they add value beyond existing hash-linked evidence; explore tiny specialist-model prototypes (approximately 5M, 25M and 50M parameters) only after separate research and training decisions.
4. **Protected storage** — study standard authenticated encryption for sensitive archives and memory. Hashing is not encryption; encrypted or compressed content must be decoded in an authorised process before a model can use it. Compression side channels and key management need their own threat model.

These are research hypotheses, not available product capabilities or measured resource savings.

## Linux: a first Workspace integration

A separate Linux track is under development using **Kubuntu and KDE Plasma**. The visual direction for **JAR-NILS Retro Desktop 1.0** is defined, distinct from the Windows-native design.

The first read-only Workspace launcher has been tested in a dedicated Chromium/Chrome application window. The draft implementation reuses the existing Workspace service rather than introducing a second frontend. Tests covered browser lifecycle, profile handling and the local HTTP boundary on Linux/X11. Its focused run reported **123 passed and 1 skipped**; the broader Linux suite still had baseline/environment failures. This work remains a **draft**, with no merge, live agent/HANDS capability or finished Linux application claimed.

The next work concerns local-chat integration, development readiness and careful compatibility checks.

## What comes next

The priority is still to turn the existing foundations into a product that another person can **install, understand, test and use**. Research stays isolated until it demonstrates net value, correct outcomes and preserved safety boundaries. Decisions about new model training, production activation, merges and major spending remain with the operator.

**Public project:** [JAR-NILS](https://github.com/scwvwyy9rm-ship-it/JAR-NILS)  
**Founder:** [Christoffer Runnholm](https://www.linkedin.com/in/christoffer-runnholm-4269a3448/)  
**Voluntary support:** [Ko-fi](https://ko-fi.com/jarnils) · [Buy Me a Coffee](https://www.buymeacoffee.com/jarnils)

*The implementation is maintained separately. Public summaries deliberately omit private source details and do not imply a commercial release, generally proven speedup or complete autonomous development.*
