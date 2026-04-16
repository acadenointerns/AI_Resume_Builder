from flask import Flask, render_template, request, send_file, jsonify
from github_fetcher import fetch_github_profile
from resume_engine import generate_resume
from ats_scoring import score_resume
from sheets_logger import log_student
import os, time, json

app = Flask(__name__)

latest_resume = None
latest_ats = None

def _get_pdf_engine():
    """Attempt to find a working PDF engine."""
    # 1. Try xhtml2pdf (Pure Python, best for portability on Vercel)
    try:
        from xhtml2pdf import pisa
        return "xhtml2pdf", pisa
    except Exception as e:
        print(f"xhtml2pdf not available: {e}")

    # 2. Try WeasyPrint (Might fail on Vercel due to missing shared libs)
    try:
        from weasyprint import HTML
        return "weasyprint", HTML
    except Exception as e:
        print(f"WeasyPrint not available: {e}")

    # 3. Try pdfkit (Fails on Vercel as wkhtmltopdf is usually missing)
    try:
        import pdfkit
        WKHTML_PATH = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        # Check if we are in Vercel environment
        if os.environ.get("VERCEL"):
            WKHTML_PATH = "/usr/local/bin/wkhtmltopdf" # Common path or use binary

        if os.path.exists(WKHTML_PATH) or os.environ.get("VERCEL"):
            config = pdfkit.configuration(wkhtmltopdf=WKHTML_PATH)
            return "pdfkit", (pdfkit, config)
    except Exception as e:
        print(f"pdfkit not available: {e}")

    return None, None

@app.route("/", methods=["GET", "POST"])
def index():
    global latest_resume, latest_ats

    if request.method == "POST":
        github         = request.form["github"].strip()
        portfolio      = request.form.get("portfolio", "")
        job_desc       = request.form["job_description"].strip()
        github_data_raw = request.form.get("github_data")

        # Use client-side data if available (bypasses Render IP blocks)
        if github_data_raw:
            try:
                profile = json.loads(github_data_raw)
                profile["github"] = f"https://github.com/{github.split('/')[-1]}"
            except Exception:
                profile = fetch_github_profile(github)
        else:
            profile = fetch_github_profile(github)

        profile["portfolio"] = portfolio

        # ── Collect personal details from form ──
        personal_details = {
            "full_name":    request.form.get("full_name", "").strip(),
            "email":        request.form.get("email", "").strip(),
            "phone":        request.form.get("phone", "").strip(),
            "linkedin":     request.form.get("linkedin", "").strip(),
            "manual_skills": [
                s.strip() for s in request.form.get("manual_skills", "").split(",")
                if s.strip()
            ],
            "achievements": [
                a.strip() for a in request.form.get("achievements", "").splitlines()
                if a.strip()
            ],
            "education": [],
        }

        # Parse education JSON submitted from JS
        edu_raw = request.form.get("education_data", "[]")
        try:
            personal_details["education"] = json.loads(edu_raw)
        except Exception:
            personal_details["education"] = []

        # Override name if the user supplied one
        if personal_details["full_name"]:
            profile["name"] = personal_details["full_name"]

        resume   = generate_resume(profile, job_desc, personal_details)
        ats_data = score_resume(resume, job_desc)
        ats_score = ats_data["score"]

        latest_resume = resume
        latest_ats    = ats_score

        # ── Log student details to Google Sheets ──────────────────────
        github_username = github.strip().split("/")[-1]
        log_student(personal_details, github_username)
        # ──────────────────────────────────────────────────────────────

        return render_template("result.html", resume=resume, score=ats_score)

    return render_template("index.html")


def _generate_pdf(rendered_html, name):
    # Use /tmp for writing files on Vercel
    if os.environ.get("VERCEL"):
        resumes_dir = "/tmp"
    else:
        base_dir    = os.path.dirname(os.path.abspath(__file__))
        resumes_dir = os.path.join(base_dir, "resumes")
        os.makedirs(resumes_dir, exist_ok=True)

    filename    = f"{name}_{int(time.time())}.pdf"
    output_path = os.path.join(resumes_dir, filename)

    engine_name, engine_tools = _get_pdf_engine()

    if engine_name == "xhtml2pdf":
        with open(output_path, "wb") as f:
            pisa_status = engine_tools.CreatePDF(rendered_html, dest=f)
        if pisa_status.err:
            raise RuntimeError(f"xhtml2pdf error: {pisa_status.err}")
    elif engine_name == "weasyprint":
        engine_tools(string=rendered_html).write_pdf(output_path)
    elif engine_name == "pdfkit":
        pdfkit_mod, config = engine_tools
        options = {
            "enable-local-file-access": "",
            "encoding": "UTF-8",
            "page-size": "A4",
            "margin-top": "15mm",
            "margin-bottom": "15mm",
            "margin-left": "15mm",
            "margin-right": "15mm"
        }
        pdfkit_mod.from_string(rendered_html, output_path, options=options, configuration=config)
    else:
        raise RuntimeError("No PDF engine (xhtml2pdf, WeasyPrint, or wkhtmltopdf) is properly installed/configured.")

    return output_path


@app.route("/download")
def download_resume():
    global latest_resume

    if not latest_resume:
        return "No resume generated yet", 400

    try:
        rendered_html = render_template("resume_pdf.html", resume=latest_resume)
        name          = latest_resume.get('name', 'Resume').replace(" ", "_")
        output_path   = _generate_pdf(rendered_html, name)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{name}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"PDF Error: {str(e)}. Please contact support.", 500


@app.route("/download_custom", methods=["POST"])
def download_custom():
    global latest_resume

    if not latest_resume:
        return "No resume context found", 400

    try:
        name_raw         = request.form.get("name", "Resume")
        name             = name_raw.replace(" ", "_")
        summary_html     = request.form.get("summary_html", "")
        skills_html      = request.form.get("skills_html", "")
        experience_html  = request.form.get("experience_html", "")
        education_html   = request.form.get("education_html", "")
        achievements_html = request.form.get("achievements_html", "")
        contact_html     = request.form.get("contact_html", "")

        rendered_html = render_template(
            "resume_pdf.html",
            resume=latest_resume,
            custom_summary=summary_html,
            custom_skills=skills_html,
            custom_experience=experience_html,
            custom_education=education_html,
            custom_achievements=achievements_html,
            custom_contact=contact_html,
        )

        output_path = _generate_pdf(rendered_html, name)

        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{name}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return f"PDF Error: {str(e)}", 500


@app.route("/debug-sheets")
def debug_sheets():
    """Temporary diagnostic route — remove after confirming sheets works."""
    import json as _json
    report = {}

    # 1. Check env var
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON", "")
    report["GOOGLE_CREDENTIALS_JSON_set"] = bool(creds_json)
    report["SHEET_ID"] = os.environ.get("SHEET_ID", "1p4djLv3YYCX8DmHuIvHb8zhVKTPih9tR80ihGiWOI1Y")

    # 2. Check gspread importable
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        report["gspread_installed"] = True
    except ImportError as e:
        report["gspread_installed"] = False
        report["import_error"] = str(e)
        return jsonify(report)

    # 3. Try to build credentials
    try:
        if creds_json:
            creds_dict = _json.loads(creds_json)
            if "private_key" in creds_dict:
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        else:
            base_dir   = os.path.dirname(os.path.abspath(__file__))
            creds_file = os.path.join(base_dir, "credentials.json")
            with open(creds_file) as f:
                creds_dict = _json.load(f)

        report["service_account_email"] = creds_dict.get("client_email", "not found")
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        report["credentials_built"] = True
    except Exception as e:
        report["credentials_built"] = False
        report["credentials_error"] = str(e)
        return jsonify(report)

    # 4. Try to connect to sheet
    try:
        client      = gspread.authorize(creds)
        sheet_id    = report["SHEET_ID"]
        spreadsheet = client.open_by_key(sheet_id)
        report["sheet_connected"] = True
        report["sheet_title"]     = spreadsheet.title
        worksheets = [ws.title for ws in spreadsheet.worksheets()]
        report["worksheets"] = worksheets
    except Exception as e:
        report["sheet_connected"] = False
        report["sheet_error"]     = str(e)

    return jsonify(report)


@app.route("/admin/submissions")
def admin_submissions():
    """
    Read-only admin view of all logged student submissions from Google Sheets.
    Returns JSON — protect this route with a secret key in production!

    Usage: GET /admin/submissions?key=YOUR_ADMIN_KEY
    Set the env-var ADMIN_KEY to enable protection (leave unset to disable).
    """
    admin_key = os.environ.get("ADMIN_KEY", "")
    if admin_key and request.args.get("key") != admin_key:
        return jsonify({"error": "Unauthorized"}), 401

    _DEFAULT_SHEET_ID = "1p4djLv3YYCX8DmHuIvHb8zhVKTPih9tR80ihGiWOI1Y"
    sheet_id = os.environ.get("SHEET_ID", _DEFAULT_SHEET_ID).strip()

    try:
        import gspread
        from google.oauth2.service_account import Credentials
        import json as _json

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            creds = Credentials.from_service_account_info(
                _json.loads(creds_json), scopes=scopes)
        else:
            base_dir   = os.path.dirname(os.path.abspath(__file__))
            creds_file = os.path.join(base_dir, "credentials.json")
            creds = Credentials.from_service_account_file(creds_file, scopes=scopes)

        client      = gspread.authorize(creds)
        spreadsheet = client.open_by_key(sheet_id)
        ws          = spreadsheet.worksheet("Student Submissions")
        rows        = ws.get_all_records()
        return jsonify({"count": len(rows), "submissions": rows})

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
