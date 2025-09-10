import sqlite3
import os
from dotenv import load_dotenv

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