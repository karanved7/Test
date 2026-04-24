"""
Tests for google_photos.py

Run with: pytest tests/test_google_photos.py
"""
import json
import os
import pytest
from unittest.mock import MagicMock, mock_open, patch, call

import google_photos as gp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_creds(token="test-token", valid=True, expired=False, refresh_token=None):
    creds = MagicMock()
    creds.token = token
    creds.valid = valid
    creds.expired = expired
    creds.refresh_token = refresh_token
    return creds


# ---------------------------------------------------------------------------
# authenticate()
# ---------------------------------------------------------------------------

class TestAuthenticate:
    def test_returns_valid_cached_token(self, tmp_path, monkeypatch):
        """When token.json exists and credentials are valid, skip OAuth flow."""
        monkeypatch.chdir(tmp_path)
        token_file = tmp_path / "token.json"
        token_file.write_text("{}")

        creds = _make_creds(valid=True)
        with patch("google_photos.Credentials.from_authorized_user_file", return_value=creds):
            result = gp.authenticate()

        assert result is creds

    def test_refreshes_expired_token(self, tmp_path, monkeypatch):
        """When credentials exist but are expired and have a refresh_token, refresh them."""
        monkeypatch.chdir(tmp_path)
        token_file = tmp_path / "token.json"
        token_file.write_text("{}")

        creds = _make_creds(valid=False, expired=True, refresh_token="rt")
        creds.to_json.return_value = '{"refreshed": true}'

        with patch("google_photos.Credentials.from_authorized_user_file", return_value=creds), \
             patch("google_photos.Request") as mock_request:
            result = gp.authenticate()

        creds.refresh.assert_called_once_with(mock_request())
        assert (tmp_path / "token.json").read_text() == '{"refreshed": true}'
        assert result is creds

    def test_runs_oauth_flow_when_no_token_file(self, tmp_path, monkeypatch):
        """When no token.json exists, run the local OAuth server flow."""
        monkeypatch.chdir(tmp_path)

        creds = _make_creds(valid=True)
        creds.to_json.return_value = '{"new": true}'

        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = creds

        with patch("google_photos.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow):
            result = gp.authenticate()

        mock_flow.run_local_server.assert_called_once_with(port=0)
        assert (tmp_path / "token.json").read_text() == '{"new": true}'
        assert result is creds

    def test_writes_token_file_after_oauth(self, tmp_path, monkeypatch):
        """Token file is written after a successful OAuth flow."""
        monkeypatch.chdir(tmp_path)
        creds = _make_creds(valid=True)
        creds.to_json.return_value = '{"written": true}'

        mock_flow = MagicMock()
        mock_flow.run_local_server.return_value = creds

        with patch("google_photos.InstalledAppFlow.from_client_secrets_file", return_value=mock_flow):
            gp.authenticate()

        assert json.loads((tmp_path / "token.json").read_text()) == {"written": True}


# ---------------------------------------------------------------------------
# _headers()
# ---------------------------------------------------------------------------

class TestHeaders:
    def test_returns_authorization_header(self):
        creds = _make_creds(token="my-access-token")
        assert gp._headers(creds) == {"Authorization": "Bearer my-access-token"}


# ---------------------------------------------------------------------------
# list_albums()
# ---------------------------------------------------------------------------

class TestListAlbums:
    def test_single_page(self):
        creds = _make_creds()
        albums_data = [{"id": "a1", "title": "Vacation"}]

        mock_resp = MagicMock()
        mock_resp.json.return_value = {"albums": albums_data}

        with patch("google_photos.requests.get", return_value=mock_resp) as mock_get:
            result = gp.list_albums(creds)

        assert result == albums_data
        mock_get.assert_called_once()

    def test_pagination_fetches_all_pages(self):
        creds = _make_creds()
        page1 = MagicMock()
        page1.json.return_value = {"albums": [{"id": "a1"}], "nextPageToken": "tok123"}
        page2 = MagicMock()
        page2.json.return_value = {"albums": [{"id": "a2"}]}

        with patch("google_photos.requests.get", side_effect=[page1, page2]) as mock_get:
            result = gp.list_albums(creds)

        assert len(result) == 2
        assert mock_get.call_count == 2
        # Second call should include the page token
        _, kwargs = mock_get.call_args_list[1]
        assert kwargs["params"]["pageToken"] == "tok123"

    def test_empty_response_returns_empty_list(self):
        creds = _make_creds()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}

        with patch("google_photos.requests.get", return_value=mock_resp):
            result = gp.list_albums(creds)

        assert result == []

    def test_http_error_propagates(self):
        creds = _make_creds()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("403 Forbidden")

        with patch("google_photos.requests.get", return_value=mock_resp):
            with pytest.raises(Exception, match="403 Forbidden"):
                gp.list_albums(creds)


