#!/usr/bin/env python3
"""
Reorganize BLAUWEISS-EDV-LLC GDrive folder structure.

Target structure:
BLAUWEISS-EDV-LLC/
├── Akquise/
│   ├── Profile/
│   ├── Jobs/
│   │   ├── _neu/
│   │   ├── matched/
│   │   └── abgelehnt/
│   ├── Bewerbungen/
│   │   ├── entwurf/
│   │   ├── gesendet/
│   │   ├── interview/
│   │   ├── verhandlung/
│   │   └── abgeschlossen/
│   └── _tracking.json
├── CLARISSA/
│   ├── config/
│   ├── notebooks/
│   └── benchmarks/
├── Buchhaltung/
│   ├── Rechnungen/
│   ├── Angebote/
│   └── Belege/
├── Kunden/
├── Personal/
│   └── CVs/
├── Vorlagen/
└── Archiv/
"""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
ROOT_FOLDER_ID = "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs"

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive"]
)
service = build("drive", "v3", credentials=credentials)

def find_or_create_folder(name, parent_id):
    """Find existing folder or create new one."""
    query = f"name='{name}' and '{parent_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = results.get('files', [])
    
    if files:
        print(f"  Found: {name} ({files[0]['id'][:8]}...)")
        return files[0]['id']
    
    # Create folder
    metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_id]
    }
    folder = service.files().create(body=metadata, fields='id', supportsAllDrives=True).execute()
    print(f"  Created: {name} ({folder['id'][:8]}...)")
    return folder['id']

def move_file(file_id, new_parent_id, file_name=""):
    """Move file to new parent folder."""
    # Get current parents
    file = service.files().get(fileId=file_id, fields='parents', supportsAllDrives=True).execute()
    previous_parents = ",".join(file.get('parents', []))
    
    # Move to new parent
    service.files().update(
        fileId=file_id,
        addParents=new_parent_id,
        removeParents=previous_parents,
        fields='id, parents',
        supportsAllDrives=True
    ).execute()
    print(f"  Moved: {file_name} -> new location")

def find_file(name, parent_id):
    """Find file by name in parent folder."""
    query = f"name='{name}' and '{parent_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

def delete_file(file_id, name=""):
    """Move file to trash."""
    service.files().update(fileId=file_id, body={'trashed': True}, supportsAllDrives=True).execute()
    print(f"  Trashed: {name}")

# ============================================================
# MAIN REORGANIZATION
# ============================================================

print("=" * 60)
print("GDrive Reorganization: BLAUWEISS-EDV-LLC")
print("=" * 60)

# 1. Create main folder structure
print("\n[1/6] Creating folder structure...")
folders = {}

# Top-level folders
for name in ['Akquise', 'CLARISSA', 'Buchhaltung', 'Kunden', 'Personal', 'Vorlagen', 'Archiv']:
    folders[name] = find_or_create_folder(name, ROOT_FOLDER_ID)

# Akquise subfolders
folders['Akquise/Profile'] = find_or_create_folder('Profile', folders['Akquise'])
folders['Akquise/Jobs'] = find_or_create_folder('Jobs', folders['Akquise'])
folders['Akquise/Jobs/_neu'] = find_or_create_folder('_neu', folders['Akquise/Jobs'])
folders['Akquise/Jobs/matched'] = find_or_create_folder('matched', folders['Akquise/Jobs'])
folders['Akquise/Jobs/abgelehnt'] = find_or_create_folder('abgelehnt', folders['Akquise/Jobs'])
folders['Akquise/Bewerbungen'] = find_or_create_folder('Bewerbungen', folders['Akquise'])
for stage in ['entwurf', 'gesendet', 'interview', 'verhandlung', 'abgeschlossen']:
    folders[f'Akquise/Bewerbungen/{stage}'] = find_or_create_folder(stage, folders['Akquise/Bewerbungen'])

# CLARISSA subfolders
folders['CLARISSA/config'] = find_or_create_folder('config', folders['CLARISSA'])
folders['CLARISSA/notebooks'] = find_or_create_folder('notebooks', folders['CLARISSA'])
folders['CLARISSA/benchmarks'] = find_or_create_folder('benchmarks', folders['CLARISSA'])

