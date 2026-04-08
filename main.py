import os
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime
import PyPDF2
from playwright.sync_api import sync_playwright
import google.generativeai as genai

# ==========================================
# 1. CONFIGURATION (FILL THIS IN)
# ==========================================
PORTAL_EMAIL = "username"
PORTAL_PASSWORD = "examplepassword123"  # Your VTU Internyet password (consider using environment variables for security)
INTERNSHIP_NAME = "exact name of your internship as it appears in the dropdown (e.g. 'VTU Internship - 2026')"

GEMINI_API_KEY = "create one in your Google Cloud Console and paste it here"

SENDER_EMAIL = "example@gmail.com"
EMAIL_APP_PASSWORD = "wzqv wjhd wjpf ztqk(example app password, generate one in your Gmail settings)" 
RECEIVER_EMAIL = "receiver@gmail.com"

# The name of your PDF file in the same folder
PDF_FILE_NAME = "diary_data.pdf"

# ==========================================
# 2. THE AI BRAIN & PDF READER
# ==========================================
def extract_exact_entry(target_pdf_date):
    """Reads the PDF, finds today's date, and copies the exact text."""
    print(f"📄 Reading {PDF_FILE_NAME}...")
    
    # 1. Extract raw text from the PDF
    pdf_text = ""
    try:
        with open(PDF_FILE_NAME, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                pdf_text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Could not read PDF file: {e}. Make sure {PDF_FILE_NAME} is in the folder!")

    print(f"🧠 Asking AI to find exact data for {target_pdf_date}...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    # We use JSON mode to ensure the AI gives us structured data back
    model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
    
    prompt = f"""
    Here is the raw text from my internship diary PDF:
    ---
    {pdf_text}
    ---
    
    1. Find the entry for the exact date: {target_pdf_date}.
    2. Copy the EXACT text for "Work Summary" word-for-word. Do not expand or change it.
    3. Copy the EXACT text for "Learning/Outcome" word-for-word. Do not expand or change it.
    4. Extract the "Skills Used" into an array of individual strings.
    
    Output strictly in this JSON format:
    {{
        "work_summary": "exact copied text here",
        "learning": "exact copied text here",
        "skills": ["skill1", "skill2", "skill3"]
    }}
    """
    
    response = model.generate_content(prompt)
    
    # Convert the JSON string from AI into a Python dictionary
    data = json.loads(response.text)
    print("✅ AI successfully extracted the exact content!")
    return data

# ==========================================
# 3. THE EMAIL MOUTH
# ==========================================
def send_alert_email(subject, body):
    print("📧 Sending email notification...")
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# ==========================================
# 4. THE AUTOMATION HANDS
# ==========================================
def run_automation(diary_data, calendar_date):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("🌐 Navigating to VTU Internyet portal...")
        page.goto("https://vtu.internyet.in/sign-in")
        page.wait_for_load_state("networkidle")

        # --- LOGIN ---
        page.get_by_placeholder("Enter your email address").fill(PORTAL_EMAIL)
        page.locator('input[type="password"]').fill(PORTAL_PASSWORD)
        page.get_by_role("button", name="Sign In").click()
        
        # --- GO TO DIARY PAGE ---
        page.wait_for_url("**/dashboard**", timeout=15000) 
        page.goto("https://vtu.internyet.in/dashboard/student/student-diary")
        page.wait_for_load_state("networkidle")

        # --- SELECT INTERNSHIP AND DATE ---
        page.locator("select").select_option(value="3636")
        page.wait_for_timeout(1000)
        
        page.get_by_text("Pick a Date").click()
        page.wait_for_timeout(1000)
        page.locator(f'[data-day="{calendar_date}"]').click()
        page.get_by_role("button", name="Continue").click()
        
        # --- THE FINAL SUBMISSION PAGE ---
        print("✍️ Typing the extracted content into all fields...")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        
        # 1. Fill Work Summary (Usually the very first text box)
        summary_box = page.locator('textarea').nth(0) 
        summary_box.fill(diary_data['work_summary'])
        
        # 2. Fill Hours Worked (Fixed to 8)
        hours_box = page.locator('input[type="number"], input[placeholder*="Hour"], input[placeholder*="hour"]').first
        hours_box.fill("8")

        # 3. Fill Learning (THE FIX: Using exact placeholder from your screenshot!)
        learning_box = page.get_by_placeholder("What did you learn or ship today?")
        learning_box.fill(diary_data['learning'])

        # 4. Fill Skills Used (React-Select Bypass)
        print("Adding skills...")
        
        # Target the outer container of the React dropdown
        skills_container = page.locator('.react-select__control').first
        
        # Click it to activate the hidden text cursor
        skills_container.click()
        page.wait_for_timeout(500)
        
        # Simulate a human typing on the keyboard to trigger the dropdown search
        for skill in diary_data['skills']:
            page.keyboard.type(skill)
            page.wait_for_timeout(600) # Wait half a second for the UI to find the skill
            page.keyboard.press("Enter")
            page.wait_for_timeout(300) # Wait a moment for the tag to lock in
        
        print("Clicking Submit...")
        page.get_by_role("button", name="Submit").click(no_wait_after=True)
        
        # Wait just a bit to ensure the website registers the submission before closing
        page.wait_for_timeout(5000)
        print("🎉 Diary successfully submitted!")
        browser.close()

# ==========================================
# 5. MAIN EXECUTION LOOP
# ==========================================
if __name__ == "__main__":
    current_day = datetime.now().weekday()
    
    # 2026-04-08 format for the calendar widget
    calendar_date = datetime.now().strftime("%Y-%m-%d") 
    
    # "Apr 08, 2026" format to match your PDF exactly
    pdf_date = datetime.now().strftime("%b %d, %Y")     

    if current_day == 6:
        print("😴 Today is Sunday! The bot is resting.")
    else:
        print("🚀 Starting Automated Diary System...")
        try:
            # 1. Read PDF and get exact JSON data from Gemini
            ai_data = extract_exact_entry(pdf_date)
            
            # 2. Run the web automation with the exact dictionary
            run_automation(ai_data, calendar_date)
            
            # 3. Email receipt
            success_body = f"""
            Your automated bot has successfully logged your daily diary exactly from the PDF.
            
            Date Found: {pdf_date}
            Summary: {ai_data['work_summary']}
            Hours: 8
            Learning: {ai_data['learning']}
            Skills Selected: {', '.join(ai_data['skills'])}
            """
            send_alert_email("✅ VTU Diary Auto-Filled Successfully", success_body)
            
        except Exception as e:
            print(f"🛑 CRITICAL ERROR: {e}")
            send_alert_email("❌ VTU Diary Automation FAILED", str(e))