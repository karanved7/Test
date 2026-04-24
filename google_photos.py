#!/usr/bin/env python3
import os
import json
import requests
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/photoslibrary.readonly",
    "https://www.googleapis.com/auth/photoslibrary.appendonly",
]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"
BASE_URL = "https://photoslibrary.googleapis.com/v1"


def authenticate() -> Credentials:
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def _headers(creds: Credentials) -> dict:
    return {"Authorization": f"Bearer {creds.token}"}


def list_albums(creds: Credentials) -> list[dict]:
    albums, page_token = [], None
    while True:
        params = {"pageSize": 50}
        if page_token:
            params["pageToken"] = page_token
        resp = requests.get(f"{BASE_URL}/albums", headers=_headers(creds), params=params)
        resp.raise_for_status()
        data = resp.json()
        albums.extend(data.get("albums", []))
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return albums


def list_media_items(creds: Credentials, album_id: str | None = None, page_size: int = 25) -> list[dict]:
    if album_id:
        body = {"albumId": album_id, "pageSize": page_size}
        resp = requests.post(f"{BASE_URL}/mediaItems:search", headers=_headers(creds), json=body)
    else:
        resp = requests.get(f"{BASE_URL}/mediaItems", headers=_headers(creds), params={"pageSize": page_size})
    resp.raise_for_status()
    return resp.json().get("mediaItems", [])


def upload_photo(creds: Credentials, file_path: str, album_id: str | None = None) -> dict:
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        raw = f.read()

    upload_headers = {
        **_headers(creds),
        "Content-Type": "application/octet-stream",
        "X-Goog-Upload-Content-Type": "image/jpeg",
        "X-Goog-Upload-Protocol": "raw",
    }
    token_resp = requests.post(f"{BASE_URL}/uploads", headers=upload_headers, data=raw)
    token_resp.raise_for_status()
    upload_token = token_resp.text

    body: dict = {"newMediaItems": [{"simpleMediaItem": {"fileName": filename, "uploadToken": upload_token}}]}
    if album_id:
        body["albumId"] = album_id

    create_resp = requests.post(f"{BASE_URL}/mediaItems:batchCreate", headers=_headers(creds), json=body)
    create_resp.raise_for_status()
    return create_resp.json()


def download_photo(creds: Credentials, media_item_id: str, dest_dir: str = ".") -> str:
    resp = requests.get(f"{BASE_URL}/mediaItems/{media_item_id}", headers=_headers(creds))
    resp.raise_for_status()
    item = resp.json()
    base_url = item["baseUrl"] + "=d"
    filename = item.get("filename", media_item_id)
    dest = os.path.join(dest_dir, filename)
    with requests.get(base_url, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return dest


if __name__ == "__main__":
    creds = authenticate()
    print("Authenticated. Fetching recent media items...")
    items = list_media_items(creds, page_size=10)
    for item in items:
        print(f"  {item['id']} - {item.get('filename', 'unknown')}")
