# ML workspace

Datasets, audits, and experiments for the Contextual PII Anonymizer.

## Layout

| Path | Responsibility |
|---|---|
| `data/raw/`, `data/processed/` | DVC payloads. Only the `.dvc` metadata is versioned in Git. |
| `src/pii_ml/data/` | Reusable audit and validation code shared by datasets. |
| `datasets/<name>/` | Everything specific to one dataset: notebooks, reports, figures, and preparation scripts. |

A dataset is the unit of organisation. Preparation scripts, audits, and conclusions live inside its
`datasets/<name>/` directory, and the payload lives in `data/` under DVC. Files that only exist to move data around
locally are ignored; only transformation code, self-contained notebooks, and their reports are versioned.

## Environment

```powershell
cd ml
uv sync
```

`uv` creates `.venv` from `pyproject.toml` and `uv.lock`. Add dependencies with `uv add <package>`.

## Restore data

```powershell
cd ml
dvc pull
```

The DVC remote is configured per machine in `.dvc/config.local`, which is not committed. A new machine needs the
remote configured before `dvc pull` can work.

## Audits

An audit is a notebook plus a written report, both stored under the dataset they describe:

```
datasets/<name>/notebooks/001_dataset_audit.ipynb
datasets/<name>/reports/dataset_audit_v1.md
datasets/<name>/reports/figures/
```

Run a notebook in place so its outputs are committed with it:

```powershell
uv run jupyter nbconvert --to notebook --execute --inplace `
  datasets/dataset2/notebooks/001_dataset_audit.ipynb
```

Export the reviewed result to PDF with Quarto (install it separately):

```powershell
quarto render datasets/dataset2/notebooks/001_dataset_audit.ipynb --to pdf
```

Notebooks must be self-contained: purpose, dataset identity, method, definitions, results, and conclusions inside the
notebook, with no external narration required to review them.
