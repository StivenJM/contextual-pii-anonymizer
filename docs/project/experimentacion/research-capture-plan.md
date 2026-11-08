# Research capture: plan and delivery boundaries

Status: implementation plan, 2026-10-29. This is a second, explicitly enabled workflow, not a replacement for privacy protection. No participant results have been collected by this work.

Implementation is in progress. Do not interpret this plan as institutional approval or completed acceptance of every provider adapter.

## Intended outcome

1. An adult participant receives the study information and explicitly agrees to collection.
2. The researcher enables collection in the local API. In the extension, the participant starts a session on a supported chat tab.
3. Before each supported text submission reaches the commercial chat, the extension durably buffers the exact text locally. Collection does not call the privacy model or converter.
4. The extension records assistant text rendered during that session, distinguishing it from participant submissions. It does not scrape previous conversations or unrelated tabs.
5. On **Finish and save**, capture stops, the remaining visible response is flushed, and the frozen session is uploaded to the API. Failures retain the local copy for retry.
6. The API commits the session and returns an opaque identifier. Repeating the same upload returns the same identifier; conflicting content must not silently overwrite it.
7. The extension shows the confirmed identifier and asks the participant to copy and keep it. A Google Forms response may contain this identifier to link consented background information to the session.
8. Researchers annotate disclosures and evaluate a frozen de-identification model offline, using participant-disjoint training and test sets.

## Two different research questions

| Question | Evidence | Not justified by this evidence |
|---|---|---|
| What identifying information do participants disclose during the tasks? | Consented submitted text, annotations, optional participant confirmation | Whether a participant has manually de-identified information without observing both an original and an edited version |
| How well does the model remove identifying information? | Independent gold spans, frozen model outputs, residual disclosures and utility | Improvement from training without a held-out comparison |

A personal-data form is a linkage aid, not a complete ground truth: an unmatched name can refer to another person, a fictional persona, or a paraphrased identifier. Separate **self**, **third party**, **synthetic**, and **uncertain** annotations.

## Boundaries

Deployment clarification (2026-10-30): each student will use their own computer. The verified localhost prototype is not yet a shared collection deployment. A common API/archive is proposed for automatic aggregation; its HTTPS address/hosting is pending. Participant enrollment must be separated from researcher raw-record access before distributing the extension; do not share the current researcher key with participants.

- Keep `/api/interactions/protect`, its engines and inference behavior unchanged.
- Add a separate research API namespace and a dedicated extension controller. Collection defaults off and is mutually exclusive with attachment protection during a capture session.
- Canonical documents belong in `docs/`. Read `workspace/pii-anonymizer-kb` as background only; never commit external resources or participant data.
- A local FastAPI process cannot observe a browser draft by itself. The extension captures it; the API authorizes the session and persists the final batch.
- Use one explicitly selected tab and text-only tasks for the initial implementation. No keystroke logging, historic chat import, passwords, clipboard scraping, screenshots or attachment contents.
- Treat assistant capture as rendered-text observation, not a provider transcript/export guarantee. Site adapters require a manual smoke test before a real study.
- Collection can operate without starting BentoML. Existing development Compose behavior remains unchanged; provide a separate research-only launch path.

## Delivery units

| Unit | Deliverable | Verification |
|---|---|---|
| Plan | This document and a recoverable work log | Structural readback |
| Evidence | At least 30 distinct papers, evidence matrix and reusable bibliography | Primary-source metadata and claim checks; record abstract/full-text depth |
| Study kit | Protocol, task cards, questionnaire, consent draft, coding guide, analysis/report templates | Cross-check every measure against a question and evidence; no invented outcomes |
| Storage | Opt-in, bounded, authorized, idempotent local persistence with receipt | HTTP validation, retries, conflicting uploads, access denial and persistence tests |
| Extension | Start, durable capture, stop/flush/upload, retry and copy receipt | Browser tests with synthetic local chat pages and API calls; existing attachment regression suite |
| Operation | Model-free launch, data access/export/withdrawal guidance and readiness checklist | Real local service integration where available; record all limitations |

## Data stewardship before recruiting

These are required institutional decisions, not approvals that software can grant:

- Name the responsible investigator and institution; obtain applicable ethics approval and consent wording.
- Decide a concrete retention/deletion schedule, authorized researchers, encrypted storage and backup controls.
- Do not require real national IDs, exact addresses, grades, health or financial details merely to provoke leakage. Start with synthetic task identities. Real-data collection requires a separate justified protocol.
- Keep Google Forms personal responses separate from chat storage. Disable automatic email collection unless separately justified; disclose Google's processing and any external chatbot processing.
- Make participation voluntary and unrelated to grades; provide an alternative and permit skipped tasks and withdrawal.
- Obtain separate optional permission for model training; study participation does not imply permission to train or publish raw chats.
- Use the receipt for linkage, not as authorization to read raw chats. Do not publish real transcripts or a joinable identity table.

## Current findings and limitations

Verified initial inspection: the delivered extension currently processes attachments, while architecture pages also describe target text protection. The API lifespan constructs an inference client without calling it, but the normal Compose API waits for healthy inference. Study pages describe intended capabilities, not evidence that study-session persistence exists.

Implementation update (2026-10-30): the independent capture API, opt-in extension, bounded archive and investigator-review study kit now exist with synthetic verification. Student-owned computers and a campus-private fixed IP were confirmed. Separate [university-network deployment artifacts](../../guides/research-campus-deployment.md) provide internal-CA HTTPS, enrollment-only access and a narrow-host extension copy without replacing the development Compose. Actual campus deployment, browser trust provisioning and provider/institutional fieldwork checks remain unperformed; consult the linked guide rather than treating the initial inspection above as the current implementation state.

The student package will be **ready for investigator review and a synthetic pilot**, not an assertion of ethics approval or production readiness. A results document will contain literature findings and an empty empirical reporting structure until observations exist.

## Follow the deliverables

- [Study kit](research-study/README.md)
- [Architecture and decisions](../../architecture/backend/privacy-middleware/research-capture.md)
- [Operation and verification](../../guides/research-capture.md)
- [Private-network deployment and participant setup](../../guides/research-campus-deployment.md)
