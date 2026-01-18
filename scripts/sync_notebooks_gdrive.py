#!/usr/bin/env python3
"""Sync notebooks to GDrive CLARISSA/notebooks/ folder for Colab access."""

import json
import os
import glob
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
CONFIG_PATH = "config/clarissa_credentials.json"
NOTEBOOKS_DIR = "docs/tutorials"

with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

# Target: CLARISSA/notebooks/ folder
TARGET_FOLDER_ID = config['gdrive']['clarissa']['notebooks_folder_id']

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)
print(f"Service Account: {sa_key.get('client_email')}")
print(f"Target folder: CLARISSA/notebooks/ ({TARGET_FOLDER_ID})")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

notebooks = glob.glob(f"{NOTEBOOKS_DIR}/*.ipynb")
print(f"Found {len(notebooks)} notebooks")

colab_urls = {}

for nb_path in notebooks:
    nb_name = os.path.basename(nb_path)
    
    query = f"name='{nb_name}' and '{TARGET_FOLDER_ID}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    existing = results.get('files', [])
    
    media = MediaFileUpload(nb_path, mimetype='application/x-ipynb+json', resumable=True)
    
    if existing:
        file_id = existing[0]['id']
        service.files().update(fileId=file_id, media_body=media, supportsAllDrives=True).execute()
        print(f"  Updated: {nb_name}")
    else:
        file_metadata = {'name': nb_name, 'parents': [TARGET_FOLDER_ID]}
        file = service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        file_id = file.get('id')
        print(f"  Created: {nb_name}")
    
    colab_urls[nb_name] = f"https://colab.research.google.com/drive/{file_id}"

with open('notebook_colab_urls.json', 'w') as f:
    json.dump(colab_urls, f, indent=2)

print(f"\nNotebooks synced to CLARISSA/notebooks/")
for name, url in colab_urls.items():
    print(f"  {name}: {url}")
