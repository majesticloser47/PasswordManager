import os
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
        if os.path.exists(self.db_path):
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return self.conn

    def fetch_password_by_id(self, pwd_id):
        if os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute(
                """
            SELECT * FROM PASSWORDS WHERE id=?""",
                (pwd_id,),
            )
            row = c.fetchone()
            conn.close()
            if row:
                copy_to_clipboard(str(row[2]))
                return True
        return False


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
