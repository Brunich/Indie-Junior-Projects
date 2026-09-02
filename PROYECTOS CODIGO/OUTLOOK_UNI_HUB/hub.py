import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from O365 import Account, FileSystemTokenBackend
import google.generativeai as genai
import pdfplumber
from icalendar import Calendar, Event

# Load environment variables from a .env file (if present)
load_dotenv()

# Setup paths
BASE_DOWNLOAD_DIR = Path.home() / "Downloads" / "University"
BASE_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

CLIENT_ID = os.environ.get('AZURE_CLIENT_ID', 'YOUR_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    # Using gemini-1.5-flash for fast text tasks
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# Define keywords for class categorization (fallback logic if no Gemini API key)
CLASS_KEYWORDS = {
    "Math": ["math", "calculus", "algebra", "geometry", "equations"],
    "Physics": ["physics", "mechanics", "thermodynamics", "quantum", "gravity"],
    "Computer Science": ["programming", "code", "python", "java", "algorithms", "software"],
    "History": ["history", "war", "century", "revolution", "ancient"],
    "Literature": ["literature", "poem", "essay", "novel", "reading"]
}

def determine_class_name(subject: str, body: str) -> str:
    """
    Determines the class name based on the email's subject and body.
    Uses Gemini if an API key is provided, otherwise falls back to keyword matching.
    """
    if model:
        try:
            prompt = f"""
            You are an assistant organizing a university student's files.
            Given the following email subject and body, determine the name of the class or subject.
            CRITICAL: Return ONLY the subject name (e.g., "Physics", "Calculus", "Computer Science") and NOTHING else. Do not use quotes.
            If you can't determine it, return "Uncategorized".
            
            Subject: {subject}
            Body: {body[:1000]} # Limit body to save tokens
            """
            response = model.generate_content(prompt)
            lines = [line.strip() for line in response.text.splitlines() if line.strip()]
            class_name = lines[0].strip('"').strip("'") if lines else "Uncategorized"
            # Clean up invalid characters for a folder name
            class_name = re.sub(r'[\\/*?:"<>|]', "", class_name)
            return class_name if class_name else "Uncategorized"
        except Exception as e:
            print(f"Gemini API error, falling back to keywords: {e}")

    # Fallback keyword logic
    text_to_search = f"{subject} {body}".lower()
    for class_name, keywords in CLASS_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_to_search:
                return class_name
                
    return "Uncategorized"

def process_inbox(account):
    """
    Scans the inbox for emails with attachments and processes them.
    """
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()
    
    print("Fetching recent emails with attachments...")
    # Fetch recent messages that have attachments
    query = mailbox.new_query().filter("hasAttachments eq true")
    messages = inbox.get_messages(limit=25, query=query)
    
    for msg in messages:
        # Example filtering: uncomment to only process .edu emails
        # sender_email = msg.sender.address
        # if not sender_email.endswith(".edu"):
        #     continue

        subject = msg.subject
        body = msg.body
        
        # Determine class based on subject and body
        class_name = determine_class_name(subject, body)
        class_dir = BASE_DOWNLOAD_DIR / class_name
        
        if msg.has_attachments:
            # Note: with python-o365, attachments need to be fetched 
            msg.attachments.download_attachments()
            
            for attachment in msg.attachments:
                file_name = attachment.name
                ext = file_name.split('.')[-1].lower() if '.' in file_name else ''
                
                if ext in ['pdf', 'docx', 'xlsx']:
                    # Create class directory only when we actually have a file to save
                    class_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Downloading '{file_name}' for class '{class_name}'...")
                    # Evitar sobreescritura si ya existe un archivo con ese nombre
                    save_path = class_dir / file_name
                    counter = 1
                    while save_path.exists():
                        name, extension = os.path.splitext(file_name)
                        save_path = class_dir / f"{name}_{counter}{extension}"
                        counter += 1
                        
                    # Save attachment directly to the class directory
                    attachment.save(location=str(class_dir), custom_name=save_path.name)
                    print(f"Saved to: {save_path}")
                    
                    if ext == 'pdf':
                        try:
                            with pdfplumber.open(save_path) as pdf:
                                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                                
                            cal = Calendar()
                            cal.add('prodid', '-//University Hub Calendar//mxm.dk//')
                            cal.add('version', '2.0')
                            
                            events_added = False
                            for line in text.split('\n'):
                                line_lower = line.lower()
                                if any(kw in line_lower for kw in ['exam', 'midterm', 'final']):
                                    date_match = re.search(r'\b(\d{1,4}[-/]\d{1,2}[-/]\d{1,4})\b', line)
                                    if date_match:
                                        date_str = date_match.group(1)
                                        event_date = None
                                        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d'):
                                            try:
                                                event_date = datetime.strptime(date_str, fmt)
                                                break
                                            except ValueError:
                                                pass
                                        
                                        if event_date:
                                            event = Event()
                                            event.add('summary', f'{class_name} Event: {line.strip()[:40]}')
                                            event.add('dtstart', event_date.date())
                                            event.add('dtend', event_date.date())
                                            event.add('uid', str(uuid.uuid4()))
                                            cal.add_component(event)
                                            events_added = True
                            
                            if events_added:
                                ics_path = class_dir / "calendar_events.ics"
                                with open(ics_path, 'wb') as f:
                                    f.write(cal.to_ical())
                                print(f"Generated calendar events at: {ics_path}")
                        except Exception as e:
                            print(f"Error processing PDF {save_path.name}: {e}")

def main():
    if CLIENT_ID == 'YOUR_CLIENT_ID' or not CLIENT_ID:
        print("Please set your AZURE_CLIENT_ID and AZURE_CLIENT_SECRET in the .env file.")
        return

    credentials = (CLIENT_ID, CLIENT_SECRET)
    
    # Use FileSystemTokenBackend to store the token locally so we don't have to authenticate every time
    token_backend = FileSystemTokenBackend(token_path='.', token_filename='o365_token.txt')
    
    account = Account(credentials, token_backend=token_backend)
    
    # Scopes needed to read emails
    scopes = ['basic', 'message_all']
    
    if not account.is_authenticated:
        print("Authenticating with Microsoft Graph...")
        account.authenticate(scopes=scopes)
        print("Authenticated successfully!")
    else:
        print("Already authenticated.")
    
    print("Scanning inbox for university files...")
    process_inbox(account)
    print("Finished scanning inbox.")

if __name__ == "__main__":
    main()