# ---------------------------------------------------------------------------
# list_media_items()
# ---------------------------------------------------------------------------

class TestListMediaItems:
    def test_without_album_id_uses_get(self):
        creds = _make_creds()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"mediaItems": [{"id": "m1"}]}

        with patch("google_photos.requests.get", return_value=mock_resp) as mock_get, \
             patch("google_photos.requests.post") as mock_post:
            result = gp.list_media_items(creds, page_size=10)

        mock_get.assert_called_once()
        mock_post.assert_not_called()
        assert result == [{"id": "m1"}]

    def test_with_album_id_uses_post(self):
        creds = _make_creds()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"mediaItems": [{"id": "m2"}]}

        with patch("google_photos.requests.post", return_value=mock_resp) as mock_post, \
             patch("google_photos.requests.get") as mock_get:
            result = gp.list_media_items(creds, album_id="album123", page_size=5)

        mock_post.assert_called_once()
        mock_get.assert_not_called()
        _, kwargs = mock_post.call_args
        assert kwargs["json"]["albumId"] == "album123"
        assert kwargs["json"]["pageSize"] == 5
        assert result == [{"id": "m2"}]

    def test_empty_response_returns_empty_list(self):
        creds = _make_creds()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}

        with patch("google_photos.requests.get", return_value=mock_resp):
            assert gp.list_media_items(creds) == []

    def test_http_error_propagates(self):
        creds = _make_creds()
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("500 Server Error")

        with patch("google_photos.requests.get", return_value=mock_resp):
            with pytest.raises(Exception, match="500 Server Error"):
                gp.list_media_items(creds)


# ---------------------------------------------------------------------------
# upload_photo()
# ---------------------------------------------------------------------------

class TestUploadPhoto:
    def _setup_mocks(self, upload_token="upload-tok-abc", create_response=None):
        if create_response is None:
            create_response = {"newMediaItemResults": [{"status": {"message": "OK"}}]}

        token_resp = MagicMock()
        token_resp.text = upload_token

        create_resp = MagicMock()
        create_resp.json.return_value = create_response

        return token_resp, create_resp

    def test_upload_without_album_id(self, tmp_path):
        creds = _make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"fake-image-data")

        token_resp, create_resp = self._setup_mocks()

        with patch("google_photos.requests.post", side_effect=[token_resp, create_resp]) as mock_post:
            result = gp.upload_photo(creds, str(photo))

        assert mock_post.call_count == 2
        # First call: raw upload
        first_call_url = mock_post.call_args_list[0][0][0]
        assert first_call_url.endswith("/uploads")
        # Second call: batch create — no albumId key
        second_call_body = mock_post.call_args_list[1][1]["json"]
        assert "albumId" not in second_call_body

    def test_upload_with_album_id(self, tmp_path):
        creds = _make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"fake-image-data")

        token_resp, create_resp = self._setup_mocks()

        with patch("google_photos.requests.post", side_effect=[token_resp, create_resp]):
            gp.upload_photo(creds, str(photo), album_id="album-xyz")

        create_call = mock_post = None
        # Re-run to capture call args cleanly
        with patch("google_photos.requests.post", side_effect=[token_resp, create_resp]) as mock_post:
            gp.upload_photo(creds, str(photo), album_id="album-xyz")

        body = mock_post.call_args_list[1][1]["json"]
        assert body["albumId"] == "album-xyz"

    def test_upload_token_http_error_propagates(self, tmp_path):
        creds = _make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"data")

        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = Exception("403 Forbidden")

        with patch("google_photos.requests.post", return_value=bad_resp):
            with pytest.raises(Exception, match="403 Forbidden"):
                gp.upload_photo(creds, str(photo))

    def test_batch_create_http_error_propagates(self, tmp_path):
        creds = _make_creds()
        photo = tmp_path / "photo.jpg"
        photo.write_bytes(b"data")

        token_resp = MagicMock()
        token_resp.text = "tok"

        bad_create = MagicMock()
        bad_create.raise_for_status.side_effect = Exception("500 Server Error")

        with patch("google_photos.requests.post", side_effect=[token_resp, bad_create]):
            with pytest.raises(Exception, match="500 Server Error"):
                gp.upload_photo(creds, str(photo))


