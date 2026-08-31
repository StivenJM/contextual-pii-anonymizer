# ML Inference Service

BentoML service that executes the current OpenMed token-classification model and returns its native detections.

The service performs only ML inference and technical output adaptation. It does not run regex recognizers, map labels to the canonical taxonomy, fuse detections, apply protection rules, or de-identify text.

## Structure

```text
app/
  service.py              # BentoML service entrypoint
  controllers/
    dtos/                 # BentoML API request/response DTOs
  models/                 # OpenMed loading and native output adaptation
  use_cases/              # ML inference orchestration
tests/                    # Isolated tests with controlled model output
```

## Install

```powershell
.\.venv\Scripts\activate.ps1
python -m pip install -e .
```

The first server startup downloads the Hugging Face model if it is not already cached.

## Run

```powershell
$env:PYTHONUTF8='1'
$env:PYTHONPATH='app'
.\.venv\Scripts\python.exe -m bentoml serve service:PiiInferenceService --reload
```

## Test

```powershell
$env:PYTHONPATH='app'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The isolated tests do not load or download the real model.

## Detect

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:3000/detect `
  -ContentType 'application/json' `
  -Body '{"text":"Juan Perez tiene el correo juan@example.com"}'
```

The response contains the current model identifier and detections with the model's native labels:

```json
{
  "model_id": "OpenMed/OpenMed-PII-Spanish-QwenMed-XLarge-600M-v1",
  "detections": [
    {
      "native_type": "PER",
      "text": "Juan Perez",
      "start": 0,
      "end": 10,
      "confidence": 0.95
    }
  ]
}
```

An email, phone number, or identifier is absent when the ML model does not detect it. Rule-based detection belongs to the privacy middleware and is intentionally outside this service.
