#!/usr/bin/env python3
"""Sync CLARISSA credentials to GDrive/CLARISSA/config folder."""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
CONFIG_PATH = "config/clarissa_credentials.json"
GDRIVE_FILENAME = "clarissa_credentials.json"

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Use CLARISSA/config folder if available, otherwise root
TARGET_FOLDER_ID = config.get('gdrive', {}).get('config_folder_id') or config['gdrive']['shared_folder_id']

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)

print(f"Service Account: {sa_key.get('client_email')}")
print(f"Target folder: {TARGET_FOLDER_ID}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

# Check if file exists
query = f"name='{GDRIVE_FILENAME}' and '{TARGET_FOLDER_ID}' in parents and trashed=false"
results = service.files().list(
    q=query, spaces='drive', fields='files(id)',
    supportsAllDrives=True, includeItemsFromAllDrives=True
).execute()
existing = results.get('files', [])

media = MediaFileUpload(CONFIG_PATH, mimetype='application/json', resumable=True)

if existing:
    file_id = existing[0]['id']
    service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
    print(f"Updated: {GDRIVE_FILENAME} (ID: {file_id})")
else:
    file_metadata = {'name': GDRIVE_FILENAME, 'parents': [TARGET_FOLDER_ID]}
    file = service.files().create(
        body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
    ).execute()
    print(f"Created: {GDRIVE_FILENAME} (ID: {file.get('id')})")

print("Credentials synced to GDrive!")
