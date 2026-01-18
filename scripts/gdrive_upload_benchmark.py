#!/usr/bin/env python3
"""Upload benchmark files to Google Drive."""

import json
import os
import sys
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
ROOT_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs")
BENCHMARK_FOLDER = os.environ.get("BENCHMARK_FOLDER_NAME", "Benchmarks")
PIPELINE_ID = os.environ.get("CI_PIPELINE_ID", "unknown")

print(f"Root Folder ID: {ROOT_FOLDER_ID}")
print(f"Subfolder: {BENCHMARK_FOLDER}")

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)
print(f"Service Account: {sa_key.get('client_email')}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

is_shared_drive = False
try:
    folder_info = service.files().get(
        fileId=ROOT_FOLDER_ID, supportsAllDrives=True, fields="id,name,driveId"
    ).execute()
    print(f"Folder found: {folder_info.get('name')}")
    if folder_info.get('driveId'):
        is_shared_drive = True
        print(f"This is a Shared Drive")
except HttpError as e:
    print(f"Could not get folder info: {e}")
    sys.exit(1)

def find_or_create_folder(parent_id, folder_name):
    try:
        query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)',
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folders = results.get('files', [])
        if folders:
            return folders[0]['id']
    except HttpError:
        pass
    folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
    try:
        folder = service.files().create(body=folder_metadata, fields='id', supportsAllDrives=True).execute()
        print(f"Created folder: {folder_name}")
        return folder.get('id')
    except HttpError as e:
        print(f"Failed to create folder: {e}")
        return None

benchmark_folder_id = find_or_create_folder(ROOT_FOLDER_ID, BENCHMARK_FOLDER) or ROOT_FOLDER_ID
timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
run_folder_name = f"benchmark_{timestamp}_pipeline_{PIPELINE_ID}"
run_folder_id = find_or_create_folder(benchmark_folder_id, run_folder_name) or benchmark_folder_id

benchmark_dir = "docs/ci/benchmarks"
if not os.path.exists(benchmark_dir):
    benchmark_dir = "."

uploaded = 0
for filename in os.listdir(benchmark_dir):
    filepath = os.path.join(benchmark_dir, filename)
    if not os.path.isfile(filepath):
        continue
    mimetypes = {'.md': 'text/markdown', '.json': 'application/json', '.png': 'image/png'}
    ext = os.path.splitext(filename)[1]
    mimetype = mimetypes.get(ext, 'application/octet-stream')
    file_metadata = {'name': filename, 'parents': [run_folder_id]}
    media = MediaFileUpload(filepath, mimetype=mimetype, resumable=True)
    try:
        service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()
        print(f"  Uploaded: {filename}")
        uploaded += 1
    except HttpError as e:
        print(f"  Failed: {filename} - {e}")

print(f"Uploaded {uploaded} files")
print(f"Folder: https://drive.google.com/drive/folders/{run_folder_id}")

summary = {"pipeline_id": PIPELINE_ID, "timestamp": timestamp, "folder_id": run_folder_id, 
           "files_uploaded": uploaded, "is_shared_drive": is_shared_drive}
with open("gdrive_upload_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
