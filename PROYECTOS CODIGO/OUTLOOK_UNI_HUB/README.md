# Outlook University Hub

A local Python tool to automatically organize university files from your Outlook inbox. It authenticates with Microsoft Graph, scans your inbox for specific attachments (`.pdf`, `.docx`, `.xlsx`), determines the relevant subject/class based on the email content, and downloads them into organized local folders.

## Setup Instructions

### 1. Azure App Registration (Getting Client ID and Secret)

To use the Microsoft Graph API, you need to register an application in the Azure Portal:
1. Go to the [Azure Portal](https://portal.azure.com/) and sign in with your Microsoft account.
2. Navigate to **Microsoft Entra ID** (formerly Azure Active Directory) -> **App registrations**.
3. Click **New registration**.
   - **Name**: `Outlook University Hub` (or anything you prefer).
   - **Supported account types**: Select "Accounts in any organizational directory and personal Microsoft accounts".
   - **Redirect URI**: Select `Web` and enter `https://login.microsoftonline.com/common/oauth2/nativeclient` (the O365 library default redirect URI).
   - Click **Register**.
4. Once registered, copy the **Application (client) ID** from the Overview page.
5. Go to **Certificates & secrets** -> **New client secret**.
   - Give it a description and set an expiration.
   - Click **Add**.
   - **Copy the secret Value immediately** (you won't be able to see it again).

### 2. Environment Variables

Create a `.env` file in the root directory of this project with the following content:
```env
AZURE_CLIENT_ID=your_client_id_here
AZURE_CLIENT_SECRET=your_client_secret_here
# Optional: GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Installation

Install the required Python packages:
```bash
pip install -r requirements.txt
```

### 4. Running the Tool

Execute the script:
```bash
python hub.py
```

On the first run, the script will provide a link to authenticate. Open the link in your browser, sign in, grant the required permissions, and paste the resulting URL back into the terminal. The authentication token will be saved locally (`o365_token.txt`) for future runs.