# ---------------------------------------------------------------------------
# download_photo()
# ---------------------------------------------------------------------------

class TestDownloadPhoto:
    def test_downloads_to_dest_dir(self, tmp_path):
        creds = _make_creds()
        item_data = {"baseUrl": "https://example.com/photo", "filename": "sunset.jpg"}

        meta_resp = MagicMock()
        meta_resp.json.return_value = item_data

        chunk_resp = MagicMock()
        chunk_resp.__enter__ = lambda s: s
        chunk_resp.__exit__ = MagicMock(return_value=False)
        chunk_resp.iter_content.return_value = [b"chunk1", b"chunk2"]

        with patch("google_photos.requests.get", side_effect=[meta_resp, chunk_resp]):
            dest = gp.download_photo(creds, "media-id-123", dest_dir=str(tmp_path))

        expected = str(tmp_path / "sunset.jpg")
        assert dest == expected
        assert (tmp_path / "sunset.jpg").read_bytes() == b"chunk1chunk2"

    def test_uses_media_item_id_as_fallback_filename(self, tmp_path):
        creds = _make_creds()
        item_data = {"baseUrl": "https://example.com/photo"}  # no "filename" key

        meta_resp = MagicMock()
        meta_resp.json.return_value = item_data

        chunk_resp = MagicMock()
        chunk_resp.__enter__ = lambda s: s
        chunk_resp.__exit__ = MagicMock(return_value=False)
        chunk_resp.iter_content.return_value = [b"data"]

        with patch("google_photos.requests.get", side_effect=[meta_resp, chunk_resp]):
            dest = gp.download_photo(creds, "fallback-id", dest_dir=str(tmp_path))

        assert dest == str(tmp_path / "fallback-id")

    def test_http_error_on_metadata_propagates(self):
        creds = _make_creds()
        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = Exception("404 Not Found")

        with patch("google_photos.requests.get", return_value=bad_resp):
            with pytest.raises(Exception, match="404 Not Found"):
                gp.download_photo(creds, "media-id-404")

    def test_appends_download_param_to_base_url(self, tmp_path):
        creds = _make_creds()
        item_data = {"baseUrl": "https://example.com/base", "filename": "img.jpg"}

        meta_resp = MagicMock()
        meta_resp.json.return_value = item_data

        chunk_resp = MagicMock()
        chunk_resp.__enter__ = lambda s: s
        chunk_resp.__exit__ = MagicMock(return_value=False)
        chunk_resp.iter_content.return_value = []

        with patch("google_photos.requests.get", side_effect=[meta_resp, chunk_resp]) as mock_get:
            gp.download_photo(creds, "mid", dest_dir=str(tmp_path))

        download_url = mock_get.call_args_list[1][0][0]
        assert download_url == "https://example.com/base=d"
