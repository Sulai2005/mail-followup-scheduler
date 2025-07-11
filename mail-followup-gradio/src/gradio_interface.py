import gradio as gr
from pdf_utils import extract_text_from_pdf
from llm_utils import summarize_context, generate_followup_email
from add_followup import add_follow_up
from datetime import datetime

def process_pdf_and_schedule(pdf_file, recipient_name, recipient_email, followup_datetime, custom_prompt):
    # Extract text from the uploaded PDF
    raw_text = extract_text_from_pdf(pdf_file.name)

    # Summarize the conversation using the provided custom prompt
    context_summary = summarize_context(raw_text)

    # Generate follow-up email using the recipient's name and the summarized context
    subject, body = generate_followup_email(recipient_name, context_summary)

    # Customize the body as a Sales Assistant
    full_body = (
        f"{body.strip()}\n\n"
        "Best regards,\n"
        "Sulaiman\n"
        "Sales Assistant, YourCompany"
    )

    # Format the follow-up datetime
    dt_str = followup_datetime.strftime('%Y-%m-%d %H:%M')

    # Schedule the email
    add_follow_up(
        recipient=recipient_email,
        subject=subject,
        body=full_body,
        send_time=dt_str
    )

    return f"✅ Follow-up scheduled for {recipient_email} at {dt_str}"

def main():
    with gr.Blocks() as demo:
        gr.Markdown("## Email Follow-Up Scheduler")
        
        with gr.Row():
            pdf_input = gr.File(label="Upload PDF", type="file")
            recipient_name_input = gr.Textbox(label="Recipient Name")
            recipient_email_input = gr.Textbox(label="Recipient Email")
            followup_datetime_input = gr.DateTime(label="Follow-Up Date and Time")
            custom_prompt_input = gr.Textbox(label="Custom Prompt", placeholder="Enter any custom prompt here...")

        submit_button = gr.Button("Schedule Follow-Up")
        output_text = gr.Textbox(label="Output")

        submit_button.click(
            process_pdf_and_schedule,
            inputs=[pdf_input, recipient_name_input, recipient_email_input, followup_datetime_input, custom_prompt_input],
            outputs=output_text
        )

    demo.launch()

if __name__ == "__main__":
    main()