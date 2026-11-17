# Protect chat messages before sending

Branch: `feat/platform/unify-research-enrollment` (working tree has other uncommitted work; do not commit).
Test runners: `node --test browser-extension/tests/*.test.cjs`, `uv run --directory e2e --no-sync pytest`.

## Specs

- S1. Add an independent `Protección de chats` switch with help text `Revisa y protege tus mensajes antes de enviarlos`. Persist it independently from attachment protection; existing installs default to off. Synchronize open tabs.
- S2. No API call while typing, pasting, or idle. One protection request per draft version the user attempts to send.
- S3. Intercept send button, Enter shortcut, and form submit before the provider sends. Preserve the draft; snapshot exact editor text and conversation; show `Revisando mensaje…`.
- S4. A clean result with no warnings and no proposed changes continues the same send once, after verifying draft and conversation unchanged. No unnecessary confirmation and no claim that the message is PII-free.
- S5. A result with protected operations blocks the send, keeps the original draft, highlights protected spans with pastel red, and shows only `Se protegerá 1 dato personal` / `Se protegerán X datos personales` plus `Enviar versión protegida` and `Volver a editar`.
- S6. Confirming uses the exact `protected_text` from that snapshot, removes highlights, updates and verifies the editor, and sends once without another inference. If the editor cannot be updated or verified, keep/restore the draft, show an error, and never send the original.
- S7. Editing the draft or changing conversation while reviewing or confirming invalidates the pending result immediately; never overwrite newer text or confirm different text.
- S8. Highlighting is non-destructive: no text markers, preserved line breaks, formatting, selection, cursor, composition, and focus. Emoji/non-BMP offsets must not shift marks. Remove highlights on invalidation, cancel, send, disable, or conversation change. Provide an accessible non-color indication.
- S9. Reuse `POST /api/interactions/protect` and the existing protection rules/model. Preserve the full response; attachment flow keeps using `protected_text`.
- S10. Count/highlight only operations that change text, including conservative mapping gaps; exclude `KEEP`; merge overlaps so one span counts once.
- S11. Warnings or inconsistent responses never auto-send. Timeouts, invalid responses, API errors, empty messages, repeated clicks/Enter, switch-off, editor changes, and pending attachments keep the draft and show a clear retry path.
- S12. Coordinate with research capture so neither bypasses the other, messages are not duplicated, and send replay is scoped to one authorized operation. Adapt editor/send selectors for ChatGPT, Claude, and Gemini without claiming real-provider compatibility.
- S13. Do not persist drafts or PII. No silent truncation. No regex shortcut that skips the model.

## Tasks

- T1. Background reusable full protection response + `PROTEGER_TEXTO` message; preserve attachment behavior. Status: completed. Attachment E2E still passes with the full response.
- T2. Popup independent chat switch + background tab synchronization. Status: completed; default off and open-tab synchronization covered.
- T3. Chat protection module: state, API review, validation, counts, card, editor adapters, highlights, invalidation, confirm/replay. Status: completed.
- T4. Integrate with research-content send gate and reload/manifest wiring. Status: completed; unit coverage proves research capture receives the protected text once.
- T5. Unit and E2E coverage, including emoji offsets, counts, cancellation, errors, and research/attachment regression. Status: completed.
- T6. Full applicable checks and final limitations report. Status: in progress.

## Log

### L1 — user request

Implement chat-message protection in the browser extension: independent switch, no inference while typing, protect on send, non-destructive highlights, confirmation card with count and two actions, exact protected_text replay, invalidation on edits/conversation changes, research-capture coordination, and focused validation. Exact UI strings are quoted in Specs.

### L2 — baseline

- Extension tests: 79 passed before this feature.
- E2E non-integration: 23 passed, 6 deselected before this feature.
- The API response is `original_text, protected_text, detections, operations, mapping_gaps, warnings`; operations include `KEEP` and mapping-gap masks.
- Attachment protection currently reduces the response to `protected_text`; research capture already intercepts sends in `research-content.js`.

### L3 — implementation and evidence (2026-11-17)

- Added the independent `chatProtection` switch, default off, with background broadcast synchronization.
- Refactored the background protection call to retain the full response and added `PROTEGER_TEXTO`; attachment protection still consumes only `protected_text`.
- Added chat protection with contenteditable CSS-highlight ranges and a transparent textarea mirror; Python code-point offsets are converted to UTF-16 before drawing.
- Integrated the protection gate before research capture. Research capture receives the confirmed protected text; a failed replay still reports a research incident.
- Final checks: extension 91 passed; API 75 passed, 2 skipped; chat browser tests 12 passed; research browser tests 15 passed; attachment browser tests 6 passed; E2E non-integration 35 passed, 6 deselected; Ruff and `git diff --check` clean; documentation local links 50 files, 0 broken.
- Limitations: real-provider editors were not exercised; textarea and one synthetic contenteditable stand in for ChatGPT, Claude and Gemini. An editor-update failure path is implemented but not reproduced end-to-end. Server-side model/configuration changes are not observed while a confirmation card is open; the result remains bound to the in-memory draft/conversation snapshot. Docker integration tests were not run.

### L4 — card placement follow-up

- Moved the confirmation/status card from editor-relative positioning to the fixed bottom-right corner at 16 px, matching the attachment-processing card. Removed the editor-relative placement and its scroll/resize listeners.
- When an attachment is still processing, the chat card is suppressed so it does not cover the attachment spinner; the attachment status remains the visible feedback.
- E2E asserts computed `position: fixed`, `right: 16px`, `bottom: 16px`; chat tests 12 passed, full non-integration E2E 35 passed.

### L5 — research capture pauses both protections

- `obtenerChatProtection(tabId)` now returns false while that tab's research session is recording or paused, matching the existing attachment behavior. The background broadcasts the effective per-tab state.
- `research-content` also bypasses the chat gate whenever its own recording/paused state is active, covering the interval before a broadcast arrives.
- The captured tab records the raw submitted text again; chat protection resumes after the capture stops. Other tabs keep their independent protections.
- Updated the popup capture notice and the developer/research guides. Added unit coverage for per-tab effective state and for chat protection being bypassed during capture and resuming after stop.
- The popup now makes the effective state visible: while the captured tab is active, both protection cards are dimmed, their switches are unchecked and disabled, and their labels read `Desactivada`. The stored global preferences are preserved and restored after capture ends. The research browser test asserts the labels, `opacity: 0.55`, and disabled switches while capture is active.
