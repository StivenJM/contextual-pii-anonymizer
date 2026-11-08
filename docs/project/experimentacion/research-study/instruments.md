# Consent, form and moderator instruments

Status: investigator-review masters. Fill the named institutional fields and obtain approved final wording before recruitment. These are bespoke instruments, not validated scales. No live Google Form has been created.

## Participant information / consent master

**Study:** Academic AI interaction and de-identification research, research-v1.

**Responsible investigator and institution:** TO BE COMPLETED by the institution. **Contact / ethics complaint route:** TO BE COMPLETED. **Exact retention end date and backup deletion schedule:** TO BE APPROVED. Missing values are a no-go, not defaults granted by this draft.

We invite you to complete fictional academic tasks using an AI chatbot. The extension stores the text you submit and replies rendered during the active session, a task code and timestamps. It does not record unsent keystrokes or automatically protect your text. Capture is limited to the selected conversation document. Your prompts also go to the commercial chatbot you use, whose processing is separate from the local research archive. Technical failures may produce an incomplete session, which will be marked.

The initial pilot asks you to use only fictional card data. Do not enter real passwords, national IDs, health information, financial details or other people's private information. Participation is voluntary, unrelated to grades and may be stopped or skipped without penalty. State the locally approved compensation and alternative activity here before use.

An opaque identifier links the chat session to the study questionnaire. This is pseudonymous, **not anonymous**, particularly if you voluntarily provide identifiable information. Only authorized study staff may access raw chats; the institution must identify those roles and approved storage/access arrangements. Google Forms responses, if used, are processed by Google and stored separately. Do not collect account email addresses automatically unless the approved protocol explicitly requires it.

You may request withdrawal using the saved code and the approved contact route. The extension's withdrawal action deletes its current/last linked research record where available. The investigator must separately remove linked form, exports and annotations, subject to the stated protocol. The system cannot delete the commercial provider's records, guarantee forensic erasure from backups, or undo already completed model training. Explain the withdrawal cutoff before training, and disclose when aggregate results can no longer be linked.

Check separately:

- [ ] I am at least 18, have received information I understand, and voluntarily agree to this research collection.
- [ ] OPTIONAL: I agree that eligible session text may be used to train a research model after the stated withdrawal window. Declining does not prevent participation.
- [ ] OPTIONAL, separately administered if ever needed: permission for specifically reviewed quotations. Do not publish raw chats by default.

A software checkbox records an assertion of consent; it does not replace an approved information process, comprehension check or institutional records. Retain evidence of consent version/date separately with restricted access [R14–R19](references.md#r14), [R22–R23](references.md#r22).

## Google Forms build specification

Use an institution-approved account, not a personal investigator account by default. Do not enable public response summaries, edit-after-submit links or automatic email collection without approval. Verify who can view/download responses and whether institutional sign-in is required. Do not put the session code in a URL or public prefilled link. Never put the API key or upload capability into Forms.

| ID | Question / exact English master wording | Type | Required / handling |
|---|---|---|---|
| F01 | Are you 18 years of age or older? | Yes / No | Required; No ends recruitment under this adult-only protocol |
| F02 | Have you read the approved study information and voluntarily agreed to participate? | Yes / No | Required; No ends research, no session should start |
| F03 | How often have you used an AI chatbot in the last month? | Never; Less than weekly; Weekly; Daily; Prefer not to answer | Optional; experience covariate, not a literacy score |
| F04 | Does your current study program include substantial computing or software training? | Yes; No; Unsure; Prefer not to answer | Optional broad grouping, not exact degree/institution |
| F05 | Which age range includes you? | 18–24; 25–34; 35 or older; Prefer not to answer | Optional; merge or suppress small cells in reporting |
| F06 | Did any task lead you to include information you later wished you had omitted? | Yes; No; Unsure; Prefer not to answer | Optional; perception, not objective leakage |
| F07 | Did you omit or generalize information before sending any prompt? | Yes; No; Unsure; Prefer not to answer | Optional; compare cautiously with annotated behavior |
| F08 | How clear was it when recording was active and when it stopped? | Very unclear; Unclear; Neither; Clear; Very clear | Optional; bespoke usability item, not SUS |
| F09 | Did you experience a technical problem or skip a task? Describe it without names or personal details. | Short paragraph | Optional; raw text needs the same access controls |
| F10 | May eligible session text be used for model training under the separate information and withdrawal policy? | Yes; No | Explicit separate choice; do not default to Yes |
| F11 | Paste the confirmed saved identifier shown by the extension. | Short answer; regex ^[A-Za-z0-9_-]{32}$ | Required only for submitted sessions; preserve case and whitespace-trim only |

F11 is the last questionnaire item, matching the requested workflow. Consent and eligibility must be established **before** capture; a later form answer cannot retroactively authorize collection. If F10 contradicts the API's training_consent, use the more restrictive value until clarified; do not silently enable training.

### If a real-data linkage amendment is approved

Use the [proposed real-data amendment and ready-to-adapt L01–L04 items](real-data-amendment.md) to make the scope and exact optional questions explicit; do not interpret this master as approval to collect them.

Do not simply add compulsory national ID, exact birth date, address or telephone. Specify the minimum attribute needed for the scientific question, why it cannot be replaced by participant confirmation, who can access it and its deletion date. Prefer an optional per-session ownership confirmation (“Did this value refer to you, a fictional person, someone else, or are you unsure?”) performed by authorized staff. Exact personal attributes belong in a separate identity vault, never in the chat archive or training corpus.

Matching must handle absent answers, aliases, typos and third parties; an exact-string match is positive evidence only, while a mismatch is **not evidence of no disclosure**. No automatic Forms join or sync is implemented.

## Restricted linkage workflow

1. Export approved form responses to restricted storage outside Git. Validate code format and find the corresponding archive record through researcher-authorized API access, not by exposing chats publicly.
2. Flag missing, unknown and duplicate codes. Resolve ambiguities with the participant through the approved route or mark unlinked; never choose an arbitrary row.
3. Keep an identity/linkage table separate from raw chats, annotations and model-ready text. Give analysts a new study-level pseudonym, not the identity table.
4. Combine collection consent, training permission and withdrawal state. A withdrawal or either training refusal overrides eligibility.
5. Record join quality (linked, unlinked, ambiguous), not personal values, in the analysis manifest. Process withdrawals across every copy and backup schedule.

## Debrief / retrospective interview

Ask only after tasks to reduce priming: “What information did you think the AI needed?”, “Did you notice the recording indicator?”, “Was there a point where you wanted to stop?”, “Did you choose to leave anything out?”, “Were any instructions unclear?” Do not ask the student to reveal the omitted personal information. Use notes without quotes/names unless separately consented. Apply [R26](references.md#r26) to interpret these accounts, separately from gold-span agreement.

