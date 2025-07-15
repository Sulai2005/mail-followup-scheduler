import requests

def send_to_webhook(url, followup_text):
    try:
        response = requests.post(url, json={"followup": followup_text})
        return response.status_code == 200
    except Exception:
        return False 