# VTU Automated Internship Diary Bot 🤖

A fully automated Python script that reads internship daily logs from a PDF, uses Google's **Gemini 2.5 AI** to extract and format the exact text, and uses **Playwright** to automatically navigate the VTU Internyet portal, bypass custom React dropdowns, and submit the daily entry. 

**Features:**
- 📄 Extracts exact daily notes from a local PDF.
- 🧠 Uses Gemini 2.5 Flash to parse unstructured text.
- 🌐 Fully automates Chromium browser to navigate the portal and handle complex UI widgets.
- 📧 Sends an automated success/failure email receipt via Google SMTP.
- 🚫 Smart scheduling (automatically skips Sundays).
