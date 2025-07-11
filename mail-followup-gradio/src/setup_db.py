import sqlite3

def initialize_database():
    conn = sqlite3.connect('followups.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        body TEXT NOT NULL,
        send_time TEXT NOT NULL,
        sent INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized.")

if __name__ == "__main__":
    initialize_database()