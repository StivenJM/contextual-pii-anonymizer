# Dataset `dataset2`

Raw corpus for PII entity recognition: long Spanish-language administrative and personal documents with word-level
BIO annotations over 29 observed entity types.

| Field | Value |
|---|---|
| DVC version | `md5 5d32321fd6706a62976cba08dff97278.dir` |
| Files / size | 10 files / 311,156,761 bytes |
| Documents | 16,144 |
| Document types | 9 |
| Entity types | 31 declared, 29 observed |
| Entities | 154,142 |
| Splits | 12,915 train / 1,614 validation / 1,615 test |
| Audit status | [Dataset Audit v1](reports/dataset_audit_v1.md) |

## Contents

| Path | Content |
|---|---|
| `dataset.jsonl` | Raw documents: text, document type, declared PII fields, concrete PII values |
| `dataset.xlsx` | Human-readable export of the same documents (not a source of truth) |
| `etiquetado/train.jsonl`, `val.jsonl`, `test.jsonl` | Word-level `tokens` and BIO `ner_tags` |
| `etiquetado/train.conll`, `val.conll`, `test.conll` | CoNLL encoding of the same partitions |
| `etiquetado/labels.txt` | Tag vocabulary: 31 `B-`, 31 `I-`, and `O` |
| `prueba.json` | Empty file kept by the frozen version; scheduled for removal |

Every document joins to exactly one labelled example through `id`.

## Restore

```powershell
cd ml
dvc pull data/raw/dataset2.dvc
```

## Reproduce the audit

```powershell
cd ml
uv sync
uv run jupyter nbconvert --to notebook --execute --inplace `
  datasets/dataset2/notebooks/001_dataset_audit.ipynb
```

Evidence: [notebook](notebooks/001_dataset_audit.ipynb) and [report](reports/dataset_audit_v1.md). Figures are written
to `reports/figures/`.

## Known characteristics

- `GENERO` and `HISTORIAL_CLINICO` are declared but never observed.
- The class distribution is imbalanced 60:1; nine classes appear in fewer than 1,000 documents.
- Documents are long: median 592 tokens, maximum 984.
- Direct identifiers are unique per document; personal names and categorical values repeat.
- BIO tokens are authoritative: they cannot always be rebuilt from raw text by tokenization.
