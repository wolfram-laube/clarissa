#!/usr/bin/env python3
"""
Reorganize GDrive folder structure per ADR-017.
Creates folder hierarchy and moves existing files.
"""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
ROOT_FOLDER_ID = "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs"

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)

print(f"Service Account: {sa_key.get('client_email')}")

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

# Target folder structure (name -> subfolders)
STRUCTURE = {
    "Akquise": {
        "Profile": {},
        "Jobs": {
            "_neu": {},
            "matched": {
                "solo": {},
                "team_2": {},
                "team_3": {}
            },
            "abgelehnt": {}
        },
        "Bewerbungen": {
            "entwurf": {},
            "gesendet": {},
            "interview": {},
            "verhandlung": {},
            "abgeschlossen": {}
        }
    },
    "CLARISSA": {
        "config": {},
        "notebooks": {},
        "benchmarks": {}
    },
    "Buchhaltung": {
        "Rechnungen": {
            "2025": {},
            "2026": {}
        },
        "Angebote": {
            "2025": {},
            "2026": {}
        },
        "Belege": {}
    },
    "Kunden": {},
    "Personal": {
        "CVs": {}
    },
    "Vorlagen": {},
    "Archiv": {}
}

# File migrations: source name -> target folder path
MIGRATIONS = {
    "clarissa_credentials.json": "CLARISSA/config",
    "clarissa_colab_config.json": None,  # Delete (obsolete)
    "Skill-Matrix_Fullstack_Laube.docx": "Personal/CVs",
    "CLARISSA_Notebooks": "CLARISSA/notebooks",  # Rename/move contents
    "Benchmarks": "CLARISSA/benchmarks",  # Rename/move contents
    "2026": "Archiv",
    "generated": "Archiv"
}

def find_or_create_folder(name, parent_id):
    """Find folder by name in parent, or create it."""
    query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(
        q=query, spaces='drive', fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    files = results.get('files', [])
    
    if files:
        print(f"  Found: {name} ({files[0]['id'][:12]}...)")
        return files[0]['id']
    
    # Create folder
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=metadata, fields='id', supportsAllDrives=True).execute()
    print(f"  Created: {name} ({folder['id'][:12]}...)")
    return folder['id']

def create_structure(structure, parent_id, path=""):
    """Recursively create folder structure."""
    folder_ids = {}
    for name, subfolders in structure.items():
        full_path = f"{path}/{name}" if path else name
        folder_id = find_or_create_folder(name, parent_id)
        folder_ids[full_path] = folder_id
        if subfolders:
            sub_ids = create_structure(subfolders, folder_id, full_path)
            folder_ids.update(sub_ids)
    return folder_ids

def find_file(name, parent_id):
    """Find file or folder by name in parent."""
    query = f"name='{name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, spaces='drive', fields='files(id, name, mimeType)',
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    return results.get('files', [])

def move_file(file_id, old_parent_id, new_parent_id):
    """Move file to new parent."""
    service.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=old_parent_id,
        supportsAllDrives=True
    ).execute()

def move_folder_contents(source_id, target_id):
    """Move all contents from source folder to target folder."""
    query = f"'{source_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, spaces='drive', fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    
    for f in results.get('files', []):
        print(f"    Moving: {f['name']}")
        move_file(f['id'], source_id, target_id)

def delete_file(file_id):
    """Move file to trash."""
    service.files().update(fileId=file_id, body={'trashed': True}, supportsAllDrives=True).execute()

# Main execution
print("=" * 60)
print("GDrive Reorganization per ADR-017")
print("=" * 60)

print("\n1. Creating folder structure...")
folder_ids = create_structure(STRUCTURE, ROOT_FOLDER_ID)

print(f"\n2. Migrating existing files...")
for source_name, target_path in MIGRATIONS.items():
    files = find_file(source_name, ROOT_FOLDER_ID)
    if not files:
        print(f"  Skip (not found): {source_name}")
        continue
    
    f = files[0]
    is_folder = 'folder' in f['mimeType']
    
    if target_path is None:
        print(f"  Delete: {source_name}")
        delete_file(f['id'])
    elif is_folder and target_path in folder_ids:
        # Move folder contents to target
        target_id = folder_ids[target_path]
        print(f"  Merge folder: {source_name} -> {target_path}")
        move_folder_contents(f['id'], target_id)
        delete_file(f['id'])  # Delete empty source folder
    elif target_path in folder_ids:
        print(f"  Move: {source_name} -> {target_path}")
        move_file(f['id'], ROOT_FOLDER_ID, folder_ids[target_path])
    else:
        print(f"  Skip (target not found): {source_name} -> {target_path}")

print("\n3. Saving folder IDs...")
output = {
    "root": ROOT_FOLDER_ID,
    "folders": folder_ids
}
with open("gdrive_folder_ids.json", "w") as f:
    json.dump(output, f, indent=2)

print("\n" + "=" * 60)
print("Reorganization complete!")
print("=" * 60)

# Print key IDs for updating config
print("\nKey folder IDs for config/clarissa_credentials.json:")
key_folders = ["CLARISSA/config", "CLARISSA/notebooks", "CLARISSA/benchmarks", 
               "Akquise/Jobs/_neu", "Akquise/Bewerbungen/entwurf"]
for path in key_folders:
    if path in folder_ids:
        print(f"  {path}: {folder_ids[path]}")
