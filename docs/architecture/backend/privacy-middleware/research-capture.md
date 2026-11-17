# Independent research capture

- Status: implemented research workflow with local/private-network deployment preparation; not approved for identifiable student fieldwork.
- Documentation date: 2026-10-30.
- Scope: text capture, local archive and offline reuse; existing protection engines and inference service are unchanged.

## Two independent paths

~~~mermaid
flowchart LR
  User[Participant] --> Extension[Browser extension]
  Extension -->|existing attachment protection| Protect[Privacy API and engines]
  Protect --> Inference[Inference service]
  Extension -->|supported text: local acknowledgement then forward| Chat[Commercial chatbot]
  Extension --> Buffer[Extension local buffer]
  Buffer -->|finish: frozen batch| Research[Research API]
  Research --> Archive[Local SQLite archive]
  Research -->|confirmed opaque receipt| Extension
  Form[Separate Google Form] -. approved receipt join .-> Analysis[Restricted research analysis]
  Archive --> Analysis
  Analysis -. separately authorized offline replay .-> Protect
~~~

The API does not observe browser drafts directly. The extension records a submission attempt before replaying the supported send action, independently observes rendered assistant text, and uploads only when the participant stops. Collection never invokes the converter, privacy engines or inference adapter. Sending to the commercial chatbot remains the page's responsibility.

## Verified implementation map

| Responsibility | Source |
|---|---|
| Existing attachment flow / effective protection state | [background.js](../../../../browser-extension/extension/background.js), existing content.js |
| Serialized local session state, authorization, frozen upload and receipt | [research-background.js](../../../../browser-extension/extension/research-background.js) |
| Isolated-world editor/send adapters and assistant snapshots | [research-content.js](../../../../browser-extension/extension/research-content.js) |
| Explicit consent, start, stop/retry, task and copy/withdraw UX | [research-popup.js](../../../../browser-extension/extension/research-popup.js) |
| Bounded schemas and independent endpoints | [research/router.py](../../../../api/app/research/router.py), [schemas.py](../../../../api/app/research/schemas.py) |
| Transactional local archive | [storage.py](../../../../api/app/research/storage.py) |
| No-PostgreSQL/no-inference launch | [application.py](../../../../api/app/research/application.py) |
| Normal application integration | [routers/__init__.py](../../../../api/app/routers/__init__.py) includes the same research router |

## API contract

All routes are under /api/research and return 404 while disabled. Enable explicitly, supply a researcher key and a distinct participant enrollment code of 32–4096 UTF-8 bytes each, an absolute archive path and a valid retention setting. Missing, invalid or identical secrets make configuration fail closed with 503. JSON uploads are limited to 1,000,000 UTF-8 bytes, 1,000 events and 100,000 characters per event; invalid research payloads do not echo the input.

| Method and path | Authorization | Result |
|---|---|---|
| GET /health | No credential; explicit enabled/configuration checks | Configuration and archive access readiness; no raw content or secrets |
| POST /sessions | X-Research-Enrollment only; X-Research-Key is rejected even with the valid researcher key | Consent/protocol/provider/session UUID and client-generated capability recorded; idempotent with identical metadata and capability |
| PUT /sessions/{session_id}/complete | Bearer per-session capability | Commit an immutable batch, then return receipt_id and event_count; identical retry returns the same receipt; different retry returns 409 |
| GET /records/{receipt_id} | X-Research-Key | Restricted raw record and consent metadata, with Cache-Control: no-store |
| DELETE /sessions/{session_id} | Bearer capability | Withdraw the active or last saved session; no other session is accessible with that capability |
| DELETE /records/{receipt_id} | X-Research-Key | Investigator-mediated withdrawal by the saved linkage code |
| POST /purge-expired | X-Research-Key | Physically delete expired archive rows; operator scheduling and backup policy still required |

The opaque receipt is a **linkage identifier, not a read token**. Raw record access requires researcher authorization. Session capabilities are stored hashed in the API archive; the extension retains the capability for retry/withdrawal and never forwards it into the page/Google Forms. No public list/raw download endpoint is provided.

`RESEARCH_ENROLLMENT_KEY` is required whenever research capture is enabled and must differ from `RESEARCH_API_KEY`; there is no enrollment-only compatibility mode. Enrollment permits starts only, not export, purge or investigator deletion. This cohort code is not a single-use participant identity. Both keys support a mutually exclusive `_FILE` source for local Compose secret mounts; unreadable/conflicting sources fail configuration without echoing paths/values. Retention/protocol checks and session capability semantics are unchanged.

### Fail-closed enrollment migration

The previous API accepted the researcher key at `POST /sessions` when enrollment was not required. The current `participant` dependency accepts only `X-Research-Enrollment`, and `configuration` requires a non-empty `RESEARCH_ENROLLMENT_KEY` distinct from `RESEARCH_API_KEY`. There is no compatibility flag:

1. Provision a distinct `RESEARCH_ENROLLMENT_KEY` in every environment. This configuration change does not alter the previous server's behavior.
2. Deploy the current API first with research capture enabled. It returns 401 for `X-Research-Key` session starts and 503 for missing, invalid or identical enrollment configuration. Older extensions that send the researcher key cannot start during this window; sessions already started retain their capability for completion and withdrawal.
3. Deploy the unified extension, which sends only `X-Research-Enrollment`.
4. Verify and remove `RESEARCH_REQUIRE_ENROLLMENT` from configuration. The current code ignores it; leaving it does not restore the previous mode.

Do not deploy the extension before the current API. While the previous server remains enabled, its legacy path accepts the researcher key for session start. Schedule maintenance or stop session starts instead of preserving that server as "compatibility".

Rollback must not redeploy the previous API with research capture enabled, because that restores privileged-key enrollment. Keep the current API and roll back only the extension (older extensions fail closed with 401), or set `RESEARCH_ENABLED=false` to return 404 and disable capture until the fix is ready. Do not restore `RESEARCH_REQUIRE_ENROLLMENT` expecting the old mode. Privileged export, investigator-mediated deletion and purge continue to require `X-Research-Key` and reject the participation code.

## Deployment status in this checkout

This checkout contains the local/loopback research API and the development Compose only. It does not contain the former production collector Compose, TLS entry point, extension-packaging command or campus operation guide; those paths must not be inferred from this tree. The extension can bind a remote API origin through its packaged configuration, but a production deployment, private-IP HTTPS, client trust, host hardening, secret distribution and participant packaging require a separate product and institutional decision.

The development Compose and the standalone model-free entry point are not production deployments. Do not expose the development Admin API, run the reloading development server on a campus network, or claim that this repository provides a deployment-ready collector.

## State and failure semantics

~~~mermaid
stateDiagram-v2
  [*] --> Idle
  Idle --> Starting: consent + supported fresh tab
  Starting --> Recording: API authorizes + activation acknowledged
  Recording --> Paused: conversation route changes / capture interrupted
  Paused --> Pending: finish as interrupted
  Starting --> Idle: explicit discard
  Recording --> Pending: stop + flush + freeze
  Pending --> Pending: timeout / bad acknowledgement / retry
  Pending --> Saved: committed API response + local receipt write
  Saved --> Idle: next session
  Recording --> Withdrawing: discard / withdrawal
  Saved --> Withdrawing: withdrawal
  Withdrawing --> Withdrawing: API unavailable, capability retained
  Withdrawing --> Idle: deletion acknowledged
~~~

- Research state is stored under one storage.local key; mutations are serialized through a service-worker queue. A worker restart reloads persisted state, not globals. This is a small bounded buffer, not an unlimited log.
- A local write is awaited before replaying a send. On quota/validation failure, the supported send is blocked and the participant sees a warning. A user event denotes an attempted submission, not proven provider acceptance.
- Repeated identical user text with distinct event IDs remains distinct. Retries of the same event ID do not duplicate it. Assistant streaming updates replace the latest snapshot for that observed DOM node, not create a token-level transcript.
- On stop, the content controller stops new interception, waits for in-flight local submission work and flushes currently rendered replies before the background freezes the batch. A page that cannot flush produces capture_status=interrupted, not a false complete transcript.
- A request timeout or invalid receipt leaves the frozen batch intact. If the API committed but the response was lost, the same idempotent request recovers the receipt. Only successful acknowledgement plus local state write removes the buffered raw text.
- Research and attachment protection are mutually exclusive only on the selected tab while recording or paused. The original activo preference and other tabs are unchanged. Ordinary protection resumes during pending upload and withdrawal, not only after the API recovers. File conversion messages reject only while capture is active/paused in the bound tab.
- Initial API authorization leaves the session in starting until the content controller acknowledges activation. Unexpected same-document conversation-path changes pause capture, exclude subsequently displayed history and force an interrupted record. Only the known first fresh-chat-to-assigned-URL transition for each provider is permitted; current live-provider behavior still requires a smoke test.
- Withdrawal immediately removes local raw events/batch and stops collection, retaining only the capability/identity needed to retry API deletion. An offline deletion remains visibly pending and cannot be converted into a new upload. A previous receipt is hidden while a new session or withdrawal is active, avoiding accidental linkage to an older saved chat.
- Text-only attachment selection/drop/paste is blocked during research capture. Previously loaded attachments and unsupported provider pathways are outside the capture contract; use a fresh empty conversation and day-of-study smoke testing.

