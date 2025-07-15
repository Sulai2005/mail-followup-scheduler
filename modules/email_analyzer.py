from modules.followup_generator import extract_important_sentences

def analyze_emails(parsed_data):
    # If it's a list of dicts (CSV/JSON), use the first record for demo
    if isinstance(parsed_data, list) and parsed_data and isinstance(parsed_data[0], dict):
        record = parsed_data[0]
        # Extract some fields if present
        name = record.get('From: (Name)', 'User')
        topic = record.get('Subject', 'General Topic')
        return {'name': name, 'topic': topic, 'body': record.get('Body', '')}
    # If it's a list of dicts with only 'Body' (PDF/TXT), use the first
    elif isinstance(parsed_data, list) and parsed_data and 'Body' in parsed_data[0]:
        return {'name': 'User', 'topic': 'General Topic', 'body': parsed_data[0]['Body']}
    else:
        return {'name': 'User', 'topic': 'General Topic', 'body': ''}

def get_senders_summary(grouped_data):
    """Return a summary of senders and email counts for UI selection."""
    return {sender: len(emails) for sender, emails in grouped_data.items()}


def extract_context_for_sender(grouped_data, recipient, subject=None):
    """Extract context for a given recipient (and optionally a subject/thread)."""
    emails = grouped_data.get(recipient, [])
    if not emails:
        return {'name': recipient, 'topic': 'No emails', 'body': ''}
    if subject:
        emails = [e for e in emails if e.get('Subject') == subject]
    relevant_emails = []
    for e in emails:
        from_addr = e.get('From: (Address)', '')
        to_addr = e.get('To: (Address)', '')
        cc_addr = e.get('CC', '')
        if (
            recipient in from_addr
            or recipient in to_addr
            or (isinstance(cc_addr, str) and recipient in cc_addr)
        ):
            relevant_emails.append(e)
    if not relevant_emails:
        relevant_emails = emails
    # Max context length for LLM (characters)
    max_context_len = 3500
    min_context_len = 500
    # 1. Collect important sentences from all relevant emails
    important_content = ''
    for e in relevant_emails:
        body = e.get('Body', '')
        important_content += extract_important_sentences(body, max_context_len, min_context_len) + '\n'
    important_content = important_content.strip()
    # 2. If space remains, append as much of the most recent full message bodies as possible
    bodies_added = 0
    for e in reversed(relevant_emails):
        if len(important_content) >= max_context_len:
            break
        body = e.get('Body', '')
        to_add = body[:max_context_len - len(important_content)]
        if to_add:
            important_content += '\n' + to_add
            bodies_added += 1
    important_content = important_content[:max_context_len]
    # 3. If still too short, add a fallback line
    if len(important_content) < min_context_len:
        important_content += '\nI wanted to check in regarding our previous discussion. Please let me know if you have any updates or need further information.'
    email = relevant_emails[-1]
    name = email.get('From: (Name)', recipient)
    topic = email.get('Subject', 'General Topic')
    return {'name': name, 'topic': topic, 'body': important_content.strip()} 