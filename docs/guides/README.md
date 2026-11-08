# Development guides

These guides explain recurring procedures to prepare and operate the project during development.

## Start here

- [Install the extension and start the development system](developer-startup.md): extension installation first, then the separate research-only or attachment/protection startup sequence.

## Data

- [`Datasets and audits`](datasets-and-audits.md): registers a dataset with DVC and turns each audit into reviewable, reproducible evidence.

## Workflow

- [`Branch names`](nombres-de-ramas.md): defines how to identify the type, scope, and result of each work branch in the monorepo.

## Code quality

- [`Code quality with Ruff`](calidad-de-codigo-con-ruff.md): runs linting, formatting, and quality checks with `uv`.

## Testing

- [`Integration testing`](integration-testing.md): runs the browser extension suite against local pages and, optionally, the full Compose stack.

## Local environment

- [`Local infrastructure with Docker`](infraestructura-local-con-docker.md): operates the current development database, inference and API containers, their private networks and persistent volumes.

## Research collection

- [Model-free research capture](research-capture.md): runs the separate local API and extension capture mode, with access, retry and withdrawal procedures.
- [University-network deployment](research-campus-deployment.md): prepares separate production Docker, private-IP HTTPS/client trust and a participant-specific endpoint package.
- [Student study kit](../project/experimentacion/research-study/README.md): evidence, scenario cards, proposed protocol, instruments and analysis/reporting materials.
- [Security risk review draft](../project/experimentacion/research-study/security-risk-review.md): remaining risks, proportional storage-encryption assessment and owner decisions still pending.
