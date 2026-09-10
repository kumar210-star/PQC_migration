from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from ..config import DATABASE_PATH, DEFAULT_PROFILE
from ..models import Finding, MigrationTask


class Store:
    def __init__(self, path: Path = DATABASE_PATH) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, asset TEXT NOT NULL, file TEXT NOT NULL, line INTEGER NOT NULL,
                    evidence TEXT NOT NULL, algorithm TEXT NOT NULL, category TEXT NOT NULL, role TEXT NOT NULL,
                    parameter TEXT, risk TEXT NOT NULL, risk_reason TEXT NOT NULL, recommended_replacement TEXT NOT NULL,
                    recommendation_reason TEXT NOT NULL, migration_action TEXT NOT NULL, priority TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Not Started'
                );
                CREATE TABLE IF NOT EXISTS migration_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, inventory_id INTEGER NOT NULL UNIQUE, asset TEXT NOT NULL,
                    current_algorithm TEXT NOT NULL, cryptographic_role TEXT NOT NULL, target_algorithm TEXT NOT NULL,
                    reason TEXT NOT NULL, priority TEXT NOT NULL, dependencies TEXT NOT NULL, status TEXT NOT NULL,
                    FOREIGN KEY(inventory_id) REFERENCES inventory(id)
                );
                CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """)
            db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('profile',?)", (DEFAULT_PROFILE,))

    def replace_inventory(self, findings: list[Finding]) -> list[Finding]:
        with self.connect() as db:
            db.execute("DELETE FROM migration_tasks")
            db.execute("DELETE FROM inventory")
            for finding in findings:
                values = finding.model_dump(exclude={"id"})
                columns = ",".join(values)
                placeholders = ",".join("?" for _ in values)
                cursor = db.execute(f"INSERT INTO inventory ({columns}) VALUES ({placeholders})", tuple(values.values()))
                finding.id = cursor.lastrowid
        return findings

    def inventory(self) -> list[Finding]:
        with self.connect() as db:
            return [Finding(**dict(row)) for row in db.execute("SELECT * FROM inventory ORDER BY id")]

    def replace_tasks(self, tasks: list[MigrationTask]) -> list[MigrationTask]:
        with self.connect() as db:
            db.execute("DELETE FROM migration_tasks")
            for task in tasks:
                values = task.model_dump(exclude={"id"})
                values["dependencies"] = json.dumps(values["dependencies"])
                columns = ",".join(values)
                cursor = db.execute(f"INSERT INTO migration_tasks ({columns}) VALUES ({','.join('?' for _ in values)})", tuple(values.values()))
                task.id = cursor.lastrowid
        return tasks

    def tasks(self) -> list[MigrationTask]:
        with self.connect() as db:
            rows = db.execute("SELECT * FROM migration_tasks ORDER BY CASE priority WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 ELSE 2 END, id")
            return [MigrationTask(**{**dict(row), "dependencies": json.loads(row["dependencies"])}) for row in rows]

    def update_task(self, task_id: int, status: str) -> MigrationTask | None:
        with self.connect() as db:
            db.execute("UPDATE migration_tasks SET status=? WHERE id=?", (status, task_id))
            db.execute("UPDATE inventory SET status=? WHERE id=(SELECT inventory_id FROM migration_tasks WHERE id=?)", (status, task_id))
            row = db.execute("SELECT * FROM migration_tasks WHERE id=?", (task_id,)).fetchone()
            return MigrationTask(**{**dict(row), "dependencies": json.loads(row["dependencies"])}) if row else None

    def mark_by_role(self, role_fragment: str, status: str) -> None:
        with self.connect() as db:
            db.execute("UPDATE migration_tasks SET status=? WHERE lower(cryptographic_role) LIKE ?", (status, f"%{role_fragment.lower()}%"))
            db.execute("UPDATE inventory SET status=? WHERE id IN (SELECT inventory_id FROM migration_tasks WHERE lower(cryptographic_role) LIKE ?)", (status, f"%{role_fragment.lower()}%"))

    def profile(self) -> str:
        with self.connect() as db:
            row = db.execute("SELECT value FROM settings WHERE key='profile'").fetchone()
            return row[0] if row else DEFAULT_PROFILE

    def set_profile(self, profile: str) -> None:
        with self.connect() as db:
            db.execute("INSERT INTO settings(key,value) VALUES('profile',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (profile,))
            if profile == "PQC":
                db.execute("UPDATE migration_tasks SET status='Migrated' WHERE status IN ('Not Started','Planned','In Progress')")
                db.execute("UPDATE inventory SET status='Migrated' WHERE id IN (SELECT inventory_id FROM migration_tasks)")

