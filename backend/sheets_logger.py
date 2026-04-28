"""
sheets_logger.py
────────────────
Logs student submission data to a Google Sheet every time a resume is
generated.

Setup (one-time):
  1. Create a Google Cloud project and enable the Google Sheets API +
     Google Drive API.
  2. Create a Service Account, download the JSON key file, and place it
     at backend/credentials.json  (or set the env-var
     GOOGLE_CREDENTIALS_JSON to its contents for cloud deployments).
  3. Share your target Google Sheet with the service-account email
     (Editor permission).
  4. Set the env-var SHEET_ID to the Sheet's ID
     (the long string in its URL between /d/ and /edit).
"""

import os
import json
import datetime

try:
    import pytz
    _IST = pytz.timezone("Asia/Kolkata")
except ImportError:
    _IST = None  # pytz not installed — falls back to server local time

# ── gspread is optional; if missing the feature is silently skipped ──
try:
    import gspread
    from google.oauth2.service_account import Credentials
    _GSPREAD_AVAILABLE = True
except ImportError:
    _GSPREAD_AVAILABLE = False

# ── Constants ────────────────────────────────────────────────────────
_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Hardcoded fallback — used when SHEET_ID env-var is not set
_DEFAULT_SHEET_ID = "1p4djLv3YYCX8DmHuIvHb8zhVKTPih9tR80ihGiWOI1Y"

_HEADER_ROW = [
    "Timestamp",
    "Full Name",
    "Email",
    "Phone",
    "LinkedIn",
    "Education (Degree | Institution | Year | Grade)",
    "GitHub",
]

_SHEET_NAME = "Student Submissions"   # Tab name inside the spreadsheet


def _get_client():
    """Return an authenticated gspread client, or None on failure."""
    if not _GSPREAD_AVAILABLE:
        print("[SheetsLogger] gspread not installed – skipping log.")
        return None

    # ── Prefer env-var (for cloud / Render / Vercel deployments) ──
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        try:
            creds_dict = json.loads(creds_json)
            # Fix: Render sometimes escapes newlines in private_key as literal \n
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
            return gspread.authorize(creds)
        except Exception as exc:
            print(f"[SheetsLogger] Env-var credentials failed: {exc}")
            return None

    # ── Fall back to local file ──
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    creds_file = os.path.join(base_dir, "credentials.json")
    if os.path.exists(creds_file):
        try:
            creds = Credentials.from_service_account_file(creds_file, scopes=_SCOPES)
            return gspread.authorize(creds)
        except Exception as exc:
            print(f"[SheetsLogger] File credentials failed: {exc}")
            return None

    print("[SheetsLogger] No credentials found (set GOOGLE_CREDENTIALS_JSON or place credentials.json in backend/).")
    return None


def _get_or_create_worksheet(spreadsheet):
    """Return the target worksheet, creating it (with headers) if needed."""
    try:
        ws = spreadsheet.worksheet(_SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=_SHEET_NAME, rows=1000, cols=20)
        ws.append_row(_HEADER_ROW)
    else:
        # Ensure header row exists
        if ws.row_count == 0 or ws.row_values(1) != _HEADER_ROW:
            ws.insert_row(_HEADER_ROW, index=1)
    return ws


def _format_education(education_list):
    """Convert education list-of-dicts to a human-readable string."""
    if not education_list:
        return ""
    parts = []
    for edu in education_list:
        degree      = edu.get("degree", "")
        institution = edu.get("institution", "")
        year        = edu.get("year", "")
        grade       = edu.get("grade", "")
        part = " | ".join(filter(None, [degree, institution, year, grade]))
        if part:
            parts.append(part)
    return "  //  ".join(parts)


def log_student(personal_details: dict, github_username: str = "") -> bool:
    """
    Append one row of student data to the Google Sheet.

    Parameters
    ----------
    personal_details : dict
        Keys: full_name, email, phone, linkedin, education (list of dicts)
    github_username  : str
        The GitHub handle the student entered.

    Returns
    -------
    bool  True if logged successfully, False otherwise.
    """
    sheet_id = os.environ.get("SHEET_ID", _DEFAULT_SHEET_ID).strip()

    client = _get_client()
    if client is None:
        return False

    try:
        spreadsheet = client.open_by_key(sheet_id)
        ws          = _get_or_create_worksheet(spreadsheet)

        # Always log in IST regardless of the server's system timezone (EC2 defaults to UTC).
        if _IST is not None:
            timestamp = datetime.datetime.now(_IST).strftime("%Y-%m-%d %H:%M:%S IST")
        else:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        row = [
            timestamp,
            personal_details.get("full_name", ""),
            personal_details.get("email", ""),
            personal_details.get("phone", ""),
            personal_details.get("linkedin", ""),
            _format_education(personal_details.get("education", [])),
            github_username,
        ]
        ws.append_row(row)
        print(f"[SheetsLogger] OK Logged: {personal_details.get('full_name', 'Unknown')} at {timestamp}")
        return True

    except Exception as exc:
        print(f"[SheetsLogger] FAILED to log to Sheets: {exc}")
        return False
