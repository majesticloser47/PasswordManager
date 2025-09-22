import sqlite3
import os
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()
db_path = os.getenv("DATABASE")
print("Database path: ", db_path)
def init_db():
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
        SELECT * FROM PASSWORDS''')
        rows = c.fetchall()
        res = [(row[0], row[1], row[3]) for row in rows]
        # conn.commit()
        conn.close()
        return res

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

def fetch_password_by_id(pwd_id):
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
        SELECT * FROM PASSWORDS WHERE id=?''', (pwd_id,))
        row = c.fetchone()
        conn.close()
        if row:
            copy_to_clipboard(str(row[2]))
            return True
    return False 