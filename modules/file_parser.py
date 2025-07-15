import pandas as pd
import json
from PyPDF2 import PdfReader
import os
from collections import defaultdict

def is_email_table(records):
    if not records or not isinstance(records, list):
        return False
    sample = records[0]
    return (
        isinstance(sample, dict) and
        any(k.lower().startswith('from') for k in sample.keys()) and
        'Body' in sample
    )

def group_by_sender(records):
    grouped = defaultdict(list)
    for rec in records:
        sender = rec.get('From: (Address)', rec.get('From', 'Unknown Sender')).strip() or 'Unknown Sender'
        grouped[sender].append(rec)
    return dict(grouped)

def parse_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        df = pd.read_csv(file_path)
        records = df.to_dict(orient='records')
        if is_email_table(records):
            return group_by_sender(records)
        else:
            return {'Single Message': records}
    elif ext == '.json':
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, list) and is_email_table(data):
            return group_by_sender(data)
        elif isinstance(data, dict):
            return data
        else:
            return {'Single Message': data}
    elif ext == '.pdf':
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or '' for page in reader.pages)
        return {'Single Message': [{"Body": text}]}
    elif ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        return {'Single Message': [{"Body": text}]}
    else:
        return {'Single Message': [{"Body": ""}]} 