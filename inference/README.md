# ML Inference Service

BentoML service that discovers and executes explicitly registered PII detection models through a common contract. OpenMed is the current production implementation.

The service performs only ML inference and technical output adaptation. It does not run regex recognizers, map labels to the canonical taxonomy, fuse detections, apply protection rules, or de-identify text.

## Structure

```text
app/
  service.py              # BentoML adapter and composition root
  entities/               # Framework-independent detections and model metadata
  model_catalog.py        # Registry of loaded model instances
  schemas/                # BentoML request and response contracts
  services/               # Model contract and OpenMed implementation
  use_cases/              # Framework-independent inference orchestration
tests/                    # Tests split by architectural boundary
```

## Install

```powershell
.\.venv\Scripts\activate.ps1
python -m pip install -e .
```

Each BentoML worker loads its registered models during service initialization and reuses those instances across requests. The first startup downloads the OpenMed artifact from Hugging Face if it is not already cached.

## Run

```powershell
$env:PYTHONUTF8='1'
.\.venv\Scripts\python.exe -m bentoml serve app.service:PiiInferenceService --reload
```

## Test

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The isolated tests do not load or download the real model.

## Discover Models

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:3000/models `
  -ContentType 'application/json' `
  -Body '{}'
```

Discovery exposes stable service metadata and native labels. It does not expose the upstream artifact reference:

```json
{
  "models": [
    {
      "id": "openmed-pii-spanish-600m",
      "name": "OpenMed PII Spanish 600M",
      "version": "v1",
      "description": "Spanish PII token-classification model.",
      "native_entity_types": ["ACCOUNTNAME", "AGE", "EMAIL", "ORGANIZATION"]
    }
  ]
}
```

The native entity list above is abbreviated for readability. The API returns the complete list declared by the model.

## Detect

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:3000/detect `
  -ContentType 'application/json' `
  -Body '{"model_id":"openmed-pii-spanish-600m","text":"Juan Perez tiene el correo juan@example.com"}'
```

The response contains the current model identifier and detections with the model's native labels:

```json
{
  "model_id": "openmed-pii-spanish-600m",
  "model_version": "v1",
  "detections": [
    {
      "native_type": "FIRSTNAME",
      "text": "Juan",
      "start": 0,
      "end": 4,
      "confidence": 0.95
    }
  ]
}
```

`model_id` is the logical service identity, not a Hugging Face repository name. An unknown ID returns a deterministic `404 Not Found`; the service never selects a fallback model.

An email, phone number, or identifier is absent when the ML model does not detect it. Rule-based detection belongs to the privacy middleware and is intentionally outside this service.
