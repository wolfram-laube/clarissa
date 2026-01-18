#!/usr/bin/env python3
"""Upload benchmark files to Google Drive CLARISSA/benchmarks/ folder."""

import json
import os
import sys
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
CONFIG_PATH = "config/clarissa_credentials.json"
PIPELINE_ID = os.environ.get("CI_PIPELINE_ID", "unknown")

# Load target folder from config
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

BENCHMARKS_FOLDER_ID = config['gdrive']['clarissa']['benchmarks_folder_id']
print(f"Target folder: CLARISSA/benchmarks/ ({BENCHMARKS_FOLDER_ID})")

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)
print(f"Service Account: {sa_key.get('client_email')}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

# Create timestamped subfolder
timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
subfolder_name = f"benchmark_{timestamp}_pipeline_{PIPELINE_ID}"

folder_metadata = {
    'name': subfolder_name,
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': [BENCHMARKS_FOLDER_ID]
}
subfolder = service.files().create(
    body=folder_metadata, fields='id', supportsAllDrives=True
).execute()
subfolder_id = subfolder.get('id')
print(f"Created subfolder: {subfolder_name}")

# Upload benchmark files
benchmark_dir = "benchmark_results"
if not os.path.exists(benchmark_dir):
    print(f"No benchmark results directory found: {benchmark_dir}")
    sys.exit(0)

uploaded_files = []
for filename in os.listdir(benchmark_dir):
    filepath = os.path.join(benchmark_dir, filename)
    if os.path.isfile(filepath):
        file_metadata = {'name': filename, 'parents': [subfolder_id]}
        media = MediaFileUpload(filepath, resumable=True)
        file = service.files().create(
            body=file_metadata, media_body=media, fields='id', supportsAllDrives=True
        ).execute()
        print(f"  Uploaded: {filename}")
        uploaded_files.append(filename)

# Write summary
summary = {
    'timestamp': timestamp,
    'pipeline_id': PIPELINE_ID,
    'folder_id': subfolder_id,
    'folder_name': subfolder_name,
    'files': uploaded_files,
    'url': f"https://drive.google.com/drive/folders/{subfolder_id}"
}

with open('gdrive_upload_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"\nBenchmarks uploaded to: {summary['url']}")
