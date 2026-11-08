# Protocol: task-based research capture, version research-v1

Status: proposed protocol for investigator approval, dated 2026-10-29. Population: consenting adult university students. Initial purpose: test feasibility and handling of **fictional task data**, then evaluate de-identification offline. No institutional approval is implied.

For the subsequent natural real-disclosure question, see the separately proposed [real-data phase and minimal-linkage amendment](real-data-amendment.md). Its approval, consent and measures are not replaced by the fictional pilot.

## Research questions and estimands

| Question | Unit and measure | Interpretation |
|---|---|---|
| Q1: What identifying/task-sensitive information is submitted? | Per-participant proportion of tasks containing annotated identifying spans; counts per category | In the synthetic pilot: disclosure of provided fictional attributes, not actual personal-data prevalence |
| Q2: What information is unnecessarily included for the task? | Independently coded necessary/optional/unnecessary/uncertain spans | Contextual appropriateness is a human-coded judgment, not a keyword match |
| Q3: How effective is a frozen detector/protector on these inputs? | Strict span precision/recall/F1, residual identifying spans and utility per held-out participant | Offline technical performance, not a claim of improved real-world student behavior |
| Q4: Does a trained candidate improve over its frozen baseline? | Paired participant-level differences on untouched test participants, including utility and failure rate | Only after separate training permission, a locked split and an actual candidate exist |

These constructs follow [R01](references.md#r01), [R06–R10](references.md#r06), [R12](references.md#r12), [R21](references.md#r21). No claim of manual de-identification skill follows merely from a personal-data form.

## Design and sampling

- Begin with a feasibility pilot of **8 adults**, proposed for discovering instruction, adapter and collection problems, not statistical significance or population estimates [R04](references.md#r04), [R27](references.md#r27).
- Recruit voluntarily outside grading decisions. Do not give the instructor identifiable responses. Offer an equivalent non-research activity; compensation must not depend on disclosure, consent to training or task completion.
- All participants perform A–F, approximately 4 minutes per task. Aim for 40–50 minutes total, allowing breaks. These durations are proposed operating limits, not literature-derived effects.
- Assign the six cyclic orders ABCDEF, BCDEFA, CDEFAB, DEFABC, EFABCD, FABCDE, then their reverses, rotating by enrollment order in a restricted allocation sheet. Record the actual order and deviations. This reduces order imbalance but is not full randomization and does not prove causal effects.
- For a later prevalence estimate with independent participants, a conservative 95% interval planning approximation at p=.5 and half-width .10 is ceil(1.96²*.25/.10²)=97 completed participants. With a proposed 20% allowance, recruit 122. This is a transparent **illustration**, not the final sample-size decision. A clustered comparison or training-effect claim needs a separate simulation/power calculation using pilot variability [R27](references.md#r27).
- Record broad technical/nontechnical study background as optional. Do not infer subgroup differences from small cells or count six tasks from one student as six independent students.

## Before the session

1. Verify approval, current consent version, authorized staff and the exact retention dates. Translate/pretest the participant master if required.
2. Use an isolated browser profile with no personal provider history, memory or preloaded attachments; use only institution-authorized commercial services/accounts. Do not inspect ambient credentials or sign in on the participant's behalf.
3. Rehearse with synthetic text. Verify the site editor, send button and assistant selectors that day. A local automated fixture is not evidence that a live provider's latest UI works.
4. Prepare one fresh empty conversation, the local API, extension and scenario allocation. Keep screen/video/trace recording off.
5. Ask the participant to explain: what is recorded, that collection is not protection, where the data goes, how to stop and what withdrawal can/cannot delete. Correct misunderstandings before proceeding.

## Moderator opening script

> We are studying how people use AI for ordinary academic tasks and how software handles identifying information. Participation is voluntary and unrelated to your grades. Use only the fictional details on the cards, never real passwords, IDs, health information or other people's data. You may omit, generalize or skip any detail or task. The extension records submitted text and visible replies after you start; it does not de-identify this text. The external chatbot also receives what you send under its own service terms. You can stop at any time. Separate optional permission is required before your session can be used for model training.

This is an English master script. Do not read it verbatim to someone who does not understand it.

## Session run sheet

| Stage | Actions and observable record |
|---|---|
| Consent, 5–8 min | Read information; record consent separately; training opt-in starts unchecked; decline ends research without penalty |
| Setup, 3–5 min | Enable local API; open a fresh chat; enter researcher key in extension; participant explicitly checks consent and starts |
| Task loop, 24 min | Set the card's Task ID before its first prompt; read only that card; allow natural wording and optional follow-ups; wait for reply completion before changing tasks |
| Finish, 2–3 min | Participant clicks Finish and save, waits for confirmed identifier, copies it, and pastes it into the form |
| Debrief, 5–8 min | Complete optional background and perception items; explain receipt and withdrawal; confirm no real third-party data were intentionally requested |

Do not demand a minimum number of disclosures or reward use of identifying details. Prefer retrospective probing after tasks; concurrent think-aloud can itself change disclosure behavior. Do not type prompts for participants.

## Failure and exclusion rules

- If consent is absent or withdrawn, do not begin/continue collection. Use Discard/withdraw and remove linked form/annotation copies through the approved withdrawal process.
- If a page reloads, navigates or closes, finish the buffered session as interrupted; do not silently splice a new document into it.
- If upload fails, retain the local copy and retry the same frozen batch. Do not ask the student to repeat tasks just to obtain a receipt.
- If the adapter fails, do not claim full-history capture. Mark the affected task/session and exclude it from complete-transcript analyses, reporting the exclusion and keeping an attrition count.
- If real PII is accidentally submitted, stop, restrict access, inform the responsible investigator and apply the incident/withdrawal procedure. The research API cannot delete the provider's history or Google records.
- Primary analysis excludes no-consent, test/staff rehearsal and unrecoverable/corrupt records; incomplete sessions remain visible in attrition and feasibility reporting. Never exclude a session because the model performed badly.

## Stop/go checklist

- [ ] Investigator, institution, contact and complaint/ethics routes named.
- [ ] Applicable institutional/legal review complete; no unsupported compliance assertion.
- [ ] Participant language, accessibility and comprehension checked.
- [ ] Exact retention/deletion date, backups and access roles approved.
- [ ] Google Forms and chatbot data flows disclosed and authorized.
- [ ] Day-of-study live adapter smoke test passes; fresh profile and no attachments.
- [ ] Synthetic pilot complete; instructions and measures revised/versioned before main recruitment.
- [ ] Analysis questions, exclusions, split and stopping rule frozen before substantive evaluation.

No-go if any required item remains unchecked. The software does not grant ethical authorization [R14–R19](references.md#r14).

