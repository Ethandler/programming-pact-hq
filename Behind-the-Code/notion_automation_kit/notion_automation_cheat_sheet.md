# 📘 Notion Automation Cheat Sheet (Based on Real UI Options)

Welcome to the internal guide for using **Notion's native automation panel**. This doc outlines every supported **trigger**, **condition**, and **action** currently visible in the system — all verified through screenshots.

---

## ✅ Available Triggers

Triggers are the starting point of any automation. They tell Notion *when* to do something.

### 🔄 Event-Based Triggers

These happen automatically based on general changes:

- `Any property edited`
- `Page added`
- `Every...` *(likely time-based; exact interval options not shown)*

---

### 🧱 Property-Based Triggers

These are based on specific properties in your Notion database.

#### 🅰️ Text Fields (e.g. `Task`, `Notes / Logs`, `Links`, `Links (1)`)

**Supported Logic Operators:**

- `Is set to`
- `Is not set to`
- `Contains`
- `Does not contain`
- `Starts with`
- `Ends with`
- `Is edited`
- `Is cleared`

---

#### 🏷️ Select / Multi-Select Fields

##### Example Fields: `Priority`, `Status`, `Tools Used`

**Logic for Select:**

- `Is`
- `Is not`
- `Is edited`
- `Is cleared`

**Logic for Multi-Select:**

- `Contains`
- `Does not contain`
- `Is edited`
- `Is cleared`

**Observed Dropdown Options:**

- **Priority**:
  - High
  - Medium
  - Low
  - Complete

- **Status**:
  - 🧠 Ideas
  - ⛔ Blocked / Needs Help
  - 🛠 In Progress
  - 🧪 Testing
  - ✅ Completed

- **Tools Used**:
  - Cron, Docker, Git, GitHub, HTML/CSS, JavaScript, Node.js, Notion SDK, Python, R6 Tracker API, Steam API, Terminal, VS Code

---

#### 🔢 Number Fields (e.g. `Time Estimate`, `Difficulty`, `Completion Rate`)

**Supported Logic Operators:**

- `=`
- `≠`
- `>`
- `<`
- `≥`
- `≤`
- `Is edited`
- `Is cleared`

---

#### 👥 Person Fields (`Assigned To`)

**Logic Operators:**

- `Contains`
- `Does not contain`
- `Is edited`
- `Is cleared`

**Visible Users:**

- Ethan Blankenship
- Jimmy
- Chandler Blankenship

---

#### 📅 Date Fields (`Last Updated`)

**Available Operator:**

- `Is edited` only

---

## 🛠️ Available Actions

These are the things Notion can do *after* a trigger fires.

- `Edit property...`
- `Add page to...`
- `Edit pages in...`
- `Send notification to...`
- `Send mail...` *(New)*
- `Send webhook`
- `Send Slack notification to...`
- `Define variables`

---

## 🧪 Example Automations

Here’s how you can use what’s available to build useful workflows:

### 🔔 Auto-alert when a task gets blocked

- **Trigger**: Status `is` Blocked / Needs Help
- **Action**: Send Slack notification

---

### 📧 Email when Time Estimate exceeds 5 hours

- **Trigger**: Time Estimate `>` 5
- **Action**: Send mail...

---

## 🚫 Known Limitations

Based strictly on what’s visible:

- ❌ No support for checkboxes (true/false logic missing)
- ❌ No logic chaining (can’t combine multiple conditions like “if A AND B”)
- ❌ No formula evaluation or complex conditions
- ❌ No branching ("if this, then do A *or* B")
- ❌ No direct date/time scheduling (besides potential `Every...`)
- ❌ No condition-based filtering inside “Send mail” or webhook actions shown

---

## 🧠 Pro Tip

If you want to build **advanced workflows**, consider pairing this with:
- **Make.com or Zapier** (for external logic and API calls)
- **Notion SDK or custom bots** if you're dev-savvy

---

_Last updated: Based on screenshots captured April 17, 2025_
