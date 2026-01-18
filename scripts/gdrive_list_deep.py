import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SA_KEY_PATH = os.environ.get("GOOGLE_SERVICE_ACCOUNT_KEY", "")
ROOT_FOLDER_ID = "1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs"

with open(SA_KEY_PATH, 'r') as f:
    sa_key = json.load(f)

credentials = service_account.Credentials.from_service_account_info(
    sa_key, scopes=["https://www.googleapis.com/auth/drive.readonly"]
)
service = build("drive", "v3", credentials=credentials)

def list_folder(folder_id, indent=0):
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query, spaces='drive', 
        fields='files(id, name, mimeType, modifiedTime)',
        orderBy='name',
        supportsAllDrives=True, includeItemsFromAllDrives=True
    ).execute()
    files = results.get('files', [])
    
    for f in files:
        is_folder = 'folder' in f['mimeType']
        icon = 'D' if is_folder else 'F'
        prefix = "  " * indent
        print(f"{prefix}[{icon}] {f['name']}")
        if is_folder and indent < 2:  # Max 2 levels deep
            list_folder(f['id'], indent + 1)

print("=== BLAUWEISS-EDV-LLC GDrive Structure ===")
list_folder(ROOT_FOLDER_ID)
