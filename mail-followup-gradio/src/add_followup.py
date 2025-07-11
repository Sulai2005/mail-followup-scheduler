def add_follow_up(recipient, subject, body, send_time):
    import sqlite3
    from datetime import datetime
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'followups.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure the table and 'sent' column exist (auto-create/upgrade if missing)
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
    try:
        cursor.execute("ALTER TABLE followups ADD COLUMN sent INTEGER DEFAULT 0")
    except Exception:
        pass

    # Ensure datetime is properly formatted
    if isinstance(send_time, datetime):
        send_time = send_time.strftime('%Y-%m-%d %H:%M')

    cursor.execute('''
        INSERT INTO followups (recipient, subject, body, send_time, sent)
        VALUES (?, ?, ?, ?, 0)
    ''', (recipient, subject, body, send_time))

    conn.commit()
    conn.close()
    print("📌 Follow-up saved to database.")