# Pull request description format

This is the project's default convention, synthesized from the sources listed below. It is not a universal standard and does not override an existing repository template or an explicit user request.

## Core body

Use these sections when no other template applies. Scale their length to the change: a small correction may need only a few lines, while a cross-service branch must explain each major responsibility without narrating every commit.

| Section | Content |
|---|---|
| `## Summary` | The problem or need and resulting behavior in one or two short paragraphs. A before/after example is useful when it makes the result concrete. |
| `## Changes` | Significant changes grouped by purpose or responsibility. Include decisions and tradeoffs only when they help evaluate the solution. |
| `## Validation` | Commands or checks actually executed, their results, revision, and scope. Separate local tests, CI evidence, and pending verification. |
| `## Impact` | Effects for users, researchers, maintainers, data, compatibility, and known limitations. State unmeasured benefits as expectations. |

If no applicable checks were verified, say so directly, for example: “Tests were not run while preparing this description; validation of this branch is pending.” Tailor the statement to known evidence. Static analysis is not a functional test, mocks are not external integration, and a successful build does not prove database or model connectivity.

When useful reviewer steps exist, list them as proposed checks with an action and expected result, separate from completed validation. Do not mark unchecked work as completed.

## Conditional sections

- `## Deployment and rollback`: for migrations, containers, model artifacts, environment changes, or coordinated releases. Explain data effects and verified order without executing deployment. State when rollback is undefined.
- `## Reviewer notes`: for complex decisions, known limits, concrete risks, or a useful review order. Express uncertainty rather than inventing failures.
- `## Related work`: for confirmed requirements, issues, experiments, architectural decisions, or follow-up work. Use `docs/architecture/` for technical design, `docs/guides/` for procedures, and `docs/project/` for product purpose and rules.
- `## Visual evidence`: only when real screenshots or diagrams exist and help review. Link repository-accessible evidence rather than absolute local paths.
- `## Privacy and data`: when the change affects PII handling, datasets, logs, persistence, exports, or external model interactions. Identify the trust boundary and minimization behavior supported by the diff; do not make legal or irreversible-anonymization claims.

A heterogeneous branch still needs a complete description. It may recommend a better review split, but drafting the PR must not rewrite the branch.

## Quality criteria

- Open with the result and its reason; avoid generic claims such as “Several improvements were made.”
- Explain the final state, not the conversation or abandoned approaches unless they justify a current decision.
- Connect each major change to its purpose without repeating the same sentence in Summary, Changes, and Impact.
- Preserve the architecture boundary between the FastAPI privacy middleware and BentoML inference service unless the diff intentionally changes it.
- Distinguish target architecture from implemented behavior and experimental evidence from production guarantees.
- Do not fill sections merely to appear thorough.

## Sources

Consulted 16 October 2026. These sources support the general principles; project headings, scopes, privacy cautions, and output fields are local conventions.

- [Google Engineering Practices: Writing good CL descriptions](https://google.github.io/eng-practices/review/developer/cl-descriptions.html): preserve what changes and why for reviewers and future maintainers.
- [GitHub: Helping others review your changes](https://docs.github.com/en/pull-requests/concepts/helping-others-review-your-changes): explain the problem, approach, result, and review guidance.
- [GitLab Code Review Guidelines](https://docs.gitlab.com/development/code_review/): provide context, validation, and relevant compatibility or deployment consequences.
