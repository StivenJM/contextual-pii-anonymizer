"""Reusable audit primitives for the Contextual PII Anonymizer datasets.

The module reads the artifacts that describe a dataset (raw JSONL documents,
word-level BIO examples, and CoNLL files) and returns plain Python structures.
It performs no plotting and no formatting: notebooks and reports consume the
returned values so that every number shown in a report can be recomputed.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

O_TAG = "O"
B_PREFIX = "B-"
I_PREFIX = "I-"
BINARY_SUFFIXES = {".xlsx", ".xls", ".pdf", ".png", ".jpg", ".zip"}
WORD_RE = re.compile(r"\S+")
PUNCTUATION_TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
NON_WORD_RE = re.compile(r"^[\W_]+$", re.UNICODE)


@dataclass(frozen=True)
class FileEntry:
    """One file found inside a dataset directory."""

    path: str
    size_bytes: int
    lines: int | None
    suffix: str


@dataclass(frozen=True)
class Document:
    """A raw document as stored in ``dataset.jsonl``."""

    id: int | str
    document_type: str
    text: str
    declared_fields: tuple[str, ...]
    values: dict[str, str]
    word_count: int
    coverage: float | None
    missing_fields: tuple[str, ...]


@dataclass(frozen=True)
class Example:
    """A word-level BIO example as stored in ``etiquetado/*.jsonl``."""

    id: int | str
    document_type: str
    tokens: tuple[str, ...]
    tags: tuple[str, ...]

    @property
    def text(self) -> str:
        return " ".join(self.tokens)


def normalize(text: str) -> str:
    """Return a comparable form: case-folded, accent-free, single-spaced."""
    decomposed = unicodedata.normalize("NFD", text.casefold())
    without_accents = "".join(
        char for char in decomposed if unicodedata.category(char) != "Mn"
    )
    return " ".join(without_accents.split())


def tokenize(text: str) -> list[str]:
    return WORD_RE.findall(text)


def tokenize_punctuation(text: str) -> list[str]:
    """Split words from punctuation, the scheme used by the BIO examples."""
    return PUNCTUATION_TOKEN_RE.findall(text)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def file_inventory(root: Path) -> list[FileEntry]:
    """List every file below ``root`` with size and, for text, line count."""
    entries: list[FileEntry] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        suffix = path.suffix.lower()
        lines: int | None = None
        if suffix not in BINARY_SUFFIXES:
            with path.open(encoding="utf-8", errors="replace") as handle:
                lines = sum(1 for _ in handle)
        entries.append(
            FileEntry(
                path=path.relative_to(root).as_posix(),
                size_bytes=path.stat().st_size,
                lines=lines,
                suffix=suffix,
            )
        )
    return entries


def _document_from_record(record: dict[str, Any]) -> Document:
    return Document(
        id=record.get("id"),
        document_type=str(record.get("tipo_documento", "")),
        text=str(record.get("texto", "")),
        declared_fields=tuple(record.get("pii_incluida") or ()),
        values={
            key: str(value) for key, value in (record.get("valores_pii") or {}).items()
        },
        word_count=int(record.get("num_palabras") or 0),
        coverage=record.get("cobertura_pii"),
        missing_fields=tuple(record.get("pii_faltante") or ()),
    )


def _example_from_record(record: dict[str, Any]) -> Example:
    return Example(
        id=record.get("id"),
        document_type=str(record.get("tipo_documento", "")),
        tokens=tuple(record.get("tokens") or ()),
        tags=tuple(record.get("ner_tags") or ()),
    )


def load_documents(path: Path) -> list[Document]:
    return [_document_from_record(record) for record in iter_jsonl(path)]


def load_examples(path: Path) -> list[Example]:
    return [_example_from_record(record) for record in iter_jsonl(path)]


def load_splits(
    etiquetado_dir: Path, splits: Sequence[str] = ("train", "val", "test")
) -> dict[str, list[Example]]:
    return {split: load_examples(etiquetado_dir / f"{split}.jsonl") for split in splits}


def read_label_vocabulary(path: Path) -> tuple[str, ...]:
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )


def schema_report(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Describe the fields, presence, and runtime types of JSONL records."""
    total = 0
    presence: Counter[str] = Counter()
    types: dict[str, Counter[str]] = {}

    for record in records:
        total += 1
        for field, value in record.items():
            presence[field] += 1
            types.setdefault(field, Counter())[type(value).__name__] += 1

    return {
        field: {
            "count": presence[field],
            "coverage": presence[field] / total if total else 0.0,
            "types": dict(types[field]),
        }
        for field in presence
    }


def document_type_counts(records: Iterable[Any]) -> Counter[str]:
    return Counter(record.document_type for record in records)


def iter_entities(example: Example) -> Iterator[tuple[str, tuple[str, ...], int]]:
    """Yield ``(entity_type, tokens, start_index)`` for each BIO entity."""
    entity_type: str | None = None
    buffer: list[str] = []
    start = 0

    for index, (token, tag) in enumerate(
        zip(example.tokens, example.tags, strict=False)
    ):
        if tag == O_TAG or tag.startswith(B_PREFIX):
            if entity_type is not None:
                yield entity_type, tuple(buffer), start
            entity_type = tag[len(B_PREFIX) :] if tag.startswith(B_PREFIX) else None
            buffer = [token] if entity_type is not None else []
            start = index
        elif tag.startswith(I_PREFIX):
            current = tag[len(I_PREFIX) :]
            if entity_type == current:
                buffer.append(token)
            else:
                if entity_type is not None:
                    yield entity_type, tuple(buffer), start
                entity_type = current
                buffer = [token]
                start = index

    if entity_type is not None:
        yield entity_type, tuple(buffer), start


def class_counts(examples: Iterable[Example]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for example in examples:
        for entity_type, _, _ in iter_entities(example):
            counts[entity_type] += 1
    return counts


def class_document_counts(examples: Iterable[Example]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for example in examples:
        counts.update({entity_type for entity_type, _, _ in iter_entities(example)})
    return counts


def entity_token_lengths(examples: Iterable[Example]) -> list[int]:
    return [
        len(tokens) for example in examples for _, tokens, _ in iter_entities(example)
    ]


def documents_without_entities(examples: Iterable[Example]) -> int:
    return sum(
        1 for example in examples if not any(tag != O_TAG for tag in example.tags)
    )


def document_lengths(examples: Iterable[Example]) -> list[int]:
    return [len(example.tokens) for example in examples]


def length_stats(values: Sequence[int]) -> dict[str, float]:
    """Return descriptive statistics without requiring a numeric library."""
    if not values:
        return {"count": 0}
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min": float(ordered[0]),
        "p50": percentile(ordered, 50),
        "p90": percentile(ordered, 90),
        "p99": percentile(ordered, 99),
        "max": float(ordered[-1]),
        "mean": sum(ordered) / len(ordered),
    }


def percentile(ordered: Sequence[int], fraction: float) -> float:
    """Linear-interpolation percentile over an already sorted sequence."""
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * fraction / 100
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float(ordered[lower] * (1 - weight) + ordered[upper] * weight)


def bio_violations(
    examples: Iterable[Example], vocabulary: Sequence[str]
) -> Counter[str]:
    """Count structural BIO problems that make tags untrainable as-is."""
    allowed = set(vocabulary)
    problems: Counter[str] = Counter()

    for example in examples:
        open_type: str | None = None
        for tag in example.tags:
            if tag != O_TAG and tag not in allowed:
                problems["unknown_tag"] += 1
                continue
            if tag.startswith(I_PREFIX) and tag[len(I_PREFIX) :] != open_type:
                problems["orphan_inside_tag"] += 1
            if tag.startswith(B_PREFIX):
                open_type = tag[len(B_PREFIX) :]
            elif tag == O_TAG:
                open_type = None

    return problems


def punctuation_entities(examples: Iterable[Example]) -> Counter[str]:
    """Count entities whose surface text carries no alphanumeric character."""
    flagged: Counter[str] = Counter()
    for example in examples:
        for entity_type, tokens, _ in iter_entities(example):
            surface = " ".join(tokens)
            if NON_WORD_RE.match(surface):
                flagged[entity_type] += 1
    return flagged


def _prefix_key(text: str, size: int = 10) -> tuple[str, ...] | None:
    words = normalize(text).split()
    if len(words) < size:
        return None
    return tuple(words[:size])


def duplicate_report(
    records: Iterable[Any], jaccard_threshold: float = 0.9
) -> dict[str, Any]:
    """Detect exact, normalized, and near-duplicate documents.

    Near-duplicates are candidates that share their opening ten words and reach
    a token-set Jaccard similarity above ``jaccard_threshold``.
    """
    materialized = list(records)
    texts = [record.text for record in materialized]
    normalized = [normalize(text) for text in texts]

    exact_groups = _group_indexes(texts, lambda item: item)
    normalized_groups = _group_indexes(normalized, lambda item: item)
    prefix_groups = _group_indexes(normalized, _prefix_key)

    near_pairs: list[tuple[int, int, float]] = []
    for indexes in prefix_groups:
        for left_position, left in enumerate(indexes):
            left_tokens = set(normalized[left].split())
            for right in indexes[left_position + 1 :]:
                right_tokens = set(normalized[right].split())
                union = left_tokens | right_tokens
                if not union:
                    continue
                similarity = len(left_tokens & right_tokens) / len(union)
                if similarity >= jaccard_threshold:
                    near_pairs.append((left, right, similarity))

    return {
        "documents": len(materialized),
        "exact_duplicate_groups": sum(1 for group in exact_groups if len(group) > 1),
        "exact_duplicate_documents": sum(
            len(group) for group in exact_groups if len(group) > 1
        ),
        "exact_duplicate_samples": exact_groups[:5],
        "normalized_duplicate_groups": sum(
            1 for group in normalized_groups if len(group) > 1
        ),
        "normalized_duplicate_documents": sum(
            len(group) for group in normalized_groups if len(group) > 1
        ),
        "near_duplicate_pairs": len(near_pairs),
        "near_duplicate_samples": near_pairs[:5],
        "near_duplicate_threshold": jaccard_threshold,
    }


def _group_indexes(items: Sequence[Any], key: Any) -> list[list[int]]:
    groups: dict[Any, list[int]] = {}
    for index, item in enumerate(items):
        group_key = key(item)
        if group_key is None:
            continue
        groups.setdefault(group_key, []).append(index)
    return [group for group in groups.values() if len(group) > 1]


def partition_report(splits: dict[str, Sequence[Example]]) -> dict[str, Any]:
    """Compare identifiers, texts, and document types across partitions."""
    names = list(splits)
    ids = {name: {example.id for example in splits[name]} for name in names}
    texts = {
        name: {normalize(example.text) for example in splits[name]} for name in names
    }

    overlap = {
        f"{left}->{right}": {
            "ids": len(ids[left] & ids[right]),
            "texts": len(texts[left] & texts[right]),
        }
        for position, left in enumerate(names)
        for right in names[position + 1 :]
    }

    return {
        "sizes": {name: len(splits[name]) for name in names},
        "identifier_overlap": overlap,
        "within_split_duplicate_texts": {
            name: len(splits[name]) - len(texts[name]) for name in names
        },
        "document_types": {
            name: dict(document_type_counts(splits[name])) for name in names
        },
    }


def grounding_report(documents: Sequence[Document]) -> dict[str, Any]:
    """Check that declared PII values actually appear in the document text."""
    declared_but_missing: Counter[str] = Counter()
    empty_values: Counter[str] = Counter()
    not_in_text: Counter[str] = Counter()
    documents_with_gaps = 0

    for document in documents:
        normalized_text = normalize(document.text)
        gap_found = False

        for field in document.declared_fields:
            if field not in document.values:
                declared_but_missing[field] += 1
                gap_found = True
                continue
            value = document.values[field]
            if not normalize(value):
                empty_values[field] += 1
                gap_found = True
                continue
            if normalize(value) not in normalized_text:
                not_in_text[field] += 1
                gap_found = True

        documents_with_gaps += int(gap_found)

    return {
        "documents": len(documents),
        "documents_with_gaps": documents_with_gaps,
        "declared_but_missing": dict(declared_but_missing),
        "empty_values": dict(empty_values),
        "not_in_text": dict(not_in_text),
    }


def value_reuse_report(
    documents: Sequence[Document],
    partition_of: dict[Any, str],
) -> list[dict[str, Any]]:
    """Measure how often each declared field reuses the same value across documents.

    ``partition_of`` maps a document identifier to its split name so that reuse
    inside one split can be separated from reuse across splits, which is the
    leakage channel that grouped splitting must control.
    """
    values_per_field: dict[str, dict[str, set[Any]]] = {}
    for document in documents:
        for field, value in document.values.items():
            normalized = normalize(value)
            if not normalized:
                continue
            values_per_field.setdefault(field, {}).setdefault(normalized, set()).add(
                document.id
            )

    rows: list[dict[str, Any]] = []
    for field in sorted(values_per_field):
        owners = values_per_field[field]
        reused = {
            value: identifiers
            for value, identifiers in owners.items()
            if len(identifiers) > 1
        }
        cross_split = {
            value: identifiers
            for value, identifiers in reused.items()
            if len(
                {partition_of.get(identifier, "unknown") for identifier in identifiers}
            )
            > 1
        }
        rows.append(
            {
                "field": field,
                "distinct_values": len(owners),
                "reused_values": len(reused),
                "cross_split_values": len(cross_split),
                "max_documents_per_value": max(
                    (len(ids) for ids in owners.values()), default=0
                ),
            }
        )
    return rows


def declaration_consistency(documents: Sequence[Document]) -> dict[str, Any]:
    """Compare declared PII fields against the labels that carry values."""
    mismatches: Counter[str] = Counter()
    for document in documents:
        declared = set(document.declared_fields)
        labelled = set(document.values)
        mismatches["declared_without_value"] += len(declared - labelled)
        mismatches["value_without_declaration"] += len(labelled - declared)

    coverage = [
        document.coverage for document in documents if document.coverage is not None
    ]
    return {
        "mismatches": dict(mismatches),
        "documents_with_missing_fields": sum(
            1 for document in documents if document.missing_fields
        ),
        "coverage_stats": length_stats([round(value * 100) for value in coverage]),
    }
