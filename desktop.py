"""Setswana Speaker as a Mac app: the server lives only as long as the window.

Started by "Setswana Speaker.app" (see build_app.sh), which loads .env first.
"""
import threading
from pathlib import Path

import webview
from AppKit import NSApplication, NSBundle, NSImage

import app

ICON = Path(__file__).parent / "icon.png"


def brand_process():
    # ponytail: the process is Python.app underneath; rename it and swap the Dock icon instead of freezing with py2app.
    NSBundle.mainBundle().infoDictionary()["CFBundleName"] = "Setswana Speaker"
    NSApplication.sharedApplication().setApplicationIconImage_(NSImage.alloc().initWithContentsOfFile_(str(ICON)))


if __name__ == "__main__":
    pula, history = app.load_dependencies()
    server = app.make_server(0, pula, history)  # any free port, so a stray copy can never block startup
    threading.Thread(target=server.serve_forever, daemon=True).start()
    brand_process()
    window = webview.create_window("Setswana Speaker", f"http://127.0.0.1:{server.server_port}",
                                   width=900, height=820, min_size=(380, 600))
    window.events.closing += pula.close  # fires on both the close button and Quit
    webview.start()  # returns when the window closes; the daemon server thread dies with the process
