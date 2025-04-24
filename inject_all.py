from dotenv import load_dotenv
import os, json
from notion_client import Client

# Load your secret token from `.env`
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

# Hardcoded Notion page IDs (pre-locked)
PAGE_IDS = {
    "Jimmy": "1dacccbb43388030847ce08e774476f4",
    "Chan":  "1dacccbb433880bf8ea6d5d64bc9a94f",
    "Ethan": "1dacccbb4338806ebd0de59087572b5c"
}

# Path to mission brief files
FILE_PATHS = {
    "Jimmy": "Jimmy_Mission_Notion.json",
    "Chan":  "Chan_Mission_Notion.json",
    "Ethan": "ResumeBot_Mission_Notion.json"
}

notion = Client(auth=NOTION_TOKEN)

def inject_json(page_id, json_path):
    with open(json_path, "r") as f:
        data = json.load(f)
    data["parent"]["page_id"] = page_id
    result = notion.pages.create(**data)
    print(f"✅ Injected to {page_id}: {result['url']}")

# Run injections
for name in PAGE_IDS:
    try:
        inject_json(PAGE_IDS[name], FILE_PATHS[name])
    except Exception as e:
        print(f"❌ {name} failed: {e}")