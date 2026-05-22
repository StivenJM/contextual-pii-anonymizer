from __future__ import annotations

import json
from pathlib import Path

from contextual_pii_anonymizer.evaluation import evaluate_scenarios


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = evaluate_scenarios(root / "data" / "escenarios_iniciales.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))
