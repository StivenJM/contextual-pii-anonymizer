# Contextual PII Inference Service

BentoML service that exposes the model inference API for the contextual PII anonymizer.

## Structure

```text
src/
  service.py              # BentoML service entrypoint
  controllers/
    dtos/                 # BentoML API request/response DTOs
  use_cases/              # Inference use cases grouped by domain
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
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m bentoml serve service:PiiInferenceService --reload
```

## Analyze

```powershell
Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:3000/analyze `
  -ContentType 'application/json' `
  -Body '{"text":"Juan Perez tiene el correo juan@example.com"}'
```
