#!/usr/bin/env python3
"""Sync Jupyter notebooks to GDrive/CLARISSA/notebooks folder."""

import json
import os
import glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
NOTEBOOKS_PATH = "docs/tutorials"
CONFIG_PATH = "config/clarissa_credentials.json"

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Use CLARISSA/notebooks folder if available, otherwise legacy folder
TARGET_FOLDER_ID = config.get('gdrive', {}).get('notebooks_folder_id') or "1meMlElQRVGj3dDkzt2h0SGF6jJa3HDTa"

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)

print(f"Service Account: {sa_key.get('client_email')}")
print(f"Target folder: {TARGET_FOLDER_ID}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

notebooks = glob.glob(f"{NOTEBOOKS_PATH}/*.ipynb")
colab_urls = {}

for nb_path in notebooks:
    filename = os.path.basename(nb_path)
    print(f"\nProcessing: {filename}")
    
    # Check if exists
    query = f"name='{filename}' and '{TARGET_FOLDER_ID}' in parents and trashed=false"
    results = service.files().list(
        q=query, spaces='drive', fields='files(id)',
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    existing = results.get('files', [])
    
    media = MediaFileUpload(nb_path, mimetype='application/x-ipynb+json', resumable=True)
    
    if existing:
        file_id = existing[0]['id']
        service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
        print(f"  Updated (ID: {file_id})")
    else:
        file_metadata = {'name': filename, 'parents': [TARGET_FOLDER_ID]}
        file = service.files().create(
            body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
        ).execute()
        file_id = file.get('id')
        print(f"  Created (ID: {file_id})")
    
    colab_url = f"https://colab.research.google.com/drive/{file_id}"
    colab_urls[filename] = colab_url
    print(f"  Colab: {colab_url}")

# Save URLs
with open("notebook_colab_urls.json", "w") as f:
    json.dump(colab_urls, f, indent=2)

print(f"\nSynced {len(notebooks)} notebooks to GDrive!")
