from .db import DatabaseConnection


def fetch_master_user(username):
    db = DatabaseConnection()
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM USERS WHERE user_name = ?", (username,))
    user = cursor.fetchone()
    db.conn.close()
    return user


def insert_master_user(username, pass_hash):
    db = DatabaseConnection()
    cursor = db.conn.cursor()
    cursor.execute("INSERT INTO USERS (user_name, password_hash) VALUES (?, ?)", (username, pass_hash))
    db.conn.commit()
    db.conn.close()
    return True
