#!/usr/bin/env python3
"""Sync Colab config to GDrive for automatic credential loading."""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
ROOT_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs")
CONFIG_FILENAME = "clarissa_colab_config.json"
CONFIG_PATH = "config/clarissa_colab_config.json"

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)
print(f"Service Account: {sa_key.get('client_email')}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

# Check if file exists
query = f"name='{CONFIG_FILENAME}' and '{ROOT_FOLDER_ID}' in parents and trashed=false"
results = service.files().list(q=query, spaces='drive', fields='files(id)',
    supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
existing = results.get('files', [])

if not os.path.exists(CONFIG_PATH):
    print(f"ERROR: {CONFIG_PATH} not found")
    exit(1)

media = MediaFileUpload(CONFIG_PATH, mimetype='application/json', resumable=True)

if existing:
    file_id = existing[0]['id']
    service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
    print(f"Updated: {CONFIG_FILENAME} (ID: {file_id})")
else:
    file_metadata = {'name': CONFIG_FILENAME, 'parents': [ROOT_FOLDER_ID]}
    file = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
    print(f"Created: {CONFIG_FILENAME} (ID: {file.get('id')})")

print(f"Config synced to GDrive!")
