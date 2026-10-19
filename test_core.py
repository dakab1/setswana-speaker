"""Self-check for word alignment and history. Run: .venv/bin/python test_core.py"""
import tempfile
from pathlib import Path

from history import History
from pula import align_gloss

# Pula skipped "a" and "leboga" and merged the first line: those words get blanks, later words still line up.
words = align_gloss("Ke a leboga, tsala ya me.", "Ke = thank you\ntsala = friend\nya = of\nme = my")
assert words == [
    {"setswana": "Ke", "english": "thank you"},
    {"setswana": "a", "english": ""},
    {"setswana": "leboga", "english": ""},
    {"setswana": "tsala", "english": "friend"},
    {"setswana": "ya", "english": "of"},
    {"setswana": "me", "english": "my"},
], words

# Header lines and stray text are ignored; repeated words each take their own line, in order.
words = align_gloss("Ke tla go bona ka moso. Ke tla.",
                    "Word = English meaning\nKe = I\ntla = will\ngo = you\nbona = see\nka = on\nmoso = tomorrow\nKe = I\ntla = will")
assert [w["english"] for w in words] == ["I", "will", "you", "see", "on", "tomorrow", "I", "will"], words

# Numbered or bulleted lines still match.
words = align_gloss("Sala sentle", "1. Sala = Farewell\n- sentle = well")
assert [w["english"] for w in words] == ["Farewell", "well"], words

# A lone punctuation token is not a word.
assert align_gloss("Dumela !", "Dumela = hello") == [{"setswana": "Dumela", "english": "hello"}]

with tempfile.TemporaryDirectory() as tmp:
    history = History(Path(tmp) / "nested" / "history.db")
    first = history.add("Thank you.", "Ke a leboga.", [{"setswana": "Ke", "english": "I"}])
    second = history.add("Home", "Gae", [])
    assert first["favourite"] is False and first["words"][0]["english"] == "I"
    assert [e["id"] for e in history.recent()] == [second["id"], first["id"]]  # newest first
    assert history.set_favourite(first["id"], True)["favourite"] is True
    assert History(Path(tmp) / "nested" / "history.db").recent()[1]["favourite"] is True  # survives reopening
    assert history.set_favourite(999, True) is None

print("all checks passed")
