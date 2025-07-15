"""
To run as Streamlit app (with API endpoint):
    streamlit run app.py

- UI: http://localhost:8501
- API: http://localhost:8001/generate-followup

The API endpoint accepts POST requests with:
  - file: (file upload)
  - prompt: (string, optional)
  - recipient: (string, optional)

Example curl:
curl -X POST "http://localhost:8001/generate-followup" \
  -F "file=@yourfile.csv" \
  -F "recipient=recipient@example.com"
"""

import threading
import time
import os
import shutil
import re
import tempfile

import streamlit as st
from modules.file_parser import parse_file
from modules.email_analyzer import get_senders_summary, extract_context_for_sender
from modules.followup_generator import generate_followup
from utils.prompt_template import fill_prompt_template
from utils.webhook import send_to_webhook

# --- FastAPI server in background thread ---
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

api = FastAPI(title="FollowUp Generator API")
api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@api.post("/generate-followup")
async def generate_followup_api(
    file: UploadFile = File(...),
    prompt: str = Form(None),
    recipient: str = Form(None)
):
    default_prompt = "Hi {name},\n\nJust following up on {topic}."
    use_prompt = prompt if prompt else default_prompt
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        parsed_data = parse_file(tmp_path)
        recipients = list(parsed_data.keys())
        selected_recipient = recipient or (recipients[0] if recipients else None)
        if not selected_recipient:
            return JSONResponse({"error": "No recipient found in file."}, status_code=400)
        context = extract_context_for_sender(parsed_data, selected_recipient)
        filled_prompt = fill_prompt_template(use_prompt, context)
        followup = generate_followup(filled_prompt, context)
        return {"followup": followup, "recipient": selected_recipient, "context": context}
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

# Only start FastAPI server once
if 'fastapi_thread_started' not in st.session_state:
    def run_fastapi():
        uvicorn.run(api, host="0.0.0.0", port=8001, log_level="warning")
    t = threading.Thread(target=run_fastapi, daemon=True)
    t.start()
    st.session_state['fastapi_thread_started'] = True
    time.sleep(1)  # Give FastAPI a moment to start

# --- Streamlit App (UI) ---
TEMP_DIR = "temp"
st.set_page_config(page_title="Follow-Up Generator", layout="wide", page_icon="📧")

# Sidebar
with st.sidebar:
    st.title("📧 Follow-Up Generator")
    st.markdown("""
    **Automate your follow-up emails!**
    - Upload CSV, JSON, PDF, or TXT
    - Enter a custom prompt (optional)
    - Select recipient (if multiple)
    - Generate, download, or send follow-up
    """)
    st.markdown("---")
    st.subheader("API Usage")
    st.code("""POST /generate-followup
file: (file upload)
prompt: (string, optional)
recipient: (string, optional)
""", language="markdown")
    st.markdown("[API Docs](http://localhost:8001/docs)")
    st.markdown("---")
    st.caption("Made with team")

os.makedirs(TEMP_DIR, exist_ok=True)

def extract_prompt_vars(prompt):
    return re.findall(r"{(.*?)}", prompt)

if 'parsed_data' not in st.session_state:
    st.session_state['parsed_data'] = None
if 'senders' not in st.session_state:
    st.session_state['senders'] = None
if 'selected_sender' not in st.session_state:
    st.session_state['selected_sender'] = None

st.markdown("""
# ✨ Generate Custom Follow-Ups
""")

col1, col2 = st.columns([1, 2])
with col1:
    uploaded_file = st.file_uploader("📤 Upload a file", type=["csv", "json", "pdf", "txt"])
with col2:
    default_prompt = "Hi {name},\n\nJust following up on {topic}."
    custom_prompt = st.text_area("📝 Custom Prompt (optional)", "", height=120, help="Use {name}, {topic}, etc. as variables.")
    webhook_url = st.text_input("🔗 Webhook URL (optional)")

submitted = st.button("Parse File", use_container_width=True)

if submitted:
    if not uploaded_file:
        st.warning("Please upload a file to proceed.")
    else:
        with st.spinner("Processing file..."):
            temp_path = os.path.join(TEMP_DIR, uploaded_file.name)
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            parsed_data = parse_file(temp_path)
            st.session_state['parsed_data'] = parsed_data
            if parsed_data:
                senders = list(parsed_data.keys())
                st.session_state['senders'] = senders
                if len(senders) == 1:
                    st.session_state['selected_sender'] = senders[0]
                else:
                    st.session_state['selected_sender'] = None
            else:
                st.session_state['senders'] = None
                st.session_state['selected_sender'] = None
            if os.path.exists(temp_path):
                os.remove(temp_path)

if st.session_state['parsed_data']:
    senders = st.session_state['senders']
    st.markdown("---")
    st.subheader("👤 Recipient Selection")
    if len(senders) > 1:
        recipient = st.selectbox("Select Recipient", senders, key="sender_select")
        st.session_state['selected_sender'] = recipient
    else:
        recipient = senders[0]
        st.session_state['selected_sender'] = recipient
    st.success(f"Selected recipient: {st.session_state['selected_sender']}")

    prompt_vars = extract_prompt_vars(custom_prompt if custom_prompt else default_prompt)
    st.info(f"Detected prompt variables: {', '.join(prompt_vars) if prompt_vars else 'None'}")

    context = extract_context_for_sender(st.session_state['parsed_data'], st.session_state['selected_sender'])
    filled_prompt = fill_prompt_template(custom_prompt if custom_prompt else default_prompt, context)

    if st.button("🚀 Generate Follow-Up", use_container_width=True):
        with st.spinner("Generating follow-up..."):
            followup = generate_followup(filled_prompt, context)
            st.success("Follow-up generated!")
            st.markdown("---")
            st.subheader("📨 Generated Follow-Up")
            st.text_area("Follow-Up Email", followup, height=200)
            st.download_button("⬇️ Download Follow-Up", followup, file_name="followup.txt")
            if webhook_url:
                with st.spinner("Sending to webhook..."):
                    response = send_to_webhook(webhook_url, followup)
                    if response:
                        st.success("Sent to webhook!")
                    else:
                        st.warning("Failed to send to webhook.")

if os.path.exists(TEMP_DIR) and not os.listdir(TEMP_DIR):
    shutil.rmtree(TEMP_DIR) 