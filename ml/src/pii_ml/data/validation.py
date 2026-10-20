"""Structural and annotation validation for the Contextual PII Anonymizer datasets.

Validation reports problems; it never modifies the dataset. Each check returns
``Issue`` records so that a notebook or report can decide how to present them.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pii_ml.data.audit import (
    Example,
    bio_violations,
    iter_jsonl,
    load_documents,
    load_splits,
    normalize,
    read_label_vocabulary,
    tokenize,
    tokenize_punctuation,
)

Severity = Literal["error", "warning"]

REQUIRED_DOCUMENT_FIELDS = (
    "id",
    "tipo_documento",
    "pii_incluida",
    "valores_pii",
    "texto",
    "num_palabras",
    "cobertura_pii",
    "pii_faltante",
)
REQUIRED_EXAMPLE_FIELDS = ("id", "tipo_documento", "tokens", "ner_tags")

EXPECTED_DOCUMENT_TYPES: dict[str, Any] = {
    "id": (int, str),
    "tipo_documento": str,
    "pii_incluida": list,
    "valores_pii": dict,
    "texto": str,
    "num_palabras": int,
    "cobertura_pii": (int, float),
    "pii_faltante": list,
}
EXPECTED_EXAMPLE_TYPES: dict[str, Any] = {
    "id": (int, str),
    "tipo_documento": str,
    "tokens": list,
    "ner_tags": list,
}


@dataclass(frozen=True)
class Issue:
    """One aggregated validation finding."""

    severity: Severity
    code: str
    message: str
    count: int
    samples: tuple[str, ...] = field(default_factory=tuple)


def _issue(
    severity: Severity,
    code: str,
    message: str,
    samples: Sequence[str] = (),
    count: int | None = None,
) -> Issue:
    return Issue(
        severity=severity,
        code=code,
        message=message,
        count=count if count is not None else len(samples),
        samples=tuple(samples[:5]),
    )


def _missing_or_mistyped(
    record: dict[str, Any],
    required: Sequence[str],
    expected: dict[str, Any],
) -> tuple[list[str], list[str]]:
    missing = [name for name in required if name not in record]
    mistyped = [
        name
        for name in required
        if name in record and not isinstance(record[name], expected.get(name, object))
    ]
    return missing, mistyped


def validate_documents(path: Path) -> list[Issue]:
    """Validate the raw ``dataset.jsonl`` contract."""
    issues: list[Issue] = []
    missing: list[str] = []
    mistyped: list[str] = []
    duplicate_ids: Counter[Any] = Counter()
    mismatched_word_counts: list[str] = []
    empty_texts: list[str] = []

    total = 0
    for record in iter_jsonl(path):
        total += 1
        record_missing, record_mistyped = _missing_or_mistyped(
            record, REQUIRED_DOCUMENT_FIELDS, EXPECTED_DOCUMENT_TYPES
        )
        missing.extend(record_missing)
        mistyped.extend(record_mistyped)
        if not record_missing:
            duplicate_ids[record["id"]] += 1
            text = record["texto"]
            if not text.strip():
                empty_texts.append(str(record["id"]))
            expected_words = record["num_palabras"]
            actual_words = len(tokenize(text))
            if expected_words != actual_words:
                mismatched_word_counts.append(
                    f"id={record['id']} declared={expected_words} actual={actual_words}"
                )

    if missing:
        issues.append(
            _issue(
                "error",
                "document_field_missing",
                "Required fields are absent.",
                sorted(set(missing)),
            )
        )
    if mistyped:
        issues.append(
            _issue(
                "error",
                "document_field_type",
                "Required fields have unexpected types.",
                sorted(set(mistyped)),
            )
        )
    if total == 0:
        issues.append(
            _issue(
                "error",
                "document_empty_file",
                "The document file contains no records.",
                count=1,
            )
        )
    duplicated = [str(key) for key, count in duplicate_ids.items() if count > 1]
    if duplicated:
        issues.append(
            _issue(
                "error",
                "document_duplicate_id",
                "Identifiers are not unique.",
                duplicated,
            )
        )
    if empty_texts:
        issues.append(
            _issue(
                "error",
                "document_empty_text",
                "Documents have empty text.",
                empty_texts,
            )
        )
    if mismatched_word_counts:
        issues.append(
            _issue(
                "warning",
                "document_word_count_mismatch",
                "Declared num_palabras differs from whitespace tokenization.",
                mismatched_word_counts,
            )
        )
    return issues


def validate_examples(path: Path, vocabulary: Sequence[str]) -> list[Issue]:
    """Validate a word-level BIO split."""
    issues: list[Issue] = []
    missing: list[str] = []
    mistyped: list[str] = []
    length_mismatch: list[str] = []
    empty: list[str] = []
    duplicate_ids: Counter[Any] = Counter()
    blank_tokens: list[str] = []
    examples: list[Example] = []

    for record in iter_jsonl(path):
        record_missing, record_mistyped = _missing_or_mistyped(
            record, REQUIRED_EXAMPLE_FIELDS, EXPECTED_EXAMPLE_TYPES
        )
        missing.extend(record_missing)
        mistyped.extend(record_mistyped)
        if record_missing:
            continue

        example = Example(
            id=record["id"],
            document_type=record["tipo_documento"],
            tokens=tuple(record["tokens"]),
            tags=tuple(record["ner_tags"]),
        )
        examples.append(example)
        duplicate_ids[example.id] += 1
        if len(example.tokens) != len(example.tags):
            length_mismatch.append(
                f"id={example.id} tokens={len(example.tokens)} tags={len(example.tags)}"
            )
        if not example.tokens:
            empty.append(str(example.id))
        blank_tokens.extend(
            f"id={example.id}" for token in example.tokens if not token.strip()
        )

    if missing:
        issues.append(
            _issue(
                "error",
                "example_field_missing",
                "Required fields are absent.",
                sorted(set(missing)),
            )
        )
    if mistyped:
        issues.append(
            _issue(
                "error",
                "example_field_type",
                "Required fields have unexpected types.",
                sorted(set(mistyped)),
            )
        )
    if length_mismatch:
        issues.append(
            _issue(
                "error",
                "token_tag_length_mismatch",
                "Tokens and tags differ in length.",
                length_mismatch,
            )
        )
    if empty:
        issues.append(
            _issue("warning", "empty_example", "Examples without tokens.", empty)
        )
    if blank_tokens:
        issues.append(
            _issue(
                "error",
                "blank_token",
                "Tokens are empty or whitespace.",
                sorted(set(blank_tokens)),
            )
        )
    duplicated = [str(key) for key, count in duplicate_ids.items() if count > 1]
    if duplicated:
        issues.append(
            _issue(
                "error",
                "example_duplicate_id",
                "Identifiers are not unique inside the split.",
                duplicated,
            )
        )

    bio = bio_violations(examples, vocabulary)
    for code, count in bio.items():
        issues.append(
            _issue(
                "error",
                f"bio_{code}",
                "BIO sequences violate the label contract.",
                [f"{code}: {count}"],
                count=count,
            )
        )
    return issues


def validate_partitions(splits: dict[str, Sequence[Example]]) -> list[Issue]:
    """Check split sizes, identifier overlap, and text leakage."""
    issues: list[Issue] = []
    for name, examples in splits.items():
        if not examples:
            issues.append(
                _issue(
                    "error", "empty_split", f"Split '{name}' has no examples.", count=1
                )
            )

    names = list(splits)
    for position, left in enumerate(names):
        for right in names[position + 1 :]:
            shared_ids = {example.id for example in splits[left]} & {
                example.id for example in splits[right]
            }
            shared_texts = {normalize(example.text) for example in splits[left]} & {
                normalize(example.text) for example in splits[right]
            }
            if shared_ids:
                issues.append(
                    _issue(
                        "error",
                        "split_identifier_leak",
                        f"'{left}' and '{right}' share document identifiers.",
                        [str(value) for value in shared_ids],
                    )
                )
            if shared_texts:
                issues.append(
                    _issue(
                        "error",
                        "split_text_leak",
                        f"'{left}' and '{right}' share identical texts.",
                        sorted(shared_texts)[:5],
                    )
                )
    return issues


def validate_cross_artifact(root: Path) -> list[Issue]:
    """Compare the raw documents against the labelled partitions."""
    documents = load_documents(root / "dataset.jsonl")
    splits = load_splits(root / "etiquetado")
    issues: list[Issue] = []

    by_id = {document.id: document for document in documents}
    split_ids = {example.id for examples in splits.values() for example in examples}

    unlabelled = sorted(str(value) for value in set(by_id) - split_ids)
    orphaned = sorted(str(value) for value in split_ids - set(by_id))
    if unlabelled:
        issues.append(
            _issue(
                "warning",
                "document_without_example",
                "Documents have no labelled example.",
                unlabelled,
            )
        )
    if orphaned:
        issues.append(
            _issue(
                "error",
                "example_without_document",
                "Labelled examples have no source document.",
                orphaned,
            )
        )

    type_mismatch = [
        (
            f"id={example.id} example={example.document_type} "
            f"document={by_id[example.id].document_type}"
        )
        for examples in splits.values()
        for example in examples
        if example.id in by_id
        and example.document_type != by_id[example.id].document_type
    ]
    if type_mismatch:
        issues.append(
            _issue(
                "error",
                "document_type_mismatch",
                "Document types differ between artifacts.",
                type_mismatch,
            )
        )

    token_mismatch = [
        (
            f"id={example.id} tokens={len(example.tokens)} "
            f"punctuation={len(tokenize_punctuation(by_id[example.id].text))}"
        )
        for examples in splits.values()
        for example in examples
        if example.id in by_id
        and len(example.tokens) != len(tokenize_punctuation(by_id[example.id].text))
    ]
    if token_mismatch:
        issues.append(
            _issue(
                "warning",
                "tokenization_drift",
                "BIO tokens differ from punctuation-aware tokenization of the "
                "raw text.",
                token_mismatch,
            )
        )
    return issues


def validate_dataset(root: Path) -> tuple[list[Issue], dict[str, Sequence[Example]]]:
    """Run every validation check for one dataset directory."""
    vocabulary = read_label_vocabulary(root / "etiquetado" / "labels.txt")
    splits = load_splits(root / "etiquetado")

    issues = validate_documents(root / "dataset.jsonl")
    for name, _examples in splits.items():
        issues.extend(
            validate_examples(root / "etiquetado" / f"{name}.jsonl", vocabulary)
        )
    issues.extend(validate_partitions(splits))
    issues.extend(validate_cross_artifact(root))
    return issues, splits


def summarise(issues: Iterable[Issue]) -> dict[str, Any]:
    """Aggregate issues by severity for a report header."""
    materialized = list(issues)
    by_severity = Counter(issue.severity for issue in materialized)
    return {
        "total": len(materialized),
        "errors": by_severity.get("error", 0),
        "warnings": by_severity.get("warning", 0),
        "by_code": dict(Counter(issue.code for issue in materialized)),
    }
