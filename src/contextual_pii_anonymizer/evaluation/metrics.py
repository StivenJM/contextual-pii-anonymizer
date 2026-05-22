"""Evaluation helpers for annotated experimental scenarios."""

from __future__ import annotations

import json
from pathlib import Path

from contextual_pii_anonymizer.context import SENSITIVITY_WEIGHTS
from contextual_pii_anonymizer.processing import process_text


def evaluate_scenarios(path: str | Path) -> dict:
    scenarios = json.loads(Path(path).read_text(encoding="utf-8"))
    scenario_results = []

    total_expected = 0
    total_detected = 0
    total_matches = 0
    exposure_before = 0
    exposure_after = 0

    for scenario in scenarios:
        result = process_text(scenario["texto"])
        expected = scenario.get("entidades_esperadas", [])
        detected = result["entidades"]
        matches = _count_exact_matches(expected, detected)

        total_expected += len(expected)
        total_detected += len(detected)
        total_matches += matches
        exposure_before += sum(entity.get("peso", _weight(entity.get("sensibilidad"))) for entity in expected)
        exposure_after += result["indice_exposicion_salida"]

        scenario_results.append(
            {
                "id": scenario["id"],
                "esperadas": len(expected),
                "detectadas": len(detected),
                "coincidencias": matches,
                "salida": result["salida"],
            }
        )

    precision = _safe_divide(total_matches, total_detected)
    recall = _safe_divide(total_matches, total_expected)
    f1 = _safe_divide(2 * precision * recall, precision + recall)

    return {
        "precision": precision,
        "exhaustividad": recall,
        "f1": f1,
        "indice_exposicion_antes": exposure_before,
        "indice_exposicion_despues": exposure_after,
        "reduccion_exposicion": exposure_before - exposure_after,
        "escenarios": scenario_results,
    }


def _count_exact_matches(expected: list[dict], detected: list[dict]) -> int:
    unmatched = {(entity["texto"].lower(), entity["tipo"]) for entity in detected}
    matches = 0
    for entity in expected:
        key = (entity["texto"].lower(), entity["tipo"])
        if key in unmatched:
            matches += 1
            unmatched.remove(key)
    return matches


def _weight(sensitivity: str | None) -> int:
    if sensitivity is None:
        return 0
    return SENSITIVITY_WEIGHTS.get(sensitivity.lower(), 0)


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
