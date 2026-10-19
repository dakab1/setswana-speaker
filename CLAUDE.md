# CLAUDE.md

Setswana Speaker: a personal Mac app (Python, stdlib HTTP server + pywebview window) that speaks Setswana and translates English into Setswana. See README.md for setup, the API and the file map.

## How it fits together

- `desktop.py` starts the server from `app.py` on a free port, opens a pywebview window on it, and frees Pula when the window closes. `run.sh` is the same server for a browser on `$PORT`.
- `app.py` is the HTTP layer only. `pula.py` (model) and `history.py` (SQLite) are built in `load_dependencies()` and injected into the handler.
- All config comes from `.env` (see `.env.example`); a missing setting or model file must stop startup, never fall back.

## Things that bit us (don't undo these)

- **Pula prompt format:** build the raw Llama 3 prompt with `\n\n` after each header (llama.cpp adds BOS). The GGUF's own chat template injects a dated system message that makes Pula answer questions instead of translating. This format reproduces Ollama's output exactly.
- **repeat_penalty:** 1.1 for translation (1.0 loops: "kae kae kae..."), 1.0 for glossing (the gloss legitimately repeats words).
- **Gloss parsing:** Pula numbers or bullets its lines and sometimes skips words. `align_gloss` matches lines to the sentence's own words in order; keep `test_core.py` passing.
- **Metal crash on quit:** llama.cpp aborts if the model is still loaded at process exit. `Pula.close()` runs on the window's `closing` event.
- **Rosetta:** the app launcher must use `arch -arm64`, or macOS starts python.org's universal Python as Intel and llama.cpp fails to load.
- **App identity:** the process is Python.app underneath (no py2app). `desktop.py` renames it and sets the Dock icon. AppleEvents sent to the bundle id don't reach it; quit via the Dock or Cmd-Q.
- **Voice:** no offline Setswana or isiZulu neural voice exists (Meta MMS has none; Apple has none). Edge TTS isiZulu (Themba default) needs internet; translation does not.

## Working here

- Check: `.venv/bin/python test_core.py`. Then test the real flow in the browser (`./run.sh`) and in the app; the UI must work at phone width and in light and dark mode.
- After changing `app.py`/`pula.py`/`history.py`/`index.html`, restart the app (the page is read at startup). Rebuild with `./build_app.sh` only if the bundle itself changes.
- Pin exact versions in `requirements.txt` (`pip freeze`); zero warnings when run with `-W default`.
- Git flow: `main`, `develop`, and `feature/<desc>` branches off `develop`. Never commit to `main`/`develop` directly, and never commit or push without being asked.
