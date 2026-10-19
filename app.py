"""Setswana Speaker: hear Setswana text spoken, translate English into Setswana with Pula, keep a history.

Run in a browser:  ./run.sh   (reads .env, then serves on http://127.0.0.1:$PORT)
Run as a Mac app:  see desktop.py
"""
import asyncio
import base64
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import edge_tts

from history import History
from pula import Pula

HERE = Path(__file__).parent
MAX_CHARS = 500
# ponytail: no Setswana neural voice exists; isiZulu reads Setswana spelling closely enough.
VOICES = {"thando": "zu-ZA-ThandoNeural", "themba": "zu-ZA-ThembaNeural"}
PAGE = (HERE / "index.html").read_text(encoding="utf-8")


class BadRequest(Exception):
    pass


async def synthesize(text, voice, rate):
    audio, words = bytearray(), []
    async for chunk in edge_tts.Communicate(text, voice, rate=f"{rate:+d}%", boundary="WordBoundary").stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":  # offsets are in 100 ns ticks
            words.append({"start": chunk["offset"] / 1e7, "end": (chunk["offset"] + chunk["duration"]) / 1e7})
    return {"audio": base64.b64encode(audio).decode(), "words": words}


def text_field(req):
    text = str(req.get("text", "")).strip()
    if not text or len(text) > MAX_CHARS:
        raise BadRequest(f"Text must be 1 to {MAX_CHARS} characters")
    return text


def make_handler(pula, history):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="text/plain; charset=utf-8"):
            body = body if isinstance(body, bytes) else body.encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data):
            self._send(200, json.dumps(data), "application/json")

        def do_GET(self):
            if self.path == "/":
                return self._send(200, PAGE, "text/html; charset=utf-8")
            if self.path == "/history":
                return self._json({"items": history.recent()})
            self._send(404, "Not found")

        def do_POST(self):
            routes = {"/speak": self._speak, "/translate": self._translate, "/favourite": self._favourite}
            if self.path not in routes:
                return self._send(404, "Not found")
            try:
                req = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 4096)))
                if not isinstance(req, dict):
                    raise BadRequest("Request must be a JSON object")
                routes[self.path](req)
            except (ValueError, BadRequest) as e:  # json.JSONDecodeError is a ValueError
                self._send(400, str(e) if isinstance(e, BadRequest) else "Request must be valid JSON")

        def _speak(self, req):
            text = text_field(req)
            if req.get("voice") not in VOICES or not isinstance(req.get("rate"), int) or not -50 <= req["rate"] <= 20:
                raise BadRequest("Voice must be themba or thando, and speed between -50% and +20%")
            try:
                result = asyncio.run(synthesize(text, VOICES[req["voice"]], req["rate"]))
            except Exception as e:
                self.log_error("TTS failed: %r", e)
                return self._send(502, "The voice needs an internet connection. Check you're online, then try again.")
            self._json(result)

        def _translate(self, req):
            english = text_field(req)
            try:
                setswana = pula.translate(english)
                words = pula.gloss(english, setswana)
            except Exception as e:
                self.log_error("Translation failed: %r", e)
                return self._send(502, "Translation failed. Try again, or restart the app if it keeps happening.")
            self._json(history.add(english, setswana, words))

        def _favourite(self, req):
            if not isinstance(req.get("id"), int) or not isinstance(req.get("favourite"), bool):
                raise BadRequest("Send an integer id and a true/false favourite")
            entry = history.set_favourite(req["id"], req["favourite"])
            if entry is None:
                return self._send(404, "That translation is no longer in your history")
            self._json(entry)

    return Handler


def make_server(port, pula, history):
    """Port 0 lets the OS pick a free port; read it back from server.server_port."""
    return ThreadingHTTPServer(("127.0.0.1", port), make_handler(pula, history))


def load_dependencies():
    """Build Pula and History from .env settings, failing loudly if a setting or the model file is missing."""
    model_path = HERE / os.environ["PULA_MODEL_PATH"]
    if not model_path.is_file():
        raise SystemExit(f"Pula model not found at {model_path}")
    return Pula(model_path), History(HERE / os.environ["HISTORY_DB_PATH"])


if __name__ == "__main__":
    pula, history = load_dependencies()
    server = make_server(int(os.environ["PORT"]), pula, history)
    print(f"Setswana Speaker on http://127.0.0.1:{server.server_port}")
    try:
        server.serve_forever()
    finally:
        pula.close()
