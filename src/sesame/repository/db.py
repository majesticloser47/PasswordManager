import sqlite3
import subprocess
import sys

from ..config import Config


class DatabaseConnection:

    db_path = ""
    conn = None

    def __init__(self):
        self.db_path = Config.DB_PATH
        self.init_db()

    def init_db(self):
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS vault (
                id INTEGER PRIMARY KEY CHECK (id = 1),

                kdf_salt        BLOB    NOT NULL,
                kdf_memory      INTEGER NOT NULL,
                kdf_iterations  INTEGER NOT NULL,
                kdf_parallelism INTEGER NOT NULL,
                key_nonce     BLOB NOT NULL,
                encrypted_key BLOB NOT NULL,

                created_at INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER)),
                updated_at INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER))
            );

            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nonce BLOB NOT NULL,
                data BLOB NOT NULL,

                created_at INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER)),
                updated_at INTEGER NOT NULL DEFAULT (CAST(strftime('%s', 'now') AS INTEGER))
            );

            CREATE TRIGGER IF NOT EXISTS trg_vault_updated_at
            AFTER UPDATE ON vault FOR EACH ROW
            BEGIN
                UPDATE vault SET updated_at = CAST(strftime('%s', 'now') AS INTEGER)
                WHERE id = OLD.id;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_entries_updated_at
            AFTER UPDATE ON entries FOR EACH ROW
            BEGIN
                UPDATE entries SET updated_at = CAST(strftime('%s', 'now') AS INTEGER)
                WHERE id = OLD.id;
            END;
        """)
        self.conn.commit()

    def check_vault_exists(self) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM vault")
        count = cursor.fetchone()[0]
        return count > 0

    def vault_setup(
        self,
        kdf_salt: bytes,
        kdf_memory: int,
        kdf_iterations: int,
        kdf_parallelism: int,
        key_nonce: bytes,
        encrypted_key: bytes,
    ):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO vault (id, kdf_salt, kdf_memory, kdf_iterations, kdf_parallelism, key_nonce, encrypted_key)
            VALUES (1, ?, ?, ?, ?, ?, ?)
        """,
            (kdf_salt, kdf_memory, kdf_iterations, kdf_parallelism, key_nonce, encrypted_key),
        )
        self.conn.commit()
        return True

    def fetch_vault_info(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vault WHERE id = 1")
        row = cursor.fetchone()
        if row:
            return {
                "kdf_salt": row["kdf_salt"],
                "kdf_memory": row["kdf_memory"],
                "kdf_iterations": row["kdf_iterations"],
                "kdf_parallelism": row["kdf_parallelism"],
                "key_nonce": row["key_nonce"],
                "encrypted_key": row["encrypted_key"],
            }
        return None

    def add_password_entry(self, data, nonce) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO entries (nonce, data)
            VALUES (?, ?)
        """,
            (nonce, data),
        )
        self.conn.commit()
        return True

    def get_all_password_entries(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT nonce, data FROM entries")
        rows = cursor.fetchall()
        return [{"nonce": row["nonce"], "data": row["data"]} for row in rows]


def copy_to_clipboard(text):
    command = ""
    os_name = sys.platform
    if os_name.startswith("win"):
        command = "clip"
    elif os_name.startswith("linux"):
        command = "xclip -selection clipboard"
    elif os_name.startswith("darwin"):
        command = "pbcopy"
    try:
        subprocess.run(command, text="True", input=text)
    except Exception as e:
        print("Error copying to clipboard: ", e)
