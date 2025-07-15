import os
import re
import logging
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Set up logger
logger = logging.getLogger("followup_generator")
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def extract_important_sentences(body, max_len=10000, min_len=1000):
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', body)
    # Find important sentences: questions, requests, action items
    important = []
    for s in sentences:
        s_strip = s.strip()
        if (
            '?' in s_strip or
            re.search(r'\b(please|need|require|action|update|request|urgent|asap|remind|follow up)\b', s_strip, re.IGNORECASE)
        ):
            important.append(s_strip)
    # Always include first and last sentence for context
    if sentences:
        if sentences[0].strip() not in important:
            important.insert(0, sentences[0].strip())
        if sentences[-1].strip() not in important:
            important.append(sentences[-1].strip())
    # Remove duplicates, preserve order
    seen = set()
    curated = []
    for s in important:
        if s and s not in seen:
            curated.append(s)
            seen.add(s)
    # Build context string up to max_len
    context_str = ''
    for s in curated:
        if len(context_str) + len(s) + 1 > max_len:
            break
        context_str += s + ' '
    context_str = context_str.strip()
    # If too short, append the last part of the body for more context
    if len(context_str) < min_len and len(body) > 0:
        tail = body[-(max_len - len(context_str)):] if len(body) > (max_len - len(context_str)) else body
        context_str = (context_str + '\n' + tail).strip() if context_str else tail
    return context_str[:max_len]

def generate_followup(filled_prompt, context):
    azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
    azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
    if azure_api_key and azure_endpoint and azure_deployment:
        try:
            spam_avoidance_instructions = """
Please ensure:
- Avoid using spam trigger words (like "free", "urgent", "guarantee", "winner", "click here", "act now", etc.).
- Use a neutral, business-like tone.
- Do not use excessive exclamation marks or all-caps.
- Do not include suspicious links or attachments.
- Make the email sound genuine and helpful.
- Keep the email concise, ideally no more than 4 sentences, and do not include a full signature block unless specifically requested.
"""
            system_prompt = (
                "You are an expert business email assistant. "
                "Write professional, context-aware follow-up emails. "
                "Reference specific details from the previous conversation, summarize key points, and clearly state the purpose of the follow-up. "
                "If there are any pending questions, requests, or next steps, mention them. "
                "Do NOT use jokes, emojis, or casual language. "
                "Be clear, concise, and polite. And make sure that the follow-up does not feel vague or generic.\n" + spam_avoidance_instructions
            )
            prev_subject = context.get('topic', '')
            prev_body = context.get('body', '')
            recipient = context.get('name', 'there')
            max_context_len = 2500
            curated_body = extract_important_sentences(prev_body, max_context_len, min_len=1000)
            truncated_note = ""
            if len(prev_body) > max_context_len:
                truncated_note = "[Note: Only the most important parts of the previous message are included due to length limits.]\n"
            if not curated_body or len(curated_body.split()) < 10:
                curated_body += "\nI wanted to check in regarding our previous discussion. Please let me know if you have any updates or need further information."
            user_prompt = (
                f"Previous subject: {prev_subject}\n"
                f"{truncated_note}Previous message: {curated_body}\n\n"
                f"Write a professional follow-up email to {recipient} based on the above conversation. "
                f"Your reply must be concise and no more than 4 sentences. "
                f"Your reply must be at least one sentence and should reference the previous conversation or request a response or next step. "
                f"Reference specific details, summarize key points, and clearly state the purpose of the follow-up. "
                f"If there are any pending questions, requests, or next steps, mention them. "
                f"Use this as a template if helpful:\n{filled_prompt}"
            )
            logger.info("LLM system prompt: %s", system_prompt)
            logger.info("LLM user prompt: %s", user_prompt)
            # LangChain LLM call
            llm = AzureChatOpenAI(
                openai_api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
                deployment_name=azure_deployment,
                openai_api_version="2023-07-01-preview",
                temperature=0.7,
                max_tokens=512,
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            result = llm(messages)
            logger.info("LLM output: %s", result.content)
            return result.content.strip()
        except Exception as e:
            logger.error("LLM ERROR: %s", e)
            return f"[LLM ERROR: {e}]\n\n{filled_prompt}"
    logger.warning("LLM not called: missing Azure OpenAI configuration.")
    return filled_prompt 