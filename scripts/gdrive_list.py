#!/usr/bin/env python3
"""List Google Drive folder contents."""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs")

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)
print(f"Service Account: {sa_key.get('client_email')}")
print(f"Folder ID: {FOLDER_ID}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
service = build("drive", "v3", credentials=credentials)

try:
    folder_info = service.files().get(
        fileId=FOLDER_ID, supportsAllDrives=True, fields="id,name,driveId,mimeType"
    ).execute()
    print(f"Folder: {folder_info.get('name')}")
    if folder_info.get('driveId'):
        print(f"Shared Drive ID: {folder_info.get('driveId')}")
except HttpError as e:
    print(f"Could not get folder info: {e}")

files = []
try:
    query = f"'{FOLDER_ID}' in parents and trashed=false"
    results = service.files().list(
        q=query, spaces='drive', fields='files(id, name, mimeType, modifiedTime)',
        orderBy='modifiedTime desc', pageSize=50,
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    files = results.get('files', [])
    print(f"Found {len(files)} items:")
    for f in files:
        icon = 'D' if f['mimeType'] == 'application/vnd.google-apps.folder' else 'F'
        print(f"  [{icon}] {f['name']}")
except HttpError as e:
    print(f"Error listing files: {e}")

with open("gdrive_listing.json", "w") as out:
    json.dump(files, out, indent=2)
