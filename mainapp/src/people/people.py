from __future__ import print_function

import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/contacts']
CLIENT_SECRETS_PATH = 'mainapp/tokens/people/client_secrets.json'
CREDS_PATH = 'mainapp/tokens/people/creds.json'

def get_creds():
    creds = None
    # The file creds.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(CREDS_PATH):
        creds = Credentials.from_authorized_user_file(CREDS_PATH, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        print('Getting Google Contacts credentials')
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(CREDS_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def _upload_to_google_contacts(name, phone):
    service = build('people', 'v1', credentials=get_creds())
    return service.people().createContact(body={'names': [{'givenName': name}], 'phoneNumbers': [{'value': phone}]}).execute()

def upload_contact(name, phone):
    try:
        return _upload_to_google_contacts(name, phone)
    except Exception as first_err:
        print('Google contact upload failed, attempting again', first_err, sep='\n')
        try:
            os.remove(CREDS_PATH)
            return _upload_to_google_contacts(name, phone)
        except Exception as second_err:
            print('Could not upload contact', second_err, sep='\n')
            raise second_err

def _remove_from_google_contacts(resource_name):
    service = build('people', 'v1', credentials=get_creds())
    service.people().deleteContact(resourceName=f'people/{resource_name}').execute()

def remove_contact(resource_name):
    try:
        _remove_from_google_contacts(resource_name)
    except Exception as first_err:
        print('Google contact removal failed, attempting again', first_err, sep='\n')
        try:
            os.remove(CREDS_PATH)
            _remove_from_google_contacts(resource_name)
        except Exception as second_err:
            print('Could not remove contact', second_err, sep='\n')
            raise second_err

def _update_google_contact(resource_name, name, phone):
    service = build('people', 'v1', credentials=get_creds())
    person = service.people().get(
        resourceName=f'people/{resource_name}',
        personFields='names,phoneNumbers',
    ).execute()
    return service.people().updateContact(
        resourceName=f'people/{resource_name}',
        updatePersonFields='names,phoneNumbers',
        body={'etag': person['etag'], 'names': [{'givenName': name}], 'phoneNumbers': [{'value': phone}]}
    ).execute()

def update_contact(resource_name, name, phone):
    try:
        return _update_google_contact(resource_name, name, phone)
    except Exception as first_err:
        print('Google contact update failed, attempting again', first_err, sep='\n')
        try:
            os.remove(CREDS_PATH)
            return _update_google_contact(resource_name, name, phone)
        except Exception as second_err:
            print('Could not update contact', second_err, sep='\n')
            raise second_err