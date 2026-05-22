"""Command-line entrypoint for the contextual anonymizer."""

from __future__ import annotations

import argparse
import json
import sys

from contextual_pii_anonymizer import process_text
from contextual_pii_anonymizer.evaluation import evaluate_scenarios


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "anonymize":
        result = process_text(args.text)
    elif args.command == "evaluate":
        result = evaluate_scenarios(args.scenarios)
    else:
        parser.print_help()
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contextual-pii-anonymizer",
        description="Capa intermedia contextual para desidentificar datos sensibles en texto academico.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    anonymize_parser = subparsers.add_parser("anonymize", help="Procesa y desidentifica un texto.")
    anonymize_parser.add_argument("text", help="Texto original que se desea procesar.")

    evaluate_parser = subparsers.add_parser("evaluate", help="Evalua escenarios anotados en JSON.")
    evaluate_parser.add_argument(
        "scenarios",
        nargs="?",
        default="data/escenarios_iniciales.json",
        help="Ruta del archivo JSON de escenarios anotados.",
    )

    return parser


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
