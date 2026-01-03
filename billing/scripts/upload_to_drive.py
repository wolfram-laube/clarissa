#!/usr/bin/env python3
"""
CLARISSA Google Drive Uploader

Uploads invoices and timesheets to Google Drive.

Usage:
    python upload_to_drive.py invoice.pdf timesheet.pdf
    python upload_to_drive.py --folder "2026/01_nemensis" invoice.pdf
    
Environment:
    GOOGLE_SERVICE_ACCOUNT_KEY: Path to service account JSON file
    GOOGLE_DRIVE_FOLDER_ID: Root folder ID for uploads
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
except ImportError:
    print("❌ Google API libraries not installed")
    print("   pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)


# Scopes required for Drive upload
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def get_credentials():
    """Get credentials from service account key."""
    key_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_KEY')
    
    if not key_path:
        print("❌ GOOGLE_SERVICE_ACCOUNT_KEY not set")
        sys.exit(1)
    
    # GitLab CI provides file variables as file paths
    if os.path.isfile(key_path):
        return service_account.Credentials.from_service_account_file(key_path, scopes=SCOPES)
    else:
        # Maybe it's the JSON content directly
        try:
            key_data = json.loads(key_path)
            return service_account.Credentials.from_service_account_info(key_data, scopes=SCOPES)
        except json.JSONDecodeError:
            print(f"❌ Invalid service account key: {key_path[:50]}...")
            sys.exit(1)


def get_or_create_folder(service, parent_id: str, folder_name: str) -> str:
    """Get existing folder or create new one."""
    # Search for existing folder
    query = f"name='{folder_name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    
    if files:
        return files[0]['id']
    
    # Create new folder
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    print(f"📁 Created folder: {folder_name}")
    return folder['id']


def ensure_folder_path(service, root_id: str, path: str) -> str:
    """Create nested folder structure and return final folder ID."""
    current_id = root_id
    
    for folder_name in path.split('/'):
        if folder_name:
            current_id = get_or_create_folder(service, current_id, folder_name)
    
    return current_id


def upload_file(service, folder_id: str, file_path: Path) -> dict:
    """Upload a file to Google Drive."""
    file_name = file_path.name
    
    # Determine MIME type
    mime_types = {
        '.pdf': 'application/pdf',
        '.typ': 'text/plain',
        '.json': 'application/json',
    }
    mime_type = mime_types.get(file_path.suffix, 'application/octet-stream')
    
    # Check if file already exists
    query = f"name='{file_name}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    existing = results.get('files', [])
    
    media = MediaFileUpload(str(file_path), mimetype=mime_type)
    
    if existing:
        # Update existing file
        file = service.files().update(
            fileId=existing[0]['id'],
            media_body=media
        ).execute()
        print(f"🔄 Updated: {file_name}")
    else:
        # Create new file
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        print(f"✅ Uploaded: {file_name}")
    
    return file


def main():
    parser = argparse.ArgumentParser(description="Upload billing documents to Google Drive")
    parser.add_argument("files", nargs="+", help="Files to upload")
    parser.add_argument("--folder", "-f", default="", help="Subfolder path (e.g., '2026/01_nemensis')")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be uploaded")
    
    args = parser.parse_args()
    
    # Get root folder ID
    root_folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
    if not root_folder_id:
        print("❌ GOOGLE_DRIVE_FOLDER_ID not set")
        sys.exit(1)
    
    # Validate files
    files_to_upload = []
    for f in args.files:
        path = Path(f)
        if path.exists():
            files_to_upload.append(path)
        else:
            print(f"⚠️ File not found: {f}")
    
    if not files_to_upload:
        print("❌ No files to upload")
        sys.exit(1)
    
    print(f"📤 Uploading {len(files_to_upload)} file(s)...")
    if args.folder:
        print(f"📁 Target folder: {args.folder}")
    
    if args.dry_run:
        for f in files_to_upload:
            print(f"   Would upload: {f.name}")
        print("\n⚠️ Dry run - no files uploaded")
        return
    
    # Connect to Drive
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)
    
    # Create folder structure if needed
    target_folder_id = root_folder_id
    if args.folder:
        target_folder_id = ensure_folder_path(service, root_folder_id, args.folder)
    
    # Upload files
    for file_path in files_to_upload:
        try:
            upload_file(service, target_folder_id, file_path)
        except Exception as e:
            print(f"❌ Failed to upload {file_path.name}: {e}")
    
    print(f"\n✅ Done! View at: https://drive.google.com/drive/folders/{target_folder_id}")


if __name__ == "__main__":
    main()
