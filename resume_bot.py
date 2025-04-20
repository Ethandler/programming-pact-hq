"""
Desktop Resume Automation Bot
Author: Ethan Blankenship
Description:
  • Collects resume data (CLI prompt or JSON payload).
  • Sends to OpenAI GPT‑4 to generate polished 2‑page resume.
  • Creates PDF (ReportLab) and saves locally.
  • Uploads PDF to a private GitHub Gist.
  • Logs job to a Notion database.
  • Sends email draft with PDF attached (optional SMTP).
Requirements:
  python -m pip install openai notion-client PyGithub reportlab python-dotenv requests
Environment Variables (export or .env):
  OPENAI_API_KEY   - Your OpenAI key
  NOTION_TOKEN     - Internal integration token
  NOTION_DB_ID     - Database for resume logs
  GITHUB_TOKEN     - Personal access token with gist scope
"""
import os, sys, json, textwrap, datetime, tempfile, smtplib, ssl, requests
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from github import Github
from notion_client import Client as Notion
import openai

# ---------- config ----------
MODEL          = "gpt-4o-mini"   # cheaper turbo; change if needed
PAGE_WIDTH, PAGE_HEIGHT = LETTER
MARGIN = 72  # 1 inch

# ---------- helpers ----------
def prompt_user():
    print("=== Enter Resume Fields ===")
    name     = input("Full Name: ")
    contact  = input("Contact (email / phone / LinkedIn): ")
    jobs     = []
    print("Enter work history rows 'Title | Company | Years' (blank to finish)")
    while True:
        row = input("> ")
        if not row.strip():
            break
        jobs.append(row)
    education = input("Education: ")
    skills    = input("Skills (comma‑separated): ")
    summary   = input("Custom Summary/Objectives: ")
    return dict(name=name, contact=contact, jobs=jobs, education=education,
                skills=skills, summary=summary)

def build_prompt(data:dict)->str:
    return textwrap.dedent(f\"\"\"
    Create a two‑page, ATS‑optimized resume with the following details:

    Name: {data['name']}
    Contact: {data['contact']}

    Work History:
    {'\\n'.join(data['jobs']) or 'None provided'}

    Education: {data['education']}
    Skills: {data['skills']}
    Summary: {data['summary']}

    Use clear section headings, bullet points, and consistent formatting.
    \"\"\").strip()

def call_openai(prompt:str)->str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role":"user","content":prompt}],
        max_tokens=1800,
        temperature=0.7
    )
    return resp.choices[0].message.content.strip()

def pdf_from_text(text:str, outfile:str):
    c = canvas.Canvas(outfile, pagesize=LETTER)
    width, height = LETTER
    y = height - MARGIN
    for line in text.splitlines():
        if y < MARGIN:
            c.showPage()
            y = height - MARGIN
        c.drawString(MARGIN, y, line)
        y -= 12
    c.save()

def upload_gist(filename:str, data:bytes)->str:
    gh = Github(os.getenv("GITHUB_TOKEN"))
    gist = gh.get_user().create_gist(
        public=False,
        files={os.path.basename(filename):{"content":data.decode('latin1'),"encoding":"base64"}}
    )
    return gist.html_url, gist.raw_url

def log_notion(name:str, gist_url:str, price:int=75):
    notion = Notion(auth=os.getenv("NOTION_TOKEN"))
    notion.pages.create(**{
        "parent":{"database_id": os.getenv("NOTION_DB_ID")},
        "properties":{
            "Name":{"title":[{"text":{"content":name}}]},
            "Date":{"date":{"start":datetime.datetime.utcnow().isoformat()}},
            "Status":{"select":{"name":"Completed"}},
            "Gist":{"url": gist_url},
            "Price":{"number": price}
        }
    })

def main():
    data = prompt_user()
    prompt = build_prompt(data)
    print("\\n[+] Generating resume with GPT‑4…")
    resume_txt = call_openai(prompt)
    tmp_pdf = tempfile.NamedTemporaryFile(delete=False,suffix=".pdf").name
    pdf_from_text(resume_txt, tmp_pdf)
    print(f"[+] PDF saved → {tmp_pdf}")

    print("[+] Uploading to Gist…")
    with open(tmp_pdf,"rb") as f:
        pdf_b64 = f.read().encode("base64")
    html_url, raw_url = upload_gist(tmp_pdf, pdf_b64)
    print(f"[+] Gist URL: {html_url}")

    print("[+] Logging to Notion…")
    log_notion(data['name'], html_url)

    print("[✓] Done! Share URL or PDF as needed.")

if __name__ == "__main__":
    main()
