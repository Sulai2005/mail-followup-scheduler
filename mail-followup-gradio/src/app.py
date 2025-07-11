import gradio as gr
from pdf_utils import extract_text_from_pdf
from llm_utils import summarize_context, generate_followup_email
from datetime import datetime
import sqlite3
import os

def add_follow_up(recipient, subject, body, send_time):
    # Use the database in the same directory as this script
    db_path = os.path.join(os.path.dirname(__file__), 'followups.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Ensure the table exists (auto-create if missing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            send_time TEXT NOT NULL
        )
    ''')

    # Ensure datetime is properly formatted
    if isinstance(send_time, datetime):
        send_time = send_time.strftime('%Y-%m-%d %H:%M')

    cursor.execute('''
        INSERT INTO followups (recipient, subject, body, send_time)
        VALUES (?, ?, ?, ?)
    ''', (recipient, subject, body, send_time))

    conn.commit()
    conn.close()
    print("📌 Follow-up saved to database.")

def get_all_followups():
    db_path = os.path.join(os.path.dirname(__file__), 'followups.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''SELECT id, recipient, subject, send_time FROM followups ORDER BY send_time DESC''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def process_pdf_and_schedule(pdf_file, recipient_name, recipient_email, followup_datetime, custom_prompt, company_name, company_website, linkedin_url):
    if pdf_file is None:
        return "❌ Please upload a PDF file."
    # Extract text from the uploaded PDF file
    raw_text = extract_text_from_pdf(pdf_file.name)

    # Summarize the conversation using the provided custom prompt
    context_summary = summarize_context(raw_text)

    # Prepare company data string
    company_data = f"Name: {company_name}\nWebsite: {company_website}\nLinkedIn: {linkedin_url}"

    # Generate the follow-up email using the recipient's name, summarized context, and company data
    subject, body = generate_followup_email(recipient_name, context_summary, custom_prompt, company_data)

    # Customize the body as a Sales Assistant
    full_body = (
        f"{body.strip()}\n\n"
        "Best regards,\n"
        "Sulaiman\n"
        "Sales Assistant, YourCompany"
    )

    # Format the follow-up datetime
    # Gradio DateTime may return float (timestamp), str, or datetime
    if isinstance(followup_datetime, float):
        followup_datetime = datetime.fromtimestamp(followup_datetime)
    elif isinstance(followup_datetime, str):
        # Try parsing ISO format string
        try:
            followup_datetime = datetime.fromisoformat(followup_datetime)
        except Exception:
            return "❌ Invalid date/time format. Please select a valid date and time."
    elif not isinstance(followup_datetime, datetime):
        return "❌ Invalid date/time input. Please select a valid date and time."
    dt_str = followup_datetime.strftime('%Y-%m-%d %H:%M')

    # Schedule the email
    add_follow_up(
        recipient=recipient_email,
        subject=subject,
        body=full_body,
        send_time=dt_str
    )

    # Fetch all follow-ups after scheduling
    followups = get_all_followups()
    followup_list = "\n".join([
        f"ID: {row[0]} | To: {row[1]} | Subject: {row[2]} | Time: {row[3]}" for row in followups
    ])
    return f"✅ Follow-up scheduled for {recipient_email} at {dt_str}\n\nAll Scheduled Follow-Ups:\n{followup_list}"

# Gradio interface setup
with gr.Blocks() as app:
    gr.Markdown("## Email Follow-Up Scheduler")
    
    with gr.Row():
        pdf_input = gr.File(label="Upload PDF", type="filepath")
        recipient_name_input = gr.Textbox(label="Recipient Name")
        recipient_email_input = gr.Textbox(label="Recipient Email")
        followup_datetime_input = gr.DateTime(label="Follow-Up Date and Time")
        custom_prompt_input = gr.Textbox(label="Custom Prompt", placeholder="Enter any custom prompt for summarization...")
    with gr.Row():
        company_name_input = gr.Textbox(label="Company Name", placeholder="Enter company name...")
        company_website_input = gr.Textbox(label="Company Website", placeholder="Enter company website...")
        linkedin_url_input = gr.Textbox(label="LinkedIn URL", placeholder="Enter LinkedIn profile URL...")

    submit_button = gr.Button("Schedule Follow-Up")
    output = gr.Textbox(label="Output", lines=10)

    submit_button.click(
        process_pdf_and_schedule,
        inputs=[pdf_input, recipient_name_input, recipient_email_input, followup_datetime_input, custom_prompt_input, company_name_input, company_website_input, linkedin_url_input],
        outputs=output
    )

app.launch()