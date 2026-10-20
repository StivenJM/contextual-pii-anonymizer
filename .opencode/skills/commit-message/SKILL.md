---
name: commit-message
description: Recommend one semantic Conventional Commit message for Contextual PII Anonymizer from staged changes, a diff, or a user-provided summary. Use when asked to suggest or write a commit message; do not commit or stage changes.
---

# Generate a commit message

Generate a semantic Git commit message for Contextual PII Anonymizer. Recommend the message only; do not stage changes, create a commit, or push unless the user separately requests those actions.

## Output behavior

Return exactly one copy-pasteable commit message inside a fenced `text` block.

Do not provide explanations, alternatives, introductory text, or commentary unless the user explicitly asks for them. If the changes are unknown, ask only for the missing change summary instead of fabricating a message.

All generated commit content must be written in English, regardless of the language used in the request or conversation. This project convention cannot be overridden by a request for another output language.

## Commit rules

- Use Conventional Commits for the first line.
- Use an imperative, concise English summary without a final period.
- Keep the message semantic: describe intent, behavior, architectural impact, or user-facing effects rather than file operations.
- Keep the section labels `Why`, `What`, and `Impact` in English.
- Do not mention project file paths in those sections.
- Never add AI attribution or a `Co-Authored-By` line.
- Do not claim tests, linting, type checking, builds, migrations, model evaluation, or runtime checks passed without applicable evidence.

Choose the type that expresses the main intent:

| Type | Use |
|---|---|
| `feat` | Add or extend production functionality |
| `fix` | Correct defective behavior |
| `refactor` | Change structure without changing expected behavior |
| `test` | Add or improve tests without changing production behavior |
| `docs` | Modify documentation only |
| `build` | Change packaging, dependencies, containers, or deployment artifacts |
| `chore` | Perform repository maintenance that fits no more specific type |
| `experiment` | Run a proof of concept or model comparison not yet presented as production behavior |
| `data` | Prepare, transform, or version datasets |

Do not label a move or reorganization as a feature unless it also adds behavior. Prefer `experiment` to `feat` for exploratory ML work whose production behavior is not integrated and verifiable.

## Project scopes

Use the repository's ownership scopes:

| Scope | Responsibility |
|---|---|
| `api` | FastAPI, application use cases, privacy rules, de-identification, HTTP contracts, and PostgreSQL persistence |
| `inference` | BentoML service, model catalog, model execution, and native inference contracts |
| `ml` | Datasets, training, evaluation, and model experiments |
| `infra` | Docker Compose, images, deployment, networks, volumes, and operational resources |
| `platform` | One inseparable behavior requiring coordinated changes across multiple services |
| `docs` | Cross-cutting documentation organization and navigation |
| `repo` | Repository-wide configuration, automation, and shared tooling |

Choose the owner of the result, not every directory touched. Tests and component-specific documentation inherit the owning component. Use `platform` only when the result cannot be delivered correctly by one component. Omit the scope when no single scope honestly owns a heterogeneous change; do not combine scopes.

Documentation-only changes may use a component scope when documenting that component, such as `docs(api)`, and `docs(docs)` only when the documentation system itself is the subject. Prefer an unscoped `docs:` title when a scope adds no useful information.

## Message format

Use this structure:

```text
<type>(<optional-scope>): <short imperative summary>

Why:
<one concise paragraph explaining the motivation>

What:
- <high-level semantic change>
- <high-level semantic change>

Impact:
<one concise paragraph explaining the supported result, reduced risk, or future benefit>
```

Adjust the number of `What` bullets to the actual changes. Do not invent changes merely to fill the template. Do not include issue, requirement, or study identifiers unless the user supplies them and establishes their association with the selected changes.

## Execution process

1. Determine the changes from available evidence in this order:
   - Run `git status --short` to distinguish staged, unstaged, and untracked changes.
   - When staged changes exist, inspect `git diff --cached --stat` and `git diff --cached`. The staged diff defines the proposed commit; do not mix in unstaged edits, untracked files, or earlier conversational work unless explicitly requested.
   - If no staged changes exist, use a supplied diff or summary. If the user requests a message for current unstaged changes, inspect `git diff` and relevant untracked content without staging it.
   - For large diffs, inspect summaries and representative code while accounting for every changed area. Use rename detection to distinguish reorganization from behavior changes.
2. Identify the dominant type and owning scope from the resulting behavior.
3. Write `Why` as the supported problem, limitation, or need—not a file list or a repetition of the title.
4. Write `What` as semantic changes and responsibilities, avoiding low-level implementation trivia.
5. Write `Impact` as a supported user, maintainer, research, or architectural consequence. Distinguish intended benefit from verified outcome; do not invent privacy, security, performance, or compatibility guarantees.
6. Verify that the message covers only the selected changes and contains no unsupported claims.

## Missing information

Do not invent scope, motivation, impact, issue associations, or validation. Omit an uncertain scope when the message remains accurate. If there is insufficient evidence for an accurate message, ask only for the missing change summary.
