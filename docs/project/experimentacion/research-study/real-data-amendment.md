# Proposed real-data phase and minimal linkage amendment

Status: **proposed, not approved**. This supplements the fictional-data feasibility pilot; it does not silently replace the user's intention to investigate actual student disclosures. The capture software can retain raw text, but that technical capability is not authorization to collect real identifying data.

## Why a second phase is needed

The six fictional cards allow safe rehearsal, known-attribute annotation and initial detector tests. They cannot estimate how frequently students reveal information about themselves in everyday AI use. That question needs consented real observations and a defensible way to establish whose information appears in the text. Public-chat findings do not determine a local student's identity or an Ecuadorian prevalence estimate [R08](references.md#r08), [R09](references.md#r09), [R19](references.md#r19), [R29](references.md#r29).

## Candidate observational design

After approval, recruit consenting adults for ordinary academic writing, translation, planning and explanation tasks. Let each participant select a current low-risk task or adapt a goal from A–F. Do not instruct them to include real personal details, do not supply a disclosure quota, and do not reward disclosure. Explain collection transparently; acknowledge that knowledge of recording may change behavior.

Examples of neutral goal prompts for the moderator:

- Draft a generic appointment request about coursework organization.
- Improve a short academic or club-related paragraph that you are comfortable sharing.
- Translate a nonconfidential message or explain a harmless programming example.
- Plan a study session without revealing another person's private circumstances.

Permit aliases and omitted/generalized details. Prohibit passwords, API keys, national ID numbers, private third-party messages, medical/financial records and other unnecessary sensitive material. A participant can skip or stop without penalty. The approved real-data instructions must be versioned separately from research-v1 fictional cards; use a distinct protocol identifier in the API, for example research-real-v1, only after the institution accepts the amendment.

This is an observational disclosure phase, not a randomized live anonymization intervention. A later protection comparison requires an operational intervention and its own design/power/approval. A manual de-identification skill test additionally needs a known original/edited pair; a background-data form alone cannot provide that evidence.

## Two linkage strategies and their tradeoffs

| Strategy | Benefit | Cost / limitation |
|---|---|---|
| Recommended: participant confirms ownership of already observed attributes, through approved restricted review | Avoids a second identity/contact dataset and handles aliases, third parties and fiction | Requires a careful review workflow and participant time; not exhaustive inference ground truth |
| Optional approved name/email matching form | Simple exact-match supporting evidence for selected direct identifiers; matches the user's proposed personal-information form | Creates a second identifiable dataset, needs additional justification/access/retention, misses paraphrases and contextual disclosures; a nonmatch is not no disclosure |

The investigator must choose the scientifically necessary minimum before collection. This document does not select a legal basis, guarantee compliance or authorize a live Google Form.

## Ready-to-adapt additional form items

If the institution approves the exact-matching strategy, insert the following optional items **before the final saved-identifier item F11** in the form master. Keep their answers outside the chat archive/model corpus.

| ID | English master question | Handling |
|---|---|---|
| L01 | What name or alias, if any, did you use to refer to yourself in today's AI conversation? You may leave this blank. | Optional short text; do not demand a legal name or verify identity from it |
| L02 | If you voluntarily used your own email address in today's conversation, you may provide that address for matching. Otherwise leave this blank. | Optional short text/email validation; do not request an unused address or collect account email automatically |
| L03 | Did the conversation contain information about you, a fictional person, another person, or are you unsure? | Multi-select: About me; Fictional; About another person; Unsure; Prefer not to answer |
| L04 | May authorized study staff use these optional answers solely to help label whose information appears in this session? | Yes/No; No excludes these answers from linkage; does not revoke otherwise valid participation |

These items are bespoke, unvalidated and require participant-language adaptation. Do not infer that a declared alias is a verified legal identity. Do not send a new prompt to the commercial AI containing form answers. Do not ask participants to disclose an email or name that was absent from the conversation merely to populate a dataset.

For ownership confirmation instead, use a restricted review of the participant's session: identify only the minimum already-observed attribute, ask whether it refers to self/third party/fiction/uncertain, and permit nonresponse. Do not email full chats or create public prefilled links. Establish how staff authenticate a withdrawal/review request without making the receipt a public read credential.

## Linkage, analysis and withdrawal

1. Use the confirmed opaque receipt to join the approved form response to the API record under researcher authorization. Resolve unknown/duplicate codes explicitly.
2. Keep the form/identity vault, raw chat and analytic pseudonym table separate. Use the most restrictive consent/training/withdrawal flags across records.
3. Exact matching is a candidate annotation aid, followed by authorized human review. Code quoted/third-party values and uncertain ownership; examine indirect attributes separately [R01](references.md#r01), [R07](references.md#r07), [R10](references.md#r10).
4. Report real confirmed self-disclosure separately from provided-fictional-attribute disclosure. Stratify by task and participant, and account for missing/ambiguous linkage.
5. Define a concrete deletion date and withdrawal cutoff for each copy before training. API withdrawal does not delete Forms, exported files, provider history, backups or learned weights. State those limits before consent [R18](references.md#r18), [R22](references.md#r22), [R23](references.md#r23).

## Approval checklist before enabling this phase

- [ ] Institution, responsible investigator, participant contacts and ethics routes named.
- [ ] Necessity of each real attribute and external Google/chatbot processing reviewed.
- [ ] Approved consent, optional matching permission and separate training permission.
- [ ] Spanish/local-language participant version cognitively pretested if required.
- [ ] Storage/profile access, encryption, retention, backups and incident plan approved.
- [ ] Real-provider adapter and recovery smoke tests completed without using unapproved personal data.
- [ ] Final recruitment/sample-size/stopping/analysis plan frozen, distinct from pilot feasibility targets.

Official materials to consult with institutional reviewers: [Ecuador SPDP consent guidance](https://www.spdp.gob.ec/docs/proteccion-de-datos-personales/general/consentimiento/) and [Google Forms response management](https://support.google.com/docs/answer/139706/view-and-manage-form-responses?hl=en-GB). These are operational/legal reference points, not additional papers in the 32-work review and not a conclusion that consent is the only possible legal basis.
