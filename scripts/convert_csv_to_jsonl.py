from __future__ import annotations

import argparse
import csv
import json
import multiprocessing
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


LABEL_BY_COLUMN = {
    "nombre": "PER",
    "cedula": "ID",
    "telefono": "PH",
    "email": "EMAIL",
}


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    entity_type: str


@dataclass(frozen=True)
class TokenSpan:
    token: str
    start: int
    end: int


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_accents = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return unicodedata.normalize("NFC", without_accents)


def split_by_spaces_with_offsets(text: str) -> list[TokenSpan]:
    return [TokenSpan(match.group(), match.start(), match.end()) for match in re.finditer(r"\S+", text)]


def find_entity_spans(text: str, row: dict[str, str]) -> list[Span]:
    spans: list[Span] = []

    for column, entity_type in LABEL_BY_COLUMN.items():
        entity = normalize_text(row.get(column, "").strip())
        if not entity:
            continue

        start = 0
        while True:
            match_start = text.find(entity, start)
            if match_start == -1:
                break

            match_end = match_start + len(entity)
            spans.append(Span(match_start, match_end, entity_type))
            start = match_end

    return sorted(spans, key=lambda span: (span.start, -(span.end - span.start)))


def token_overlaps_span(token: TokenSpan, span: Span) -> bool:
    return token.start < span.end and token.end > span.start


def build_bio_tags(tokens: Iterable[TokenSpan], spans: Iterable[Span]) -> list[str]:
    tags: list[str] = []
    spans = list(spans)
    previous_span: Span | None = None

    for token in tokens:
        current_span = next((span for span in spans if token_overlaps_span(token, span)), None)

        if current_span is None:
            tags.append("O")
            previous_span = None
            continue

        prefix = "I" if current_span == previous_span else "B"
        tags.append(f"{prefix}-{current_span.entity_type}")
        previous_span = current_span

    return tags


def convert_row(row: dict[str, str]) -> dict[str, list[str]]:
    text = normalize_text(row["texto"].strip())
    token_spans = split_by_spaces_with_offsets(text)
    spans = find_entity_spans(text, row)

    return {
        "tokens": [token.token for token in token_spans],
        "ner_tags": build_bio_tags(token_spans, spans),
    }


def convert_csv(input_path: Path, output_path: Path, workers: int = 3) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)

        with output_path.open("w", encoding="utf-8", newline="\n") as target:
            if workers <= 1:
                for row in reader:
                    target.write(json.dumps(convert_row(row), ensure_ascii=False) + "\n")
                    count += 1
            else:
                with multiprocessing.Pool(processes=workers) as pool:
                    for example in pool.imap(convert_row, reader, chunksize=500):
                        target.write(json.dumps(example, ensure_ascii=False) + "\n")
                        count += 1

    return count


def parse_args() -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(description="Prepare word-level BIO NER data for Model 2.")
    parser.add_argument("--input", type=Path, default=base_dir / "dataset.csv")
    parser.add_argument("--output", type=Path, default=base_dir / "ner_dataset.jsonl")
    parser.add_argument("--workers", type=int, default=3, help="Number of worker processes for row conversion.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = convert_csv(args.input, args.output, workers=args.workers)
    print(f"Wrote {count} examples to {args.output}")


if __name__ == "__main__":
    main()