# Buchhaltung subfolders
for name in ['Rechnungen', 'Angebote', 'Belege']:
    folders[f'Buchhaltung/{name}'] = find_or_create_folder(name, folders['Buchhaltung'])

# Personal subfolders
folders['Personal/CVs'] = find_or_create_folder('CVs', folders['Personal'])

# 2. Move existing files
print("\n[2/6] Moving existing files...")

# Move clarissa_credentials.json to CLARISSA/config/
creds_file = find_file('clarissa_credentials.json', ROOT_FOLDER_ID)
if creds_file:
    move_file(creds_file, folders['CLARISSA/config'], 'clarissa_credentials.json')

# Move notebooks from CLARISSA_Notebooks to CLARISSA/notebooks/
old_notebooks = find_file('CLARISSA_Notebooks', ROOT_FOLDER_ID)
if old_notebooks:
    # List files in old folder and move them
    query = f"'{old_notebooks}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    for f in results.get('files', []):
        move_file(f['id'], folders['CLARISSA/notebooks'], f['name'])

# Move Benchmarks content to CLARISSA/benchmarks/
old_benchmarks = find_file('Benchmarks', ROOT_FOLDER_ID)
if old_benchmarks:
    query = f"'{old_benchmarks}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    for f in results.get('files', []):
        move_file(f['id'], folders['CLARISSA/benchmarks'], f['name'])

# Move Skill-Matrix to Personal/CVs/
skill_matrix = find_file('Skill-Matrix_Fullstack_Laube.docx', ROOT_FOLDER_ID)
if skill_matrix:
    move_file(skill_matrix, folders['Personal/CVs'], 'Skill-Matrix_Fullstack_Laube.docx')

# Move 2026, generated to Archiv/
for old_folder in ['2026', 'generated']:
    old_id = find_file(old_folder, ROOT_FOLDER_ID)
    if old_id:
        move_file(old_id, folders['Archiv'], old_folder)

# 3. Cleanup old/obsolete items
print("\n[3/6] Cleaning up obsolete items...")

# Delete old config file
old_config = find_file('clarissa_colab_config.json', ROOT_FOLDER_ID)
if old_config:
    delete_file(old_config, 'clarissa_colab_config.json')

# Delete empty old folders
for old_folder in ['CLARISSA_Notebooks', 'Benchmarks']:
    old_id = find_file(old_folder, ROOT_FOLDER_ID)
    if old_id:
        # Check if empty
        query = f"'{old_id}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id)',
            supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        if not results.get('files', []):
            delete_file(old_id, old_folder)
        else:
            print(f"  Skipped: {old_folder} (not empty)")

# 4. Output new folder IDs for config update
print("\n[4/6] New folder IDs for config...")
important_ids = {
    'root': ROOT_FOLDER_ID,
    'clarissa': folders['CLARISSA'],
    'clarissa_config': folders['CLARISSA/config'],
    'clarissa_notebooks': folders['CLARISSA/notebooks'],
    'clarissa_benchmarks': folders['CLARISSA/benchmarks'],
    'akquise': folders['Akquise'],
    'akquise_jobs_neu': folders['Akquise/Jobs/_neu'],
    'akquise_bewerbungen_entwurf': folders['Akquise/Bewerbungen/entwurf'],
}

for name, fid in important_ids.items():
    print(f"  {name}: {fid}")

# Save to JSON for CI to pick up
with open('gdrive_folder_ids.json', 'w') as f:
    json.dump(important_ids, f, indent=2)

print("\n[5/6] Verifying final structure...")
def list_folder(folder_id, indent=0):
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', 
        fields='files(id, name, mimeType)', orderBy='name',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    for f in results.get('files', []):
        is_folder = 'folder' in f['mimeType']
        icon = '📁' if is_folder else '📄'
        print(f"{'  ' * indent}{icon} {f['name']}")
        if is_folder and indent < 2:
            list_folder(f['id'], indent + 1)

list_folder(ROOT_FOLDER_ID)

print("\n[6/6] Done!")
print("=" * 60)
