"""
generate_readme.py – Creates a stylized README.md file for your GitHub repo

This script includes:
- A banner link
- Team roles
- Project roadmap
- Helpful links
"""

readme_content = """# ![The Programming Pact](./programming_pact_banner.png)

> **"Code is our weapon. Freedom is our mission. Brotherhood is the protocol."**

Welcome to the **Programming Pact HQ** — a digital stronghold forged by Ethan, Chandler, and Jimmy.

...

**Let’s build something the system can’t ignore.**
"""

with open("README.md", "w") as f:
    f.write(readme_content)
