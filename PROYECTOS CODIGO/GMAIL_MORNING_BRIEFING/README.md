# 🌅 Morning Gmail Briefing

An AI-powered local Web Dashboard built with Streamlit to fetch, summarize, and triage your morning emails using the Gmail API and Google Gemini.

## Features
- **Smart Summarization**: Uses Gemini 1.5 Flash to summarize long emails into 3 concise bullet points.
- **Categorization**: Automatically sorts emails into "Important", "Spam/Newsletters", and a "Quarantine Zone".
- **Quarantine Zone**: A safe space for emails Gemini isn't 90% sure about deleting. You can review and manually archive/delete them right from the dashboard.
- **Giant Purge Button**: One click to send all definite spam/newsletters straight to the trash!
- **Premium Animated UI**: Modern gradient backgrounds, glassmorphism cards, beautiful badges, and smooth hover animations.

## Setup Instructions

### 1. Prerequisites
- Python 3.8+ installed.
- A Google Cloud account.
- A Google Gemini API key.

### 2. Install Dependencies
Run the following command in your terminal:
```bash
pip install -r requirements.txt
```

### 3. Get Google Cloud Credentials (`credentials.json`)
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new Project (or select an existing one).
3. Go to **APIs & Services > Library** and search for the **Gmail API**. Click **Enable**.
4. Go to **APIs & Services > OAuth consent screen**:
   - Choose **External** (or Internal if you have Google Workspace) and fill out the required fields.
   - Under "Test Users", add your own email address.
5. Go to **APIs & Services > Credentials**:
   - Click **Create Credentials** > **OAuth client ID**.
   - Application type: **Desktop app**.
   - Give it a name and click **Create**.
   - Download the JSON file and rename it to `credentials.json`.
   - Place `credentials.json` in the root folder of this project.

### 4. Setup Gemini API Key
1. Get an API key from [Google AI Studio](https://aistudio.google.com/).
2. Duplicate the `.env.example` file and rename it to `.env` (or create a new `.env` file).
3. Add your key to the `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Run the Application
Start the Streamlit dashboard:
```bash
streamlit run app.py
```
*Note: The first time you run it, a browser window will open asking you to log in to your Google Account and authorize the app to modify your Gmail. This will generate a `token.json` file for future sessions without prompting you again.*
