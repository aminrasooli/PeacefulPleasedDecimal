
# AI Product Return Assistant

A Flask-based web application that analyzes customer return requests using AI, processes product images, and provides return policy information.

## Configuration

Set these environment variables (never commit secret values):

- `OPENPIPE_API_KEY` – OpenPipe API key
- `MODEL_ID` – model identifier used for analysis
- `HF_TOKEN` – Hugging Face Inference API token
- `HOST` – bind address (defaults to `127.0.0.1` for safe local use;
  hosted deployments set `0.0.0.0`)
- `PORT` – listen port (defaults to `81`)

## Run

```bash
python3 main.py
```
