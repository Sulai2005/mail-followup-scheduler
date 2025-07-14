from fastapi import FastAPI, Request
from pydantic import BaseModel
from llm_utils import generate_followup_email
import httpx
import os

app = FastAPI()

class MailGenRequest(BaseModel):
    contact_id: str
    companyDetails: str = ""
    custom_prompt: str = ""

async def fetch_conversation_from_gohighlevel(contact_id: str) -> dict:
    api_url = f"https://rest.gohighlevel.com/v1/conversations/?contactId={contact_id}"
    headers = {"Authorization": f"Bearer {os.environ['GHL_API_KEY']}","Accept": "application/json","Version": "2021-04-15"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(api_url, headers=headers)
        resp.raise_for_status()
        return resp.json()

@app.post("/mail-generator")
async def mail_generator(req: MailGenRequest):
    try:
        ghl_data = await fetch_conversation_from_gohighlevel(req.contact_id)
        conversation = ghl_data.get("conversations", [])
        if not conversation:
            return {"error": "No conversation found for this contact_id."}
        # Optionally, fetch contact name here for personalization
        company_details = req.companyDetails
        custom_prompt = req.custom_prompt
        subject, body = generate_followup_email(
            recipient_name="Client",  # Replace with actual name if fetched
            meeting_context=conversation,
            custom_prompt=custom_prompt,
            company_data=company_details
        )
        return {"subject": subject, "body": body}
    except Exception as e:
        return {"error": str(e)}
