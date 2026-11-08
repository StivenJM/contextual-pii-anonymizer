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

All routes are under /api/research and return 404 while disabled. Enable explicitly, supply a researcher key of 32–4096 UTF-8 bytes, an absolute archive path and a valid retention setting. JSON uploads are limited to 1,000,000 UTF-8 bytes, 1,000 events and 100,000 characters per event; invalid research payloads do not echo the input.

| Method and path | Authorization | Result |
|---|---|---|
| GET /health | No credential; explicit enabled/configuration checks | Configuration and archive access readiness; no raw content or secrets |
| POST /sessions | X-Research-Enrollment; legacy X-Research-Key only when enrollment-only mode is disabled | Consent/protocol/provider/session UUID and client-generated capability recorded; idempotent with identical metadata and capability |
| PUT /sessions/{session_id}/complete | Bearer per-session capability | Commit an immutable batch, then return receipt_id and event_count; identical retry returns the same receipt; different retry returns 409 |
| GET /records/{receipt_id} | X-Research-Key | Restricted raw record and consent metadata, with Cache-Control: no-store |
| DELETE /sessions/{session_id} | Bearer capability | Withdraw the active or last saved session; no other session is accessible with that capability |
| DELETE /records/{receipt_id} | X-Research-Key | Investigator-mediated withdrawal by the saved linkage code |
| POST /purge-expired | X-Research-Key | Physically delete expired archive rows; operator scheduling and backup policy still required |

The opaque receipt is a **linkage identifier, not a read token**. Raw record access requires researcher authorization. Session capabilities are stored hashed in the API archive; the extension retains the capability for retry/withdrawal and never forwards it into the page/Google Forms. No public list/raw download endpoint is provided.

`RESEARCH_ENROLLMENT_KEY` is optional for local compatibility, but production requires a distinct enrollment key and sets `RESEARCH_REQUIRE_ENROLLMENT=true`. Enrollment permits starts only, not export, purge or investigator deletion. This cohort code is not a single-use participant identity. Both keys support a mutually exclusive `_FILE` source for local Compose secret mounts; unreadable/conflicting sources fail configuration without echoing paths/values. Retention/protocol checks and session capability semantics are unchanged.

## Private-network deployment decision

The user confirmed participant-owned computers and a campus-private fixed IP without a domain. The separate [production Compose](../../../../compose.research.yaml) runs only a non-reloading collector and Caddy's internal-CA TLS entry point. Neither the original Compose nor its model/database lifecycle is replaced. The proxy terminates HTTPS; the collector's HTTP port is not published. TLS and archive volumes persist separately; both containers run non-root with dropped capabilities and read-only root filesystems. This is transport protection, not application-level archive encryption or institutional authorization.

The [preparation command](../../../../deployment/research/prepare.py) emits a new extension copy with exactly one additional HTTPS private-IP permission; it does not request access to all HTTPS hosts. The normal protection endpoint stays unchanged. The public research endpoint is compiled into the copy, not supplied by the chatbot page. New session/receipt/withdrawal state retains its API origin; future package configuration cannot reroute an in-progress upload or deletion. Legacy state without an origin uses the original local API. No raw data/capability migration happens on repackaging.

Tradeoff: a study-specific package must be rebuilt/reapproved if the IP changes, but avoids broad optional host permissions and a participant-facing endpoint editor. Caddy's internal CA avoids public DNS/ACME requirements, but its public root must be verified and deliberately trusted on every client; the CA private keys must stay on the restricted host. Root trust is broader than this one service. An institutional CA remains an IT-managed alternative, not an automatic fallback. See the [campus operation guide](../../../guides/research-campus-deployment.md) for trust rollout, separate key distribution and deployment limits.

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

This is a **supervised pilot**, not a hardened multi-tenant service. Use loopback for local development; private-network operation requires the separate TLS deployment, verified client trust, a university-subnet firewall rule and approved host controls. Do not expose the collector directly or deploy the development server to the campus network. Researcher keys and session capabilities are bearer credentials; CORS is not authentication. Do not share them with the page, Forms, source control, screenshots or logs. Browser/profile access, compromised extensions, malicious page DOM, local malware and a stolen key remain threats.

Neither SQLite nor storage.local encrypts this archive on the application's behalf. Restrict the OS account/filesystem, use institutional encrypted storage and backups, and keep raw data outside Git. SQLite secure_delete and deleting a browser key are not guarantees of forensic erasure from SSDs, journals or backups. Expiry denies access; the purge command/schedule and backup expiry implement the physical-retention policy. The default 30-day parameter is a technical pilot default, **not an approved retention policy**.

Commercial-site adapters depend on DOM selectors; local-fixture tests do not prove present-day ChatGPT/Claude/Gemini support, trusted-event acceptance, shadow-DOM coverage, virtualized message recovery or transcript authenticity. Only rendered text is observed; regenerated/edited branches, voice, images, hidden context and attachment text are not complete provider exports. Do not use this logger as a security boundary that promises to prevent arbitrary exfiltration by a hostile page.

## Verification and use

See [the operation guide](../../../guides/research-capture.md) for observed tests, exact commands, deployment limits, access/export and readiness gates. See [the study kit](../../../project/experimentacion/research-study/README.md) for ethics, scenarios, instruments and analysis.

