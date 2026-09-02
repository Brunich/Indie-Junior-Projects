import streamlit as st
import os.path
import base64
import re
import time
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import google.generativeai as genai
from dotenv import load_dotenv

# Page config must be the first Streamlit command
st.set_page_config(page_title="Morning Briefing", page_icon="🌅", layout="wide")

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #1a2a6c, #112b3c, #0a192f);
        color: #e6f1ff;
    }
    
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .email-card {
        background-color: rgba(17, 34, 64, 0.7);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        border: 1px solid rgba(100, 255, 218, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        animation: fadeInUp 0.6s ease-out forwards;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    .email-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        border-color: rgba(100, 255, 218, 0.3);
    }
    
    .badge {
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: inline-block;
        margin-bottom: 12px;
    }
    
    .badge-important { background-color: rgba(255, 107, 107, 0.15); color: #ff6b6b; border: 1px solid rgba(255, 107, 107, 0.3); }
    .badge-spam { background-color: rgba(254, 202, 87, 0.15); color: #feca57; border: 1px solid rgba(254, 202, 87, 0.3); }
    .badge-quarantine { background-color: rgba(72, 219, 251, 0.15); color: #48dbfb; border: 1px solid rgba(72, 219, 251, 0.3); }
    
    h1, h2, h3 {
        color: #ccd6f6 !important;
        font-weight: 800 !important;
    }
    
    .email-subject {
        font-size: 1.25rem;
        margin-bottom: 8px;
        color: #ccd6f6;
        font-weight: 600;
    }
    
    .sender-text {
        font-size: 0.9rem;
        color: #8892b0;
        margin-bottom: 16px;
    }
    
    .summary-text {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #a8b2d1;
        padding-left: 16px;
        border-left: 3px solid rgba(100, 255, 218, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                st.error("⚠️ `credentials.json` not found. Please follow the instructions in README.md to download it.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_body_from_payload(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
            elif part['mimeType'] == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    body = soup.get_text(separator=' ')
            elif 'parts' in part:
                nested_body = get_body_from_payload(part)
                if nested_body:
                    return nested_body
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
    return body

def extract_email_data(message_payload):
    headers = message_payload.get("headers", [])
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
    
    body = get_body_from_payload(message_payload)
    return subject, sender, body.strip()

@st.cache_data(show_spinner=False)
def analyze_email_with_gemini(subject, sender, body):
    if not api_key:
        return "QUARANTINE", "Gemini API key not found. Please add GEMINI_API_KEY to .env"
        
    prompt = f"""
    Analyze the following email to determine if it is important, definite spam/newsletter, or something in-between.
    Sender: {sender}
    Subject: {subject}
    Body snippet: {body[:1500]}
    
    Tasks:
    1. Categorize it into EXACTLY ONE of these categories: 'IMPORTANT', 'SPAM', or 'QUARANTINE'. 
       - 'IMPORTANT': Personal emails, direct work communications, receipts, reservations, or critical info.
       - 'SPAM': >90% sure it's a mass promotion, useless newsletter, or pure spam.
       - 'QUARANTINE': Gray-area newsletters, automated emails that might be useful, or anything you aren't absolutely sure about deleting.
    2. Summarize the email in exactly 3 short bullet points.
    
    Output exactly in this format (no markdown code blocks, just raw text):
    CATEGORY: [category]
    SUMMARY:
    - [bullet 1]
    - [bullet 2]
    - [bullet 3]
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text
        
        category_match = re.search(r'CATEGORY:\s*([A-Z]+)', text)
        category = category_match.group(1) if category_match else "QUARANTINE"
        if category not in ["IMPORTANT", "SPAM", "QUARANTINE"]:
            category = "QUARANTINE"
            
        summary_match = re.search(r'SUMMARY:\s*(.*)', text, re.DOTALL)
        summary = summary_match.group(1).strip() if summary_match else "Could not generate summary."
        
        return category, summary
    except Exception as e:
        return "QUARANTINE", f"Could not summarize: {str(e)}"

def archive_email(service, msg_id):
    try:
        service.users().messages().modify(
            userId='me', id=msg_id, body={'removeLabelIds': ['INBOX']}
        ).execute()
        return True
    except Exception as e:
        st.error(f"Failed to archive {msg_id}: {e}")
        return False

def trash_email(service, msg_id):
    try:
        service.users().messages().trash(userId='me', id=msg_id).execute()
        return True
    except Exception as e:
        st.error(f"Failed to trash {msg_id}: {e}")
        return False

def main():
    apply_custom_css()
    
    st.title("🌅 Morning Gmail Briefing")
    st.write("Your intelligent, AI-powered daily email digest.")
    
    if not os.path.exists('.env'):
        st.warning("⚠️ `.env` file not found. Please create one with `GEMINI_API_KEY=your_key`.")
    
    service = get_gmail_service()
    if not service:
        return
        
    if "emails_data" not in st.session_state:
        st.session_state.emails_data = []
        st.session_state.scanned = False
        
    col1, col2 = st.columns([1, 3])
    with col1:
        num_emails = st.number_input("Number of recent emails to fetch", min_value=1, max_value=50, value=10)
        scan_btn = st.button("🔍 Scan Inbox")
        
    if scan_btn:
        with st.spinner("Fetching emails from Gmail..."):
            results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=num_emails).execute()
            messages = results.get('messages', [])
            
            if not messages:
                st.info("Your inbox is empty! Go enjoy your day. ☕")
                return
                
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            emails_data = []
            for i, msg in enumerate(messages):
                status_text.text(f"Analyzing email {i+1} of {len(messages)}...")
                msg_full = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                subject, sender, body = extract_email_data(msg_full['payload'])
                
                category, summary = analyze_email_with_gemini(subject, sender, body)
                time.sleep(1.5) # Prevent hitting free-tier rate limits
                
                emails_data.append({
                    "id": msg['id'],
                    "subject": subject,
                    "sender": sender,
                    "category": category,
                    "summary": summary
                })
                progress_bar.progress((i + 1) / len(messages))
                
            st.session_state.emails_data = emails_data
            st.session_state.scanned = True
            st.success("Analysis complete!")
            st.rerun()

    if st.session_state.scanned:
        emails = st.session_state.emails_data
        
        important = [e for e in emails if e['category'] == 'IMPORTANT']
        quarantine = [e for e in emails if e['category'] == 'QUARANTINE']
        spam = [e for e in emails if e['category'] == 'SPAM']
        
        tab1, tab2, tab3 = st.tabs([
            f"⭐ Important ({len(important)})", 
            f"🛡️ Quarantine Zone ({len(quarantine)})", 
            f"🗑️ Spam/Newsletters ({len(spam)})"
        ])
        
        with tab1:
            if not important:
                st.info("No important emails found.")
            for e in important:
                formatted_summary = e['summary'].replace('\n', '<br>')
                st.markdown(f"""
                <div class="email-card">
                    <span class="badge badge-important">IMPORTANT</span>
                    <div class="email-subject">{e['subject']}</div>
                    <div class="sender-text">From: {e['sender']}</div>
                    <div class="summary-text">{formatted_summary}</div>
                </div>
                """, unsafe_allow_html=True)
                
        with tab2:
            st.warning("These emails might be newsletters or promotions, but Gemini wasn't >90% sure they are useless. Review them manually.")
            if not quarantine:
                st.info("Quarantine zone is clear.")
            for e in quarantine:
                with st.container():
                    formatted_summary = e['summary'].replace('\n', '<br>')
                    st.markdown(f"""
                    <div class="email-card">
                        <span class="badge badge-quarantine">QUARANTINE</span>
                        <div class="email-subject">{e['subject']}</div>
                        <div class="sender-text">From: {e['sender']}</div>
                        <div class="summary-text">{formatted_summary}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("📦 Archive", key=f"q_arch_{e['id']}"):
                            if archive_email(service, e['id']):
                                st.session_state.emails_data = [em for em in st.session_state.emails_data if em['id'] != e['id']]
                                st.success("Archived!")
                                st.rerun()
                    with col_b:
                        if st.button("🗑️ Delete", key=f"q_del_{e['id']}"):
                            if trash_email(service, e['id']):
                                st.session_state.emails_data = [em for em in st.session_state.emails_data if em['id'] != e['id']]
                                st.success("Deleted!")
                                st.rerun()
                                
        with tab3:
            if not spam:
                st.info("No spam found.")
            else:
                st.error("These are almost certainly newsletters, promotions, or spam.")
                if st.button("🔥 PURGE ALL SPAM TO TRASH", type="primary", use_container_width=True):
                    with st.spinner("Trashing spam..."):
                        for e in spam:
                            trash_email(service, e['id'])
                            time.sleep(0.2) # API rate limit protection
                        st.session_state.emails_data = [em for em in st.session_state.emails_data if em['category'] != 'SPAM']
                        st.success("Spam purged!")
                        st.rerun()
                
                for e in spam:
                    formatted_summary = e['summary'].replace('\n', '<br>')
                    st.markdown(f"""
                    <div class="email-card">
                        <span class="badge badge-spam">SPAM</span>
                        <div class="email-subject">{e['subject']}</div>
                        <div class="sender-text">From: {e['sender']}</div>
                        <div class="summary-text">{formatted_summary}</div>
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == '__main__':
    main()
