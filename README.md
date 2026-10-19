# Setswana Speaker

A personal Mac app for hearing Setswana spoken and translating English into Setswana.

- **Speak:** type Setswana and hear it read aloud, with each word highlighted as it is said.
- **Translate:** English goes in, Setswana comes out, with a word-by-word breakdown. Tap a word to hear it alone.
- **History and favourites:** every translation is saved; star the ones you want to keep handy.

Translation runs on this Mac with [Pula](https://arxiv.org/abs/2408.02239), an open Setswana language model, so it works offline. The voice is Microsoft's isiZulu neural voice (Themba or Thando) through Edge TTS, which needs an internet connection: no offline neural voice exists for Setswana. Translations and word meanings can be wrong, and the voice's tones are approximate, so check anything important with a Setswana speaker.

## Setup

Needs an Apple Silicon Mac and Python 3.12.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
mkdir -p models
curl -L -o models/pula-8b-q4_k_m.gguf https://huggingface.co/mradermacher/Pula-8B-GGUF/resolve/main/Pula-8B.Q4_K_M.gguf
```

The model is 4.9 GB. Pula's model card does not state a licence, so treat it as personal use only.

## Run

- **Mac app:** `./build_app.sh` builds `~/Applications/Setswana Speaker.app`. The app runs the code from this folder, so code changes need no rebuild; rebuild only if the folder moves. Logs go to `~/Library/Logs/SetswanaSpeaker.log`.
- **Browser:** `./run.sh`, then open http://127.0.0.1:8790.

## Check

```bash
.venv/bin/python test_core.py
```

## HTTP API

The page talks to a local server bound to 127.0.0.1. All bodies are JSON; errors are plain text with a 4xx/5xx status.

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/` | | The page |
| POST | `/speak` | `{"text", "voice": "themba"\|"thando", "rate": -50..20}` | `{"audio": base64 MP3, "words": [{"start", "end"}]}` (seconds) |
| POST | `/translate` | `{"text"}` (English, 1-500 chars) | The saved history entry (below) |
| GET | `/history` | | `{"items": [entry, ...]}`, newest first, up to 200 |
| POST | `/favourite` | `{"id": int, "favourite": bool}` | The updated entry, or 404 |

A history entry is `{"id", "english", "setswana", "words": [{"setswana", "english"}], "favourite", "created_at"}` with `created_at` in UTC.

## Files

| File | What it is |
|---|---|
| `app.py` | HTTP server and request validation |
| `pula.py` | Pula model: translation and word-by-word meanings |
| `history.py` | SQLite history and favourites |
| `index.html` | The whole interface |
| `desktop.py` | Mac app window (pywebview); owns the server's lifetime |
| `build_app.sh` | Builds the `.app` bundle and its icon |
| `generate.py` | The original one-off script that made the first pronunciation clips |
