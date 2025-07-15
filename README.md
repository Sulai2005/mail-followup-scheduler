# 📧 Follow-Up Generator

A modern, modular app to generate professional, context-aware follow-up emails from your email data.  
Supports both a user-friendly Streamlit UI and a REST API (FastAPI) for automation and integration.

---

## 🚀 Features

- **Upload CSV, JSON, PDF, or TXT files** containing email data or text.
- **Automatic context extraction**: Groups, analyzes, and summarizes conversation history for each recipient.
- **LLM-powered follow-up generation**: Uses Azure OpenAI (via LangChain) to generate concise, professional, and non-spammy follow-ups.
- **Custom prompt support**: Guide the LLM with your own prompt template (optional).
- **Webhook integration**: Send generated follow-ups to any webhook.
- **REST API**: Automate follow-up generation from other apps or workflows.

---

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd FollowUp\ Generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Azure OpenAI environment variables:**
   ```bash
   # On Windows (PowerShell)
   $env:AZURE_OPENAI_API_KEY="your-azure-api-key"
   $env:AZURE_OPENAI_ENDPOINT="https://YOUR_RESOURCE_NAME.openai.azure.com"
   $env:AZURE_OPENAI_DEPLOYMENT="your-deployment-name"
   ```

   Or create a `.env` file in the project root:
   ```
   AZURE_OPENAI_API_KEY=your-azure-api-key
   AZURE_OPENAI_ENDPOINT=https://YOUR_RESOURCE_NAME.openai.azure.com
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   ```

---

## 💻 Usage

### **Streamlit App (UI)**

```bash
streamlit run app.py
```

- Open [http://localhost:8501](http://localhost:8501) in your browser.
- Upload your file, select a recipient, (optionally) enter a custom prompt, and generate a follow-up.
- Download the result or send it to a webhook.

---

### **REST API (FastAPI)**

The API runs automatically in the background on port 8001 when you start the Streamlit app.

#### **Endpoint**
```
POST /generate-followup
```

#### **Form Data**
- `file`: (file upload, required)
- `prompt`: (string, optional)
- `recipient`: (string, optional)

#### **Example cURL**
```bash
curl -X POST "http://localhost:8001/generate-followup" \
  -F "file=@yourfile.csv" \
  -F "recipient=recipient@example.com"
```

#### **API Docs**
- [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 🧩 Project Structure

```
FollowUp Generator/
│
├── app.py                  # Streamlit UI + FastAPI API
├── requirements.txt
├── modules/
│     ├── file_parser.py
│     ├── email_analyzer.py
│     └── followup_generator.py
├── utils/
│     ├── prompt_template.py
│     └── webhook.py
```

---

## ⚙️ Configuration

- **Custom prompt:** Use `{name}`, `{topic}`, etc. as variables in your prompt.
- **LLM settings:** Controlled via environment variables and `.env`.
- **Webhook:** Enter a URL in the UI or via API to POST the generated follow-up.

---

## 📝 Example Workflow

1. Upload a CSV/JSON/PDF/TXT file with email data.
2. Select a recipient (if multiple).
3. (Optional) Enter a custom prompt.
4. Click “Generate Follow-Up.”
5. Download the result or send it to a webhook.

---

## 🧠 How It Works

- **Context extraction:** The app analyzes your data, finds all messages relevant to the recipient, and extracts the most important sentences and recent content.
- **LLM prompt:** The app builds a detailed, professional prompt for the LLM, ensuring the follow-up is concise, actionable, and not spammy.
- **Output:** The LLM generates a follow-up email that references the actual conversation and is ready to send.

---

## 📦 Dependencies

- streamlit
- pandas
- PyPDF2
- requests
- openai
- langchain

---