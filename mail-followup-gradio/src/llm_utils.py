import os
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Load environment variables
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Azure Chat Model
chat = AzureChatOpenAI(
    api_key=api_key,
    api_version=api_version,
    azure_endpoint=api_base,
    deployment_name=deployment_name,
    temperature=0.7,
)

# 1. Summarize PDF context
def summarize_context(raw_text):
    prompt = ChatPromptTemplate.from_template("""
    You are a sales assistant. Summarize the following email thread into key points for follow-up.

    Email Thread:
    {document_text}
    """)
    chain = prompt | chat
    result = chain.invoke({"document_text": raw_text})
    return result.content.strip()

# 2. Generate follow-up email
def generate_followup_email(recipient_name, meeting_context, custom_prompt=None, company_data=None):
    spam_avoidance_instructions = """
    Please ensure:
    - Avoid using spam trigger words (like "free", "urgent", "guarantee", "winner", "click here", "act now", etc.).
    - Use a neutral, business-like tone.
    - Do not use excessive exclamation marks or all-caps.
    - Do not include suspicious links or attachments.
    - Make the email sound genuine and helpful.
    - Include a real name and company signature at the end.
    - Keep the email as short and concise as possible, ideally 2-4 sentences.
    """
    # Integrate company data and custom prompt into the main prompt
    company_context = f"Company Info: {company_data}\n" if company_data else ""
    custom_prompt_section = f"Custom Instructions: {custom_prompt}\n" if custom_prompt else ""
    prompt_template = f"""
    You are a sales assistant named Sulaiman. Based on the context below, write a very short, polite, and professional follow-up email that is optimized for clarity and action.
    {spam_avoidance_instructions}
    {company_context}{custom_prompt_section}
    Client: {{recipient_name}}
    Context: {{meeting_context}}

    Respond with:
    Subject: <short, relevant subject line>
    Body:
    <brief, actionable email body>
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    chain = prompt | chat
    response = chain.invoke({
        "recipient_name": recipient_name,
        "meeting_context": meeting_context
    })

    content = response.content.strip()

    # Parse subject and body
    subject = ""
    body = ""
    lines = content.split('\n')
    for line in lines:
        if line.lower().startswith("subject:"):
            subject = line.split(":", 1)[1].strip()
        elif line.lower().startswith("body:"):
            continue
        else:
            body += line.strip() + "\n"

    return subject, body.strip()