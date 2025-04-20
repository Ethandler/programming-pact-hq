from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas

# Define file path
pdf_path = "/mnt/data/Programming_Pact_Onboarding_Example.pdf"

# Start canvas
c = canvas.Canvas(pdf_path, pagesize=LETTER)
width, height = LETTER

# Set title
c.setFont("Helvetica-Bold", 16)
c.drawCentredString(width / 2, height - 40, "Programming Pact – Onboarding Guide")

# Set font for content
c.setFont("Helvetica", 11)

def write_block(title, body, y_start):
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y_start, title)
    c.setFont("Helvetica", 11)
    y = y_start - 15
    for line in body.split("\n"):
        if y < 50:
            c.showPage()
            y = height - 50
        c.drawString(50, y, line)
        y -= 15
    return y - 20

y = height - 80
y = write_block("Step 1: Join the Pact Tools", """- Notion HQ: https://www.notion.so/team/1d4cccbb-4338-8119-8dfb-00423fb14f30/join
- GitHub HQ: https://github.com/Ethandler/programming-pact-hq
Create a GitHub account and request access to both links above.""", y)

y = write_block("Step 2: Get Set Up (First Tools)", """1. Install VS Code
2. Install Python from python.org
3. Follow the team's Getting Started Guide in Notion for tool walkthroughs
4. Clone or fork the HQ repo for practice""", y)

y = write_block("Step 3: Learn Your First Language", """Start with Python. It's readable, powerful, and used in automation, scripting, AI, and cybersecurity.

Try:
- Python Basics video (linked in Notion)
- Your first script: push 'hello world' to GitHub
- Build the File Organizer bot with the team""", y)

y = write_block("Step 4: Mission Tracker and Wiki", """Use the Mission Tracker in Notion to keep track of what you're working on.

Our Pact Wiki includes:
- Security terminology
- Coding best practices
- Member roles and team values""", y)

y = write_block("Next Level", """Once you're in, we move fast.
Together we're building:
- Bots
- Freelance projects
- Tools to resell
- Cybersecurity careers

This isn't a club. This is training for a future career built on skill, loyalty, and growth.

If you ever get stuck:
ChatGPT prompt: "I'm in the Programming Pact and need help with [your issue]. Where should I start?" """, y)

c.save()