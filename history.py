"""Translation history and favourites, kept in a local SQLite file."""
import json
import sqlite3
from contextlib import closing, contextmanager
from datetime import datetime, timezone

SCHEMA = """CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY,
    english TEXT NOT NULL,
    setswana TEXT NOT NULL,
    words TEXT NOT NULL,          -- JSON list of {setswana, english}
    favourite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL      -- ISO 8601, UTC
)"""


class History:
    def __init__(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self._path = path
        with self._connect() as db:
            db.execute(SCHEMA)

    @contextmanager
    def _connect(self):
        # closing() closes the connection; "with db" commits on success and rolls back on error.
        with closing(sqlite3.connect(self._path)) as db, db:
            db.row_factory = sqlite3.Row
            yield db

    def add(self, english, setswana, words):
        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._connect() as db:
            cur = db.execute("INSERT INTO translations (english, setswana, words, created_at) VALUES (?, ?, ?, ?)",
                             (english, setswana, json.dumps(words), created_at))
            return self._get(db, cur.lastrowid)

    def recent(self, limit=200):
        with self._connect() as db:
            rows = db.execute("SELECT * FROM translations ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [_to_dict(r) for r in rows]

    def set_favourite(self, entry_id, favourite):
        """Returns the updated entry, or None if there is no entry with that id."""
        with self._connect() as db:
            db.execute("UPDATE translations SET favourite = ? WHERE id = ?", (int(favourite), entry_id))
            return self._get(db, entry_id)

    @staticmethod
    def _get(db, entry_id):
        row = db.execute("SELECT * FROM translations WHERE id = ?", (entry_id,)).fetchone()
        return _to_dict(row) if row else None


def _to_dict(row):
    return {**dict(row), "words": json.loads(row["words"]), "favourite": bool(row["favourite"])}
