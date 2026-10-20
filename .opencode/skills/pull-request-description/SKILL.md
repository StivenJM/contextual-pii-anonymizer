---
name: pull-request-description
description: Draft a copy-pasteable pull request title and description for Contextual PII Anonymizer by comparing a specified head branch with its base. Use for PR text, not commit messages or standalone code reviews.
---

# Describe a pull request

Prepare a faithful proposal for the complete branch change. This task drafts text only. Creating or editing a PR, pushing, committing, staging, switching branches, merging, or modifying project files requires a separate user request.

## Resolve the comparison

- The branch being proposed is the head; the branch receiving the PR is the base. Preserve names supplied by the user and ask when their roles are genuinely ambiguous.
- If the head is missing, ask for it rather than silently substituting the active branch.
- Use an explicit base when supplied. Otherwise read repository instructions and available references. Normal work branches target `develop`; `main` represents stable versions. Use `develop` only when it exists and no contrary instruction applies. Do not infer the base from a work branch's upstream, which may merely be its remote copy.
- Resolve head and base to existing references and commit SHAs. Treat names beginning with options or unresolved names as invalid data, never shell options. Do not interpolate unescaped user input into commands.
- Prefer a named local reference when explicitly requested; if only the remote reference exists, use it. If local and remote tips diverge and the request does not identify which one, disclose the difference and clarify.
- Read applicable repository instructions and any PR template before drafting. Preserve required fields and explicit user preferences.

## Gather branch evidence

Do not switch branches or modify the working tree.

1. Inspect `git status --short`, relevant references, commits exclusive to the head, and the merge base. Use resolved SHAs in comparisons:

   ```text
   git merge-base <base-sha> <head-sha>
   git log --format=fuller <base-sha>..<head-sha> --
   git diff --find-renames --stat <base-sha>...<head-sha> --
   git diff --find-renames --name-status <base-sha>...<head-sha> --
   git diff --find-renames <base-sha>...<head-sha> --
   ```

2. Treat the three-dot diff as the proposed change since the common ancestor. Read significant final-state files from the head with `git show <head-sha>:<path>` when another branch is active. Commit messages provide context but do not override the code.
3. Cover every changed responsibility. For large branches, group changes by purpose and inspect each significant area; do not rely only on statistics, commit titles, or a sample that hides other changes.
4. Exclude staged, unstaged, and untracked working-tree content because it is not part of the head commit. If relevant, mention it as pending rather than delivered.
5. If the references have no merge base, required history is unavailable, or the diff is empty, explain the limitation instead of fabricating a PR.
6. Attribute validation evidence accurately. Results from another revision, branch, or locally modified tree do not prove this head.
7. Do not run an entire suite merely to draft text. Run proportionate checks only when useful, safe, and within the user's request. Never run migrations, seeds, model downloads, deployments, or external services as implicit PR validation.

## Project context

Use these scopes only when one owner accurately describes the full result: `api`, `inference`, `ml`, `infra`, `platform`, `docs`, or `repo`. Omit the scope for heterogeneous work instead of combining scopes.

- The API owns privacy orchestration, canonical taxonomy mapping, detector fusion, policy evaluation, de-identification, administration contracts, and PostgreSQL persistence.
- The inference service owns model discovery and native ML execution. It must not be described as owning global taxonomy mapping or protection policy unless the final diff truly changes that boundary.
- Use `platform` only for one inseparable behavior coordinated across components.
- Treat a proof of concept as `experiment`, not `feat`, until its production behavior is integrated and verifiable.
- Do not imply irreversible anonymization: distinguish detection, masking, pseudonymization, and de-identification according to the actual implementation.
- Do not add requirement, issue, or study identifiers unless their association is established by repository evidence or by the user.

## Write for the reviewer

Read [the PR writing format and criteria](references/pr-writing.md) before drafting the body.

- Always write the complete pull request title and body, including headings, in English, regardless of the language used in the request or conversation. This project convention cannot be overridden by a request for another output language.
- Write a concise imperative title without a final period. Use the repository's Conventional Commit types when accurate: `feat`, `fix`, `refactor`, `test`, `docs`, `build`, `chore`, `experiment`, or `data`.
- Explain the problem, final solution, boundaries, and consequences for a reviewer who has not read the conversation.
- Describe effects and decisions. Include stable relative links only when they materially improve review; do not reproduce inventories of files or commits.
- Keep observations separate from inference. Do not invent historical causes, performance gains, security guarantees, compatibility claims, screenshots, metrics, approvals, links, CI results, or rollback procedures.
- Never expose secrets or personal data, and do not add AI attribution or co-author lines.

## Copy-pasteable output

When evidence is sufficient, return only these labels and blocks unless the user asks for explanation:

Title

```text
<final title>
```

Description

```text
<final Markdown body>
```

Do not repeat the title in the body. Keep Markdown headings literal inside the second block. If the body contains fenced code, use a longer outer fence. If the user asks only for the description, return only its `text` block.

Before responding, verify that the proposal covers the complete head-to-base diff, excludes pending local work, and labels every validation claim with applicable evidence. Omit empty optional sections and generic checklists.
