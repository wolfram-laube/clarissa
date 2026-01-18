#!/usr/bin/env python3
"""
Sync Jupyter notebooks to Google Drive for Colab access.
Creates/updates notebooks in a 'Notebooks' subfolder and generates Colab URLs.
"""

import json
import os
import sys
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
ROOT_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs")
NOTEBOOKS_FOLDER = "CLARISSA_Notebooks"

# Notebooks to sync
NOTEBOOK_PATHS = [
    "docs/tutorials/reservoir-basics-code.ipynb",
]

def main():
    print(f"Root Folder ID: {ROOT_FOLDER_ID}")
    print(f"Subfolder: {NOTEBOOKS_FOLDER}")

    with open(SA_KEY_PATH, 'r') as f:
        sa_key = json.load(f)
    print(f"Service Account: {sa_key.get('client_email')}")

    credentials = service_account.Credentials.from_service_account_info(
        sa_key, scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=credentials)

    # Find or create Notebooks subfolder
    notebooks_folder_id = find_or_create_folder(service, ROOT_FOLDER_ID, NOTEBOOKS_FOLDER)
    if not notebooks_folder_id:
        print("ERROR: Could not create notebooks folder")
        sys.exit(1)

    results = {"notebooks": [], "folder_id": notebooks_folder_id}

    for notebook_path in NOTEBOOK_PATHS:
        if not os.path.exists(notebook_path):
            print(f"  SKIP: {notebook_path} not found")
            continue

        filename = os.path.basename(notebook_path)
        file_id = upload_or_update_file(service, notebooks_folder_id, notebook_path, filename)
        
        if file_id:
            colab_url = f"https://colab.research.google.com/drive/{file_id}"
            print(f"  ✅ {filename}")
            print(f"     Colab: {colab_url}")
            results["notebooks"].append({
                "path": notebook_path,
                "filename": filename,
                "file_id": file_id,
                "colab_url": colab_url
            })

    # Write results
    with open("notebook_colab_urls.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"
📁 GDrive Folder: https://drive.google.com/drive/folders/{notebooks_folder_id}")
    print(f"
✅ Synced {len(results['notebooks'])} notebooks")

    # Generate markdown snippet for docs
    if results["notebooks"]:
        print("
--- Copy this to your documentation ---")
        for nb in results["notebooks"]:
            print(f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({nb['colab_url']})")


def find_or_create_folder(service, parent_id, folder_name):
    """Find existing folder or create new one."""
    try:
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query, spaces='drive', fields='files(id, name)',
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        folders = results.get('files', [])
        if folders:
            print(f"Found existing folder: {folder_name}")
            return folders[0]['id']
    except HttpError as e:
        print(f"Search failed: {e}")

    # Create folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    try:
        folder = service.files().create(
            body=folder_metadata, fields='id', supportsAllDrives=True
        ).execute()
        print(f"Created folder: {folder_name}")
        return folder.get('id')
    except HttpError as e:
        print(f"Failed to create folder: {e}")
        return None


def upload_or_update_file(service, folder_id, filepath, filename):
    """Upload file, updating if it already exists."""
    # Check if file exists
    try:
        query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
        results = service.files().list(
            q=query, spaces='drive', fields='files(id)',
            supportsAllDrives=True, includeItemsFromAllDrives=True
        ).execute()
        existing = results.get('files', [])
    except HttpError:
        existing = []

    media = MediaFileUpload(filepath, mimetype='application/x-ipynb+json', resumable=True)

    try:
        if existing:
            # Update existing file
            file_id = existing[0]['id']
            service.files().update(
                fileId=file_id, media_body=media, supportsAllDrives=True
            ).execute()
            return file_id
        else:
            # Create new file
            file_metadata = {'name': filename, 'parents': [folder_id]}
            file = service.files().create(
                body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
            ).execute()
            return file.get('id')
    except HttpError as e:
        print(f"  ERROR uploading {filename}: {e}")
        return None


if __name__ == "__main__":
    main()
