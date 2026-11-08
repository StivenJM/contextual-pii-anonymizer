# Annotation and offline evaluation plan

Freeze this plan before inspecting model comparisons. Nothing here reports completed student outcomes.

## Data layers and provenance

| Layer | Contents | Access / training eligibility |
|---|---|---|
| Identity/Forms | Optional approved background and receipt linkage | Restricted linkage staff only; never training input |
| Raw archive | Submitted text attempts, rendered assistant snapshots, task/time, consent flags | Authorized staff; not public and not automatically trainable |
| Annotation | Span offsets, types, referents, relevance, adjudication | Analysts with pseudonymous IDs; protect text excerpts |
| Model-ready | Explicitly eligible participant text, version/split manifest | Only training-permitted, nonwithdrawn records; exclude identity table and receipts |
| Aggregate report | Counts, rates, uncertainty and utility | Small-cell suppression and no raw identifying examples |

A user event records a **submission attempt before forwarding**. It does not prove the provider received or accepted the prompt. An assistant event is a latest observed rendered snapshot, not a complete network transcript. Use separate feasibility flags for provider/adapter failures.

## Codebook

Annotate participant text first; assistant text supplies context and can be analyzed separately, never counted as the participant's own disclosure.

| Field | Allowed coding |
|---|---|
| span | Start inclusive/end exclusive Unicode character offsets in the exact stored text; do not normalize before annotation |
| semantic_type | Existing system canonical taxonomy when applicable; add study-side contextual/sensitive categories without silently changing the production taxonomy |
| identifier_kind | direct; quasi/indirect; sensitive-nonidentifying; not-PII |
| referent | self; third_party; synthetic; uncertain; organization_only |
| relevance | necessary; optional; unnecessary; uncertain, relative to the participant's actual task/request |
| occurrence | First/repeated mention and coreference group within the session |
| source | participant; provided_card; assistant_generated; uncertain |
| confidence / adjudication | Annotator label, uncertainty note without unnecessary personal values, final label and rationale |

Do not label every number or capitalized word PII. Preserve combinations that could identify someone even when each individual token appears innocuous [R01](references.md#r01), [R09](references.md#r09), [R12](references.md#r12), [R24](references.md#r24).

## Annotation procedure

1. Train two human annotators on **synthetic rehearsal sessions not used for scoring**. Discuss the codebook and freeze its version.
2. Independently label a calibration subset, then all evaluation text where feasible; if resources limit double coding, preregister a random subset and report the exact fraction and sampling rule.
3. Calculate strict span agreement and semantic-type agreement **before adjudication**. For fixed categorical units, report raw agreement and Cohen's kappa with prevalence/context; kappa is not a span-boundary metric [R25](references.md#r25).
4. Have a third authorized human adjudicate unresolved disagreements or record uncertainty rather than force a false gold label. Here “third human” is a future study staffing role, not AI-agent delegation.
5. Keep annotators blind to which candidate system produced an output. Do not use the evaluated model as its own sole labeler or judge.
6. Record role, version and changes; exclude no record solely because it contradicts a hoped-for effect. Analyze interview themes separately, without claiming reflexive thematic analysis requires kappa [R26](references.md#r26).

## Primary behavioral summaries

For participant i, compute any-disclosure task rate = tasks with at least one relevant annotated identifying span / tasks with usable submitted text. Report the exact usable-task denominator and separately report skips/interrupted tasks. For synthetic cards name the quantity **provided-fictional-attribute disclosure**, not real personal-data leakage.

Report direct/quasi-identifying, self/third-party/synthetic/uncertain, task and broad study-background slices. Repeated occurrences count in occurrence metrics, while unique attributes count separately. Do not replace uncertain ownership with “self”. Use participant-level bootstrap intervals or an appropriate clustered model; do not bootstrap individual prompts as independent students.

Questionnaire matches are secondary supporting evidence. A match alone can reflect a quoted/third-party value; a nonmatch can hide paraphrase, inference or omitted questionnaire data. Do not call this an estimate of manual de-identification skill.

## Frozen model comparison

1. Before training, assign all sessions from a participant to one split. Proposed initial split: 60% train, 20% validation, 20% test using a recorded random seed and restricted grouping manifest. Small pilots are for debugging, not estimating a stable trained-model benefit.
2. Repeated card text creates template leakage. Add a scenario-family holdout evaluation or document that same-template results only measure within-template generalization. Deduplicate exact/near-identical prompts **within split planning**, not by deleting inconvenient test outcomes [R21](references.md#r21).
3. Remove withdrawn and non-training-permitted records from training. Test/evaluation use must itself remain consented. Never train on form data, receipt IDs, upload tokens or participant contact tables.
4. Freeze baseline model/version, candidate/version, tokenizer, canonical mapping, rules, thresholds, seeds and hardware. Preserve original text and gold labels; store each transformed output separately with run status. No per-test threshold tuning [R20](references.md#r20).
5. Use the existing protection endpoint for **offline replays only**; no capture path calls it. The operation guide gives a single authorized replay example. This delivery does not automatically launch training, upload datasets or download models.

## Metrics and failure rules

- Strict entity precision = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2PR/(P+R), where exact offsets **and** canonical type must agree. Define zero-denominator metrics as not estimable, not automatically 100%.
- Report type-level and micro totals plus participant-macro summaries. Partial-overlap scores may be exploratory, clearly distinguished from strict scores [R01](references.md#r01).
- Residual exposure = identifying gold spans still recoverable after transformation / identifying gold spans in the original. Review rewritten outputs manually; original offsets alone do not locate paraphrased identifiers.
- Over-redaction = removed/altered non-PII task-critical content. Score the math control separately [R12](references.md#r12).
- Utility rubric (blind human review): 0 unusable/incorrect, 1 major repair needed, 2 minor repair needed, 3 satisfies task. For F, the numerical reasoning must remain correct. This is a proposed local rubric, not a validated scale [R05](references.md#r05), [R32](references.md#r32).
- Technical feasibility: completed uploads, interrupted sessions, lost/unavailable reply snapshots, latency median/p95, errors/timeouts and retry rate. Never drop failed runs from the denominator. A timeout is a failure observation, not a good privacy score.
- Compare candidate–baseline using paired participant-level differences with 95% confidence intervals; specify the primary metric and multiplicity handling before confirmatory analysis. If sample size is small, report descriptive intervals without significance claims [R27](references.md#r27).
- Inference-based re-identification resistance is a distinct, optional, ethically scoped experiment; masking metrics alone do not prove anonymity [R09](references.md#r09), [R31](references.md#r31).

## Reproducibility manifest and report

Record: protocol/consent versions, collection dates, approved retention date, software commit, adapter/provider test date, task order, exclusions, linkage quality, grouping/split seed, gold-label version, model/config hashes, hardware, latency definition and every failed run. Publish only aggregates or separately approved synthetic examples. Complete dataset/model documentation [R18–R20](references.md#r18) and the [results report](results-report.md).

