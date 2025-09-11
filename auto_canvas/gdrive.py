import io
import os
import time
from typing import List, Dict, Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.oauth2 import service_account
import base64

from .config import load_settings


SCOPES = ["https://www.googleapis.com/auth/drive"]


def _service():
    s = load_settings()
    keyfile = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON", "").strip()
    keyjson = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON_CONTENT", "").strip()
    keyb64 = os.getenv("GDRIVE_SERVICE_ACCOUNT_JSON_BASE64", "").strip()

    temp_path = None
    if keyfile and os.path.exists(keyfile):
        path_to_use = keyfile
    elif keyjson:
        temp_path = "/tmp/gdrive_sa.json"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(keyjson)
        path_to_use = temp_path
    elif keyb64:
        temp_path = "/tmp/gdrive_sa.json"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(base64.b64decode(keyb64))
        path_to_use = temp_path
    else:
        raise RuntimeError("GDRIVE_SERVICE_ACCOUNT_JSON not set or file missing; provide path, JSON content, or BASE64.")

    creds = service_account.Credentials.from_service_account_file(path_to_use, scopes=SCOPES)
    # Optionally impersonate user: subject=os.getenv("GDRIVE_IMPERSONATE_EMAIL")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def list_images_in_folder(folder_id: str) -> List[Dict]:
    svc = _service()
    query = f"'{folder_id}' in parents and trashed = false"
    fields = "files(id, name, mimeType, modifiedTime, size)"
    results = svc.files().list(q=query, fields=fields, pageSize=1000).execute()
    files = results.get("files", [])
    # Keep only images by mimeType
    images = [f for f in files if (f.get("mimeType", "").startswith("image/"))]
    # Sort by modifiedTime asc
    images.sort(key=lambda f: f.get("modifiedTime", ""))
    return images


def download_file(file_id: str, dest_path: str) -> None:
    svc = _service()
    request = svc.files().get_media(fileId=file_id)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()


def upload_file(filepath: str, folder_id: str, mime_type: str = "application/pdf") -> str:
    svc = _service()
    file_metadata = {"name": os.path.basename(filepath), "parents": [folder_id]}
    media = MediaFileUpload(filepath, mimetype=mime_type)
    file = svc.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return file.get("id")


