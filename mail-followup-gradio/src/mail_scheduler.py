import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import time
import os
from dotenv import load_dotenv
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def ensure_db_schema():
    db_path = os.path.join(os.path.dirname(__file__), 'followups.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Ensure the table and 'sent' column exist
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
    conn.commit()
    conn.close()

def send_email(to, subject, body):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    print(f"📨 Sent: {subject} → {to}")

def check_and_send_emails():
    db_path = os.path.join(os.path.dirname(__file__), 'followups.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cursor.execute('''
        SELECT id, recipient, subject, body FROM followups
        WHERE send_time <= ? AND sent = 0
    ''', (now,))

    for row in cursor.fetchall():
        id, recipient, subject, body = row
        try:
            send_email(recipient, subject, body)
            cursor.execute('UPDATE followups SET sent = 1 WHERE id = ?', (id,))
        except Exception as e:
            print(f"❌ Failed to send to {recipient}: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    ensure_db_schema()
    print("📬 Scheduler started. Checking every minute...")
    while True:
        check_and_send_emails()
        time.sleep(60)