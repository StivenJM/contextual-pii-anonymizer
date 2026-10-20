# Documentation contract

Read this reference when selecting pages for a new subsystem, reorganizing documentation, or recording a significant decision. File names are illustrative; preserve existing pages that already fulfill the purpose.

## Classify content

| Question | Area | Useful content |
|---|---|---|
| How is the system built and where does each responsibility live? | architecture | Components, dependencies, processes, trust boundaries, and code map |
| What happens from prompt input to protected output? | architecture | Extension/API flow, inference, detection, mapping, fusion, policy, transformation, errors, and external boundary |
| What contract is exposed? | architecture | Routes, inputs, outputs, model-native contracts, errors, and effective authorization |
| What is persisted and what preserves integrity? | architecture | Relationships, constraints, migrations, formats, versioning, and lifecycle |
| What integrates with what, and what happens on failure? | architecture | Adapters, timeouts, health behavior, startup ordering, and fallback policy |
| How do I prepare, run, test, or maintain it? | guides | Prerequisites, safe commands, execution directory, expected result, and diagnosis |
| Why does the product exist and for whom? | project | Problem, participants, researchers, administrators, objectives, and scope |
| Which privacy and study rules must remain observable? | project | Protection rules, consent/data minimization, limits, and acceptance conditions |
| What risk or decision affects the project? | project or architecture | Product impact in project; technical decision and evidence in the owning architecture component |

A deployment procedure belongs in guides; deployment topology belongs in architecture; product expectations and study constraints belong in project. Link these views rather than duplicating them.

## Pages by need

For an undocumented area, establish navigation and cover only responsibilities that actually exist.

- **Architecture:** concise overview, service/component boundaries, principal flow, API and model contracts, data, integrations, trust boundaries, and decisions. Clearly label target-only components.
- **Guides:** local setup, configuration, testing, migrations, common maintenance, operation, and diagnosis. Include a safe result check for each procedure.
- **Project:** purpose, scope, actors, capabilities, observable flows and rules, experimental context, terminology, and known limitations.

For a partial update, change only pages affected by the modified contract and indexes whose navigation changed.

## Privacy and research claims

Documentation about PII deserves explicit evidence and restrained language:

- State where raw text, detections, protected text, configuration, and study data cross process or trust boundaries.
- Distinguish locally controlled components from commercial model providers and other external dependencies.
- Name the actual transformation—masking, replacement, pseudonymization, or another operation—and avoid claiming irreversible anonymization without proof.
- Document fail-open or fail-closed behavior from executable paths and tests, including timeout and partial-failure cases.
- Avoid embedding real PII in examples. Use obviously synthetic values and minimize retained text.
- Separate intended research measurements from results actually collected and validated.
- Do not turn technical documentation into legal advice or claim regulatory compliance without authoritative evidence and an explicit project decision.

## Guide skeleton

Adapt this sequence to the task:

1. Objective and intended reader.
2. Prerequisites, environment, and execution directory.
3. Steps or commands backed by the repository.
4. Observable expected result and verification.
5. Limits, common failures, cleanup effects, and links to related contracts.

Separate PowerShell from POSIX shell instructions when syntax differs. Identify commands that mutate data, delete Docker volumes, download large models, contact external services, or consume paid resources before presenting them.

## Architecture decisions

Use the existing component-local `decisions/` structure where applicable. Follow the area's established naming style rather than imposing a new global numbering scheme.

Record at least:

```markdown
# Decision title

- Status: observed, proposed, accepted, superseded, or rejected—with evidence
- Documentation date: actual date of writing when the project uses dates
- Scope: responsibilities and behavior affected

## Context

Verified problem, constraints, and explicit assumptions.

## Decision

Observed, accepted, or proposed option and its limits.

## Consequences

Benefits, costs, privacy/data effects, and operational impact.

## Alternatives

Relevant tradeoffs without invented historical deliberation.

## Evidence and validation

Links to implementation, tests, approval evidence, and pending verification.
```

Change status only when evidence supports it. Creating a document does not accept a proposal. Preserve superseded records and link successors when the existing convention does so.

## Review evidence

For each technical finding, identify the concrete condition, source, impact, proposed priority, and next action. Distinguish an observed defect, an inferred risk, and a reproduced incident.

Record what was inspected and tested. Verify strong terms such as “protected,” “optional,” “persistent,” “healthy,” “atomic,” “idempotent,” “compatible,” and “end-to-end” against the complete applicable flow. A comment, mock, successful build, or health endpoint alone is insufficient.

When reorganizing documentation, update incoming links and avoid leaving contradictory full copies. Preserve a short compatibility page only when it maintains a useful stable entry point.
