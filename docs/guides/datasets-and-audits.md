# Datasets and audits

**Objective.** This guide defines how a dataset enters the repository, where its files live, how it is audited, and
how the evidence is delivered for review. Apply the same organisation to every new dataset; adapt the checks to the
data, not the structure.

**Intended reader.** Anyone adding a dataset, preparing data, or reviewing an audit before the project moves to
training.

## Principles

1. **One dataset is one unit.** Payload, preparation code, audit notebook, figures, and report are attributable to a
   single dataset. Nothing that belongs to a dataset lives in a shared, ambiguous folder.
2. **Git versions meaning, DVC versions bytes.** Large payloads are stored outside Git; Git keeps the metadata that
   identifies the exact version.
3. **An audit is read-only.** Audits measure and document. They never repair, deduplicate, or rewrite the frozen
   version. Fixes belong to a later dataset version.
4. **Evidence must be reproducible.** Every number in a report is produced by an executable artifact stored with it,
   not copied by hand from an interactive session.
5. **A notebook must explain itself.** A reviewer opens the notebook (or its PDF) with no prior conversation and
   understands what was measured, why it matters, and what follows.
6. **Only useful artifacts are versioned.** Transformation code, notebooks with their outputs, reports, figures, and
   the dataset card are versioned. Payloads, environments, caches, and generated PDFs are not.

## Workspace layout

The layout is stable across datasets. Replace `<dataset>` with the dataset name.

```
ml/
├── data/
│   ├── raw/<payload>              # DVC payload (not versioned in Git)
│   └── processed/<payload>        # Derived payload (not versioned in Git)
├── src/pii_ml/data/
│   ├── audit.py                   # Reusable statistics and detection
│   └── validation.py              # Reusable structural and annotation checks
├── datasets/
│   └── <dataset>/
│       ├── README.md              # Dataset card
│       ├── notebooks/
│       │   └── NNN_<purpose>.ipynb
│       └── reports/
│           ├── <purpose>_v<N>.md
│           └── figures/
│               └── NNN_<name>.png
├── scripts/
│   └── render_report_pdf.py       # Markdown report to PDF
├── pyproject.toml                 # Environment and tooling
├── uv.lock
└── .gitignore
```

`data/` holds payloads managed by DVC. `src/pii_ml/` holds code that is genuinely reusable across datasets.
`datasets/<dataset>/` holds everything that describes or analyses one dataset. A check used by a single dataset stays
inside its folder until a second dataset needs it; then it moves to `src/pii_ml/` with tests.

The workspace overview lives in [`ml/README.md`](../../ml/README.md).

## Prerequisites

| Tool | Use |
|---|---|
| `uv` | Creates the environment and runs code from `ml/` |
| `dvc` | Tracks and transfers dataset payloads |
| Chromium browser (Chrome or Edge) | Renders reports to PDF without LaTeX |

```powershell
cd ml
uv sync
dvc version
```

All dataset commands run from `ml/`, the DVC root of this workspace.

## 1. Register or locate the dataset

If the payload already exists and is tracked, skip to restoring it. To add a new payload:

```powershell
cd ml
dvc add data/raw/<file-or-directory>
git add data/raw/<file-or-directory>.dvc data/raw/.gitignore
```

`dvc add` writes `<name>.dvc` with the content hash, size, and file count, and DVC adds the payload path to
`data/raw/.gitignore`. Commit the `.dvc` file; never commit the payload. The `.dvc` metadata is the identity of the
dataset version, so a later audit always states which hash it read.

## 2. Configure the remote per machine

A remote tells DVC where the bytes live. The remote URL can contain credentials or machine-specific paths, so it
must stay outside Git:

```powershell
cd ml
dvc remote add --local -d <remote-name> <remote-url>
dvc remote list --local
```

- `--local` writes `.dvc/config.local`, which DVC keeps untracked. Commit `.dvc/config` only when the remote
  configuration is genuinely shareable and credential-free.
- Supported forms include a local or mounted directory (`D:\dvc-storage`, a synced Drive folder) and a native
  backend such as `gdrive://<folder-id>`. Native backends need their own authentication and may require extra
  dependencies.
- Never place tokens, service-account JSON, or personal filesystem paths in documentation, commits, or notebooks.

Check before continuing that `git status` does not list the remote configuration or any credential file.

## 3. Restore and verify the payload

