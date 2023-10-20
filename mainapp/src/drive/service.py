from __future__ import print_function

import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the token file.
SCOPES = [
    'https://www.googleapis.com/auth/drive',
]
CLIENT_SECRETS_PATH = 'mainapp/tokens/drive/client_secrets.json'
CREDS_PATH = 'mainapp/tokens/drive/creds.json'

def get_creds():
    creds = None
    # The file creds.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(CREDS_PATH):
        creds = Credentials.from_authorized_user_file(CREDS_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print('Getting Google Drive credentials')
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(CREDS_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def build_drive_service():
    return build('drive', 'v3', credentials=get_creds())