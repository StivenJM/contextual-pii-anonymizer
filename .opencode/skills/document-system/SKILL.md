---
name: document-system
description: Create or update persistent documentation for Contextual PII Anonymizer from code, configuration, tests, and verified external sources. Use for repository documentation, documentation reviews, or keeping docs aligned with implementation; not for an isolated chat explanation.
---

# Document Contextual PII Anonymizer

Create or maintain verifiable documentation for this repository, useful to humans and coding agents. Respect the requested scope: a focused update does not require a full-system audit. All repository documentation created or updated by this skill must be written in English, regardless of the language used in the request or conversation. This project convention cannot be overridden by a request for another output language. Preserve surrounding structural and formatting conventions, but do not reproduce a non-English language convention. Avoid leaving a touched section with mixed-language prose; translate the affected section when necessary for consistency.

## Project context

The repository implements a Prompt Privacy System for detecting and protecting PII before interactions reach a commercial language model. Its principal implemented services are a FastAPI privacy middleware and a BentoML inference service, with PostgreSQL persistence and Docker Compose development infrastructure. Product documentation also describes target browser-extension, administration, and experimental capabilities that may not yet be implemented.

Do not collapse these boundaries:

- The privacy middleware owns canonical mapping, hybrid detection, fusion, policy evaluation, and de-identification.
- The inference service owns model discovery and native ML inference; it does not own global privacy policy.
- A browser extension sends protected text to the external model in the target design; the middleware is not automatically a proxy for that provider.
- Detection and a protection decision are separate responsibilities.
- “Anonymization,” masking, pseudonymization, and de-identification are not interchangeable. Describe only the guarantees supported by implementation and evidence.

Start with the repository `README.md` and the relevant area index: `docs/architecture/README.md`, `docs/guides/README.md`, or `docs/project/README.md`. Follow links to component pages rather than assuming every target capability exists.

## Documentation organization

Preserve the repository's three existing areas:

| Destination | Responsibility |
|---|---|
| `docs/architecture/` | Technical design, components, contracts, data, flows, boundaries, and architectural decisions |
| `docs/guides/` | Executable procedures for development, configuration, testing, maintenance, and operation |
| `docs/project/` | Product purpose, users, scope, capabilities, flows, rules, study context, risks, and vocabulary |

Keep decisions near the architecture component they govern when that matches the existing structure, such as a component `decisions/` directory. Do not import another repository's ADR hierarchy or create a new one without a repository-level decision. Preserve existing canonical pages and update navigation links when needed.

Read [the documentation contract](references/documentation-contract.md) when selecting pages for a new area, reorganizing documentation, or recording a decision.

## Review evidence before writing

- Identify the repository root, applicable instructions, current branch, local changes, and existing documentation. Preserve user work and unrelated untracked content.
- Read relevant manifests, lockfiles, entry points, environment templates, routes, domain contracts, persistence models, migrations, adapters, tests, CI, and container definitions.
- Follow representative flows end to end across producer and consumer boundaries. Verify behavior in executable code rather than relying only on comments, directory names, commit messages, or older documentation.
- Distinguish target architecture, implemented behavior, optional configuration, defaults, startup requirements, and operational availability.
- For a full review, cover applicable API, inference, ML/data, persistence, privacy boundaries, tests, build, containers, and operation. Record inaccessible or unverified areas.
- For a focused change, trace the affected contract and update only related pages, indexes, and decisions.

Use relative repository links. For external facts that matter, consult authoritative current sources and link them. Never copy secrets, credentials, raw personal data, sensitive study records, or production environment values into documentation; environment variable names and safe examples are usually sufficient.

## Write and maintain

Separate explicitly:

- behavior verified in the current implementation;
- target or proposed behavior;
- architectural decisions supported by evidence;
- experiments and their measured scope;
- unknown or pending work.

Do not invent functionality, approvals, ownership, historical dates, datasets, metrics, legal conclusions, model quality, privacy guarantees, or security properties. Avoid saying a flow is “end-to-end,” “safe,” “anonymous,” “persistent,” “atomic,” or “fail-closed” unless the relevant boundaries and tests support that exact claim.

Explain how the system is built in `architecture`, how to perform and verify a task in `guides`, and why the product exists and which observable rules it preserves in `project`. Link between areas instead of duplicating contracts.

Keep an accessible architecture overview with a purposeful Mermaid diagram when visual relationships improve comprehension. Prefer `flowchart` for structure, `sequenceDiagram` for interactions, `erDiagram` for persisted relations, and `stateDiagram-v2` for lifecycle state. A diagram supplements rather than replaces precise prose.

If requirements, user stories, study protocols, or decision identifiers already exist, preserve their stable IDs and trace them to evidence. Do not invent or renumber IDs, retroactively assign them to commits, or create a user story merely to justify documentation. Defining a requirement does not prove it is implemented or accepted.

For an architecture decision, record context, status, decision, boundaries, consequences, alternatives, and evidence. A retrospective document describes an observed implementation and must not imply historical approval. A proposal remains proposed until approval evidence exists.

## Validate proportionately

- Check local links, referenced paths, heading/navigation consistency, Markdown fences, and Mermaid syntax by inspection or available tooling.
- Verify commands against actual scripts, working directories, environment requirements, and current service names.
- Check consistency among HTTP schemas, routes, consumers, use cases, persistence constraints, model contracts, and documented errors.
- Run checks only when they are relevant and safe. A small documentation edit does not require all tests, and documentation work does not authorize migrations, seeds, model downloads, destructive Docker volume operations, external API calls, or deployments.
- Record commands, results, revision/date when useful, and limitations. Distinguish unit tests, mocked contracts, integration tests, live services, and static inspection.

## Delivery

Deliver persistent, navigable Markdown rather than only a chat plan. Summarize files created or updated, point to the affected index or canonical pages, and report actual validation and important unresolved findings. Keep README entry points concise and preserve useful compatibility links when reorganizing content.