```powershell
cd ml
dvc pull data/raw/<file-or-directory>.dvc
dvc status data/raw/<file-or-directory>.dvc
```

`dvc status` must report that data is up to date. Then reconcile the working copy with the metadata: file count and
total size should match the numbers in the `.dvc` file. A mismatch means the working copy is not the frozen version;
do not run the audit until it matches.

## 4. Write the dataset card

Create `datasets/<dataset>/README.md` before analysing. It is the entry point that survives after the audit:

- Dataset identity: DVC version (hash), file count, total size.
- What the dataset contains and which formats it uses.
- Contents table: one row per artifact with its purpose.
- Restore command.
- How to reproduce the audit.
- Known characteristics and open issues.
- Links to the notebook and the report.

The card states facts that are stable. Detailed measurements belong to the report, not the card.

## 5. Inspect before writing code

Read a sample of every artifact first. Identify:

- Files, formats, sizes, and encodings.
- Record schema: fields, types, identifiers, and how artifacts join.
- Partition structure and label vocabulary.
- What the dataset declares about itself that can be verified independently.

From that inspection, decide which audit questions apply. The default question set is below; keep what the dataset
supports, drop what it does not, and add domain-specific checks when the data has a contract worth verifying.

| Question | Typical evidence |
|---|---|
| What does the dataset contain? | File inventory, sizes, record counts |
| What is the record contract? | Field presence, types, joins |
| Is the data structurally valid? | Missing fields, duplicates, length agreement, grammar |
| What labels exist? | Declared versus observed classes |
| How is the data distributed? | Class frequency, document types, lengths, imbalance |
| Are there duplicates? | Exact, normalized, near-duplicate candidates |
| Are partitions isolated and comparable? | Identifier and text overlap, class presence |
| Are annotations correct? | Boundary validity, grounding against declared values |
| What coverage exists? | Rare and absent classes per partition |
| Is the dataset ready for the next phase? | Verdict with explicit conditions |

## 6. Extend the reusable modules only when justified

`pii_ml.data.audit` returns plain data: inventory, schema, counts, lengths, duplicates, partitions, reuse, and
grounding. `pii_ml.data.validation` returns aggregated issues with a severity, a code, and samples.

Rules:

- Return data, not formatted text. Notebooks and reports format results.
- Aggregate findings; never print one line per defective record.
- Keep every function independent of a specific dataset path; pass paths as arguments.
- Add a function to `src/pii_ml/` only when it is dataset-agnostic. Otherwise keep it in the dataset notebook or a
  dataset-local script.
- Run the linter after changes:

```powershell
cd ml
uv run ruff check src
uv run ruff format --check src
```

## 7. Write the audit notebook

Place it at `datasets/<dataset>/notebooks/NNN_<purpose>.ipynb`. A reviewer must be able to read it as a standalone
document.

Required content:

1. **Title and purpose** — what the audit answers and which decisions it supports.
2. **Audience** — who reviews it and what they need in order to approve the next phase.
3. **Dataset identity** — DVC hash, file count, size, and the date or commit of the run when relevant.
4. **How to run** — environment, command, and kernel, inside the notebook.
5. **Definitions** — every domain term the reader needs (record, label, split, coverage, duplicate).
6. **Scope and method** — what is measured, what is deliberately not done, and why.
7. **One section per question** — each answers what is measured, why it matters, and how to read the result.
8. **Conclusions and limitations** — what the evidence supports and what it cannot prove.
9. **Next steps** — concrete decisions the next phase must take.

Rules:

- Read-only: never write into `data/`.
- Compute paths relative to the workspace; never hardcode a machine path.
- Save figures with deterministic names to `reports/figures/`; each figure must have a title and labelled axes.
- Keep interpretation consistent with the computed values. If a threshold changes, update the text that cites it.
- Do not depend on outside narration, chat history, or a separate explanation document.
- Version the notebook **with its outputs** so the evidence is visible without re-running it.

## 8. Execute and store the evidence

```powershell
cd ml
uv run jupyter nbconvert --to notebook --execute --inplace `
  datasets/<dataset>/notebooks/<notebook>.ipynb