## Important decisions and alternatives

| Decision | Status and rationale | Alternative / tradeoff | Evidence |
|---|---|---|---|
| Separate namespace, controller and entry point | Implemented; avoid model latency/dependency for collection | Extending protect would conflate observation with intervention and inferencing failures | Code boundaries; R03/R04 inform the browser boundary, not the storage technology |
| SQLite local archive, no new dependency/migration in the existing PostgreSQL schema | Implemented for one local investigator workstation; transactions enforce immutable finalization | Reuse PostgreSQL for managed/multi-user deployments, but it adds service startup and schema migration; revisit before shared deployment | Standard-library SQLite; engineering decision, not a paper-derived performance claim |
| Buffer in storage.local, not storage.sync or page localStorage | Implemented; survive popup closure/worker idle shutdown and avoid synchronizing raw chats | IndexedDB scales better and provides richer transactions, but requires more machinery for this bounded pilot | [Chrome storage](https://developer.chrome.com/docs/extensions/reference/api/storage), [worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle) |
| One fresh conversation document in one selected tab | Implemented; avoids cross-tab/history scraping and ambiguous provenance | Cross-tab/full provider exports need new explicit scope and durable conversation IDs | R08/R30 motivate provenance; limitation is deliberate |
| Explicit raw collection + separate training opt-in | Implemented flags; approved institutional consent remains external | Bundled consent would hide secondary use and reduce participant choice | R14–R19, R22/R23 |
| Submitted behavior versus questionnaire | Study decision; questionnaire linkage is supportive, not exhaustive gold labels | Form-string matching is simpler but misses aliases, third parties and indirect identifiers | R01/R07–R10/R17/R29 |
| Offline paired evaluation with participant-disjoint split | Proposed protocol; training is not launched automatically | Live A/B intervention is valuable later but needs a functioning intervention, power plan and new approval | R05/R11/R12/R20/R21/R27/R31/R32 |
| API and browser controls, not a public raw-chat dashboard | Implemented narrow access; reduce accidental exposure | Institutional authentication, audit logs and researcher UI are needed for wider deployments | Engineering threat-boundary decision |

R-numbers resolve to the [32-paper bibliography](../../../project/experimentacion/research-study/references.md); the [evidence matrix](../../../project/experimentacion/research-study/literature-review.md) states transfer limits. None of these papers authorizes this institution's data collection.

## Security and operational limits

This is a **supervised pilot**, not a hardened multi-tenant service. Use loopback for local development; any private-network operation would require a separately designed TLS deployment, verified client trust, a university-subnet firewall rule and approved host controls, none of which are included in this checkout. Do not expose the collector directly or deploy the development server to the campus network. Researcher keys, participant enrollment codes and session capabilities are bearer credentials; CORS is not authentication. Do not share them with the page, Forms, source control, screenshots or logs. Browser/profile access, compromised extensions, malicious page DOM, local malware and a stolen key remain threats.

Neither SQLite nor storage.local encrypts this archive on the application's behalf. Restrict the OS account/filesystem, use institutional encrypted storage and backups, and keep raw data outside Git. SQLite secure_delete and deleting a browser key are not guarantees of forensic erasure from SSDs, journals or backups. Expiry denies access; the purge command/schedule and backup expiry implement the physical-retention policy. The default 30-day parameter is a technical pilot default, **not an approved retention policy**.

Commercial-site adapters depend on DOM selectors; local-fixture tests do not prove present-day ChatGPT/Claude/Gemini support, trusted-event acceptance, shadow-DOM coverage, virtualized message recovery or transcript authenticity. Only rendered text is observed; regenerated/edited branches, voice, images, hidden context and attachment text are not complete provider exports. Do not use this logger as a security boundary that promises to prevent arbitrary exfiltration by a hostile page.

## Verification and use

See [the operation guide](../../../guides/research-capture.md) for observed tests, exact commands, deployment limits, access/export and readiness gates. See [the study kit](../../../project/experimentacion/research-study/README.md) for ethics, scenarios, instruments and analysis.

