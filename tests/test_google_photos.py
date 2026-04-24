import json
import os
from unittest.mock import MagicMock, mock_open, patch, call

import pytest
import requests

import google_photos


# ---------------------------------------------------------------------------
# _headers
# ---------------------------------------------------------------------------

def test_headers_returns_bearer_token():
    creds = MagicMock()
    creds.token = "my-token"
    assert google_photos._headers(creds) == {"Authorization": "Bearer my-token"}


# ---------------------------------------------------------------------------
# authenticate
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_valid_cached_token_returned_without_refresh(self, tmp_path, monkeypatch):
        monkeypatch.setattr(google_photos, "TOKEN_FILE", str(tmp_path / "token.json"))
        (tmp_path / "token.json").write_text("{}")

        creds = MagicMock()
        creds.valid = True

        with patch("google_photos.Credentials.from_authorized_user_file", return_value=creds) as mock_load:
            result = google_photos.authenticate()

        mock_load.assert_called_once()
        assert result is creds

    def test_expired_token_with_refresh_token_calls_refresh(self, tmp_path, monkeypatch):
        monkeypatch.setattr(google_photos, "TOKEN_FILE", str(tmp_path / "token.json"))
        (tmp_path / "token.json").write_text("{}")

        creds = MagicMock()
        creds.valid = False
        creds.expired = True
        creds.refresh_token = "refresh-tok"
        creds.to_json.return_value = '{"refreshed": true}'

        with patch("google_photos.Credentials.from_authorized_user_file", return_value=creds):
            with patch("google_photos.Request") as mock_request:
                result = google_photos.authenticate()

        creds.refresh.assert_called_once_with(mock_request())
        assert result is creds

    def test_no_token_file_runs_oauth_flow(self, tmp_path, monkeypatch):
        token_path = str(tmp_path / "token.json")
        monkeypatch.setattr(google_photos, "TOKEN_FILE", token_path)
        monkeypatch.setattr(google_photos, "CREDENTIALS_FILE", str(tmp_path / "credentials.json"))

        new_creds = MagicMock()
        new_creds.valid = True
        new_creds.to_json.return_value = '{"new": true}'

        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = new_creds

        with patch("google_photos.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow):
            result = google_photos.authenticate()

        mock_flow.run_local_server.assert_called_once_with(port=0)
        assert os.path.exists(token_path)
        assert result is new_creds

    def test_token_file_written_after_new_oauth_flow(self, tmp_path, monkeypatch):
        token_path = str(tmp_path / "token.json")
        monkeypatch.setattr(google_photos, "TOKEN_FILE", token_path)
        monkeypatch.setattr(google_photos, "CREDENTIALS_FILE", str(tmp_path / "credentials.json"))

        new_creds = MagicMock()
        new_creds.valid = True
        new_creds.to_json.return_value = '{"saved": true}'

        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = new_creds

        with patch("google_photos.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow):
            google_photos.authenticate()

        assert json.loads(open(token_path).read()) == {"saved": True}


# ---------------------------------------------------------------------------
# list_albums
# ---------------------------------------------------------------------------

class TestListAlbums:
    def test_single_page(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(
            f"{google_photos.BASE_URL}/albums",
            json={"albums": [{"id": "a1"}, {"id": "a2"}]},
        )

        result = google_photos.list_albums(creds)

        assert result == [{"id": "a1"}, {"id": "a2"}]

    def test_multiple_pages_follows_next_page_token(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(
            f"{google_photos.BASE_URL}/albums",
            [
                {"json": {"albums": [{"id": "a1"}], "nextPageToken": "page2"}},
                {"json": {"albums": [{"id": "a2"}]}},
            ],
        )

        result = google_photos.list_albums(creds)

        assert [a["id"] for a in result] == ["a1", "a2"]

    def test_empty_albums_key_returns_empty_list(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(f"{google_photos.BASE_URL}/albums", json={})

        result = google_photos.list_albums(creds)

        assert result == []

    def test_http_error_propagates(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(f"{google_photos.BASE_URL}/albums", status_code=401)

        with pytest.raises(requests.HTTPError):
            google_photos.list_albums(creds)


# ---------------------------------------------------------------------------
# list_media_items
# ---------------------------------------------------------------------------

class TestListMediaItems:
    def test_without_album_id_uses_get(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(
            f"{google_photos.BASE_URL}/mediaItems",
            json={"mediaItems": [{"id": "m1"}]},
        )

        result = google_photos.list_media_items(creds)

        assert result == [{"id": "m1"}]

    def test_with_album_id_uses_post(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.post(
            f"{google_photos.BASE_URL}/mediaItems:search",
            json={"mediaItems": [{"id": "m2"}]},
        )

        result = google_photos.list_media_items(creds, album_id="album123")

        assert result == [{"id": "m2"}]

    def test_empty_media_items_returns_empty_list(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(f"{google_photos.BASE_URL}/mediaItems", json={})

        result = google_photos.list_media_items(creds)

        assert result == []

    def test_http_error_propagates(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(f"{google_photos.BASE_URL}/mediaItems", status_code=403)

        with pytest.raises(requests.HTTPError):
            google_photos.list_media_items(creds)


# ---------------------------------------------------------------------------
# upload_photo
# ---------------------------------------------------------------------------

class TestUploadPhoto:
    def _make_creds(self):
        creds = MagicMock()
        creds.token = "tok"
        return creds

    def test_upload_without_album_id(self, tmp_path, requests_mock):
        creds = self._make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"JPEG_DATA")

        requests_mock.post(f"{google_photos.BASE_URL}/uploads", text="upload-token-123")
        requests_mock.post(
            f"{google_photos.BASE_URL}/mediaItems:batchCreate",
            json={"newMediaItemResults": [{"status": {"message": "OK"}}]},
        )

        result = google_photos.upload_photo(creds, str(photo))

        assert result == {"newMediaItemResults": [{"status": {"message": "OK"}}]}
        # album_id must not appear in request body
        batch_body = requests_mock.last_request.json()
        assert "albumId" not in batch_body

    def test_upload_with_album_id_included_in_body(self, tmp_path, requests_mock):
        creds = self._make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"JPEG_DATA")

        requests_mock.post(f"{google_photos.BASE_URL}/uploads", text="upload-token-456")
        requests_mock.post(
            f"{google_photos.BASE_URL}/mediaItems:batchCreate",
            json={"newMediaItemResults": []},
        )

        google_photos.upload_photo(creds, str(photo), album_id="alb1")

        batch_body = requests_mock.last_request.json()
        assert batch_body["albumId"] == "alb1"

    def test_upload_token_passed_to_batch_create(self, tmp_path, requests_mock):
        creds = self._make_creds()
        photo = tmp_path / "shot.jpg"
        photo.write_bytes(b"DATA")

        requests_mock.post(f"{google_photos.BASE_URL}/uploads", text="the-upload-token")
        requests_mock.post(f"{google_photos.BASE_URL}/mediaItems:batchCreate", json={})

        google_photos.upload_photo(creds, str(photo))

        batch_body = requests_mock.last_request.json()
        item = batch_body["newMediaItems"][0]["simpleMediaItem"]
        assert item["uploadToken"] == "the-upload-token"
        assert item["fileName"] == "shot.jpg"

    def test_upload_http_error_on_raw_upload_propagates(self, tmp_path, requests_mock):
        creds = self._make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"DATA")
        requests_mock.post(f"{google_photos.BASE_URL}/uploads", status_code=500)

        with pytest.raises(requests.HTTPError):
            google_photos.upload_photo(creds, str(photo))


# ---------------------------------------------------------------------------
# download_photo
# ---------------------------------------------------------------------------

class TestDownloadPhoto:
    def test_appends_equals_d_to_base_url(self, tmp_path, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        media_id = "media123"

        requests_mock.get(
            f"{google_photos.BASE_URL}/mediaItems/{media_id}",
            json={"baseUrl": "https://photos.example.com/img", "filename": "pic.jpg"},
        )
        requests_mock.get("https://photos.example.com/img=d", content=b"IMAGE_BYTES")

        dest = google_photos.download_photo(creds, media_id, dest_dir=str(tmp_path))

        assert dest == str(tmp_path / "pic.jpg")
        assert (tmp_path / "pic.jpg").read_bytes() == b"IMAGE_BYTES"

    def test_falls_back_to_media_item_id_as_filename(self, tmp_path, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        media_id = "fallback-id"

        requests_mock.get(
            f"{google_photos.BASE_URL}/mediaItems/{media_id}",
            json={"baseUrl": "https://photos.example.com/img"},
        )
        requests_mock.get("https://photos.example.com/img=d", content=b"DATA")

        dest = google_photos.download_photo(creds, media_id, dest_dir=str(tmp_path))

        assert os.path.basename(dest) == media_id

    def test_http_error_on_metadata_fetch_propagates(self, requests_mock):
        creds = MagicMock()
        creds.token = "tok"
        requests_mock.get(
            f"{google_photos.BASE_URL}/mediaItems/bad-id",
            status_code=404,
        )

        with pytest.raises(requests.HTTPError):
            google_photos.download_photo(creds, "bad-id")
