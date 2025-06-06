from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import uuid
import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

app = FastAPI()

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets setup from environment variable (safe method)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if not creds_json:
    raise RuntimeError("Missing GOOGLE_CREDENTIALS environment variable")
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(creds_json), scope)
sheet = gspread.authorize(creds).open_by_key("1BC3SFnh8ZJFwVWLzKknzlrb8-G8do80ZgW-FGPIzQyc").worksheet("leads")

# Data Model
class CheckRequest(BaseModel):
    email: str
    ref: str = "none"

@app.post("/api/check-leak")
async def check_leak(data: CheckRequest):
    email = data.email.strip().lower()
    ref = data.ref.strip()

    # 1. Run h8mail with subprocess
    try:
        process = subprocess.run(["h8mail", "-t", email, "-o", "output.txt"], capture_output=True, text=True, timeout=20)
        result_output = process.stdout or "Check completed."
    except Exception as e:
        return {"status": "error", "message": f"Error running h8mail: {e}"}

    # 2. Save to Google Sheet (if not already)
    existing = sheet.findall(email)
    if not existing:
        sheet.append_row([email, ref, str(uuid.uuid4())])

    return {"status": "ok", "message": result_output or "Check complete."}
