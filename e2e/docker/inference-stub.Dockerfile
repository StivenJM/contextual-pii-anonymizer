FROM python:3.13-slim

WORKDIR /app

COPY support/stub_inference.py .

EXPOSE 3000

CMD ["python", "stub_inference.py"]