```

Commit the executed notebook and the generated figures. If execution fails, fix the code or the environment; do not
commit a notebook with error outputs.

## 9. Write the report

Place it at `datasets/<dataset>/reports/<purpose>_v<N>.md`. The report is the reviewable decision artifact; the
notebook is its evidence.

Required structure:

1. **Header table** — status, dataset version, files and size, record counts, evidence links.
2. **Verdict** — ready or not, with explicit conditions.
3. **Method and reproducibility** — modules, commands, runtime, and what was read-only.
4. **Findings by question** — tables and the figures that support them.
5. **Limitations** — what the checks cannot detect.
6. **Recommendations** — decisions the next phase must take, in priority order.
7. **Gate** — what must be true before the dataset moves forward.

Rules:

- Every number must be traceable to a notebook cell.
- Separate measured facts from interpretation; do not claim guarantees the checks cannot support.
- State the dataset version the report refers to. A new version needs a new report.
- Write the report in English with consistent section and table labels.

## 10. Render the PDF for review

The PDF is a generated artifact and is not versioned. It embeds the figures so a reviewer can read one file.

```powershell
cd ml
uv run python scripts/render_report_pdf.py datasets/<dataset>/reports/<report>.md
```

The script converts Markdown to styled A4 HTML, embeds relative images, and prints it with headless Chrome or Edge.
Use `--browser <path>` when the browser is not in a standard location, and `--output <path>` to change the
destination. Keep the Markdown report as the source of truth; never edit the PDF.

## Versioning rules

| Commit | Ignore |
|---|---|
| `.dvc` metadata | Dataset payloads under `data/` |
| Dataset card | `.venv/`, `__pycache__/`, `*.egg-info/` |
| Notebook with outputs | `.ipynb_checkpoints/` |
| Report Markdown and figures | Generated report PDFs and HTML |
| Reusable audit and validation code | Local DVC configuration and credentials |
| `pyproject.toml` and `uv.lock` | Machine-specific paths |

The workspace `.gitignore` already covers environments, caches, notebook checkpoints, and generated reports. Extend
it only for new artifact types, and prefer narrow patterns over global ones.

## Naming conventions

| Artifact | Pattern | Example |
|---|---|---|
| Dataset folder | `datasets/<dataset>/` | `datasets/<dataset>/` |
| Notebook | `NNN_<purpose>.ipynb` | `001_dataset_audit.ipynb` |
| Report | `<purpose>_v<N>.md` | `dataset_audit_v1.md` |
| Figure | `NNN_<name>.png` | `001_document_types.png` |
| Dataset-local script | `scripts/<verb>_<object>.py` | `scripts/convert_csv_to_jsonl.py` |

Use lowercase, hyphen-free folder names that match the DVC artifact name, so metadata, payload, and artifacts are
easy to correlate.

## Hand-off checklist

- [ ] Payload restored and `dvc status` clean.
- [ ] Working copy matches the metadata file count and size.
- [ ] Dataset card written with identity, contents, and reproduction steps.
- [ ] Reusable checks extended only where they generalise; linter passes.
- [ ] Notebook is self-contained, read-only, and executed with outputs committed.
- [ ] Figures saved under `reports/figures/` with deterministic names.
- [ ] Report states the dataset version, verdict, conditions, and limitations.
- [ ] PDF rendered for review and left untracked.
- [ ] `git status` shows no payload, credential, environment, or generated PDF.
- [ ] Navigation updated in this guide area if a new convention was introduced.

## Troubleshooting

| Symptom | Cause | Action |
|---|---|---|
| `no remote` when pulling | Remote configured only on another machine | Configure it locally with `--local` |
| Pull succeeds but files mismatch metadata | Working copy belongs to another version | Re-pull the specific `.dvc` file; do not re-add blindly |
| Notebook cannot import `pii_ml` | Notebook running outside the `ml` environment | Select the `ml` environment kernel after `uv sync` |
| PDF not created | No Chromium browser found | Pass `--browser` explicitly |
| Mojibake in terminal output | Console encoding, not file content | Read files with explicit UTF-8; verify with Python |
| Huge files stall an editor | Payload opened directly | Stream JSONL and inspect samples instead |
| Report numbers disagree with the notebook | Text copied instead of recomputed | Re-run the notebook and update the report |

## Evolving this process

- A new dataset type (tabular, audio, images) may need new inventory and validation functions. Add them to
  `src/pii_ml/` only when they generalise, and keep dataset-specific assumptions in the dataset folder.
- A new question belongs in the audit only if it changes a decision. Document why it was added in the notebook.
- When the structure itself changes, update this guide and the workspace `README.md` in the same change so the next
  dataset starts from a correct description.
