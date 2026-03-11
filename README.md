# CRE Comp Intake Normalizer

Turn messy broker PDFs and email blasts into clean, structured rows for your comp database — in seconds.

Upload an Offering Memorandum, and the app automatically pulls out the address, unit count, asking price, NOI, cap rate, expenses, broker info, and ~60 other fields. Review the results in an editable table, then export to Excel or CSV.

---

## What You Need Before Starting

You need three things installed on your computer. Each one is free.

### 1. Python
Python is the programming language this app runs on.

- Go to **python.org/downloads**
- Click the big yellow "Download Python" button
- Run the installer
- **Important:** On the first screen of the installer, check the box that says **"Add Python to PATH"** before clicking Install

To confirm it worked, open PowerShell (search "PowerShell" in your Start menu) and type:
```
python --version
```
You should see something like `Python 3.13.0`. If you do, you're good.

### 2. Git
Git is what lets you download this project from GitHub.

- Go to **git-scm.com/download/win**
- Download and run the installer
- Click "Next" through all the default options — the defaults are fine

### 3. An Anthropic API Key
This app uses Claude (an AI model made by Anthropic) to read the PDFs. You need an account to get a key.

- Go to **console.anthropic.com** and sign up
- Click **"API Keys"** in the left sidebar
- Click **"Create Key"**, give it any name, and copy the key (it starts with `sk-ant-`)
- Save it somewhere safe — you only see it once

You'll need to add a small amount of credit to your account (under Settings → Billing). Each PDF extraction costs roughly **$0.05–$0.10**.

---

## Installation (Do This Once)

Open **PowerShell** (search "PowerShell" in your Start menu).

**Step 1 — Download the project:**
```
git clone https://github.com/YOUR-USERNAME/YOUR-REPO-NAME.git
```
This creates a folder called `comp-intake-normalizer` wherever you ran the command.

**Step 2 — Go into that folder:**
```
cd comp-intake-normalizer
```

**Step 3 — Install the app's dependencies:**
```
python -m pip install -r requirements.txt
```
This downloads a few packages the app needs. It may take a minute.

**Step 4 — Add your API key:**

In the project folder, find the file called `.env.example`. Make a copy of it and rename the copy to `.env` (just `.env`, no ".example"). Open it in Notepad and replace the placeholder with your actual key:

```
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
```

Save and close the file.

---

## Running the App

Every time you want to use the app, open PowerShell, navigate to the project folder, and run:

```
cd comp-intake-normalizer
python -m streamlit run app.py
```

Your browser will automatically open to `http://localhost:8501` with the app running.

To stop the app, go back to PowerShell and press **Ctrl + C**.

---

## How to Use It

**Uploading a PDF:**
1. Click the **"Upload PDFs"** tab
2. Drag and drop one or more broker OMs onto the upload area (or click to browse)
3. Click **"Extract All"**
4. Wait ~10–20 seconds per PDF while the AI reads it

**Pasting an email blast:**
1. Click the **"Paste Text"** tab
2. Copy the text from the broker email and paste it into the text box
3. Give it a short label (e.g. "Eastdil blast 3-11") so you can identify it later
4. Click **"Extract All"**

**Reviewing results:**
- Results appear in a table below
- **Yellow cells** mean that field wasn't found in the document — you can click any cell to fill it in manually
- The **Confidence** column tells you how complete the extraction was (High / Medium / Low)

**Exporting:**
- **Download CSV** — opens in Excel, Google Sheets, etc.
- **Download Excel** — pre-formatted with frozen headers and currency columns
- **Copy to Clipboard** — pastes directly into an open Excel spreadsheet with Ctrl+V

---

## Troubleshooting

**"python is not recognized"**
You forgot to check "Add Python to PATH" during installation. Uninstall Python and reinstall it, making sure to check that box.

**"No API key set" warning in the sidebar**
Either your `.env` file is missing, it's still named `.env.example`, or the key inside it has a typo. Double-check the file name and contents.

**Extraction returns mostly blank fields**
The document may be a scanned image rather than a real PDF (common with older OMs). The app reads text-based PDFs best. Try a different file, or manually fill in the yellow cells.

**The app won't start / port already in use**
Another instance is already running. Either close the other PowerShell window running the app, or add `--server.port 8502` to the run command to use a different port.

---

## Questions?

Reach out to whoever set this up for your team. If something is broken, the most helpful thing you can do is copy the red error message from PowerShell and send it along.
