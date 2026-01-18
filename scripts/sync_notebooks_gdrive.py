#!/usr/bin/env python3
"""Sync Jupyter notebooks to GDrive/CLARISSA/notebooks folder per ADR-017."""

import json
import os
import glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load service account
SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)
print(f"Service Account: {sa_key.get('client_email')}")

# Load config for folder IDs
CONFIG_PATH = "config/clarissa_credentials.json"
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Target: CLARISSA/notebooks folder per ADR-017
TARGET_FOLDER_ID = config['gdrive']['folders']['clarissa_notebooks']
print(f"Target: CLARISSA/notebooks ({TARGET_FOLDER_ID[:12]}...)")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

# Find notebooks
notebooks = glob.glob("docs/tutorials/*.ipynb")
print(f"Found {len(notebooks)} notebooks")

colab_urls = {}
for nb_path in notebooks:
    filename = os.path.basename(nb_path)
    
    # Check if exists
    query = f"name='{filename}' and '{TARGET_FOLDER_ID}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    existing = results.get('files', [])
    
    media = MediaFileUpload(nb_path, mimetype='application/json', resumable=True)
    
    if existing:
        file_id = existing[0]['id']
        service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
        print(f"  Updated: {filename}")
    else:
        file_metadata = {'name': filename, 'parents': [TARGET_FOLDER_ID]}
        file = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        file_id = file.get('id')
        print(f"  Created: {filename} ({file_id})")
    
    colab_urls[filename] = f"https://colab.research.google.com/drive/{file_id}"

# Save URLs
with open('notebook_colab_urls.json', 'w') as f:
    json.dump(colab_urls, f, indent=2)
print(f"Colab URLs saved to notebook_colab_urls.json")
