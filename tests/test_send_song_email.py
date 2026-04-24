import importlib
import smtplib
import sys
from unittest.mock import MagicMock, call, patch

import pytest


def _load_module(monkeypatch):
    """Import send_song_email with env vars set, reloading each time to pick up monkeypatches."""
    monkeypatch.setenv("SENDER_EMAIL", "sender@example.com")
    monkeypatch.setenv("SENDER_PASSWORD", "s3cr3t")
    if "send_song_email" in sys.modules:
        del sys.modules["send_song_email"]
    import send_song_email
    return send_song_email


# ---------------------------------------------------------------------------
# build_message
# ---------------------------------------------------------------------------

class TestBuildMessage:
    def test_subject_contains_title_and_artist(self, monkeypatch):
        m = _load_module(monkeypatch)
        msg = m.build_message("recipient@example.com")
        assert m.SONG["title"] in msg["Subject"]
        assert m.SONG["artist"] in msg["Subject"]

    def test_from_header_is_sender_email(self, monkeypatch):
        m = _load_module(monkeypatch)
        msg = m.build_message("recipient@example.com")
        assert msg["From"] == "sender@example.com"

    def test_to_header_matches_recipient(self, monkeypatch):
        m = _load_module(monkeypatch)
        msg = m.build_message("person@example.com")
        assert msg["To"] == "person@example.com"

    def test_body_contains_song_details(self, monkeypatch):
        m = _load_module(monkeypatch)
        msg = m.build_message("x@example.com")
        payload = msg.get_payload(0).get_payload()
        assert m.SONG["title"] in payload
        assert m.SONG["artist"] in payload
        assert str(m.SONG["year"]) in payload
        assert m.SONG["listen"] in payload
        assert m.SONG["why"] in payload

    def test_returns_multipart_alternative(self, monkeypatch):
        m = _load_module(monkeypatch)
        msg = m.build_message("x@example.com")
        assert msg.get_content_type() == "multipart/alternative"


# ---------------------------------------------------------------------------
# send_emails
# ---------------------------------------------------------------------------

class TestSendEmails:
    def test_starttls_called_before_login(self, monkeypatch):
        m = _load_module(monkeypatch)
        mock_server = MagicMock()
        call_order = []
        mock_server.starttls.side_effect = lambda: call_order.append("starttls")
        mock_server.login.side_effect = lambda *_: call_order.append("login")

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = lambda s: mock_server
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            m.send_emails()

        assert call_order.index("starttls") < call_order.index("login")

    def test_login_uses_env_credentials(self, monkeypatch):
        m = _load_module(monkeypatch)
        mock_server = MagicMock()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = lambda s: mock_server
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            m.send_emails()

        mock_server.login.assert_called_once_with("sender@example.com", "s3cr3t")

    def test_sendmail_called_once_per_recipient(self, monkeypatch):
        m = _load_module(monkeypatch)
        mock_server = MagicMock()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = lambda s: mock_server
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            m.send_emails()

        assert mock_server.sendmail.call_count == len(m.RECIPIENTS)

    def test_sendmail_targets_correct_recipients(self, monkeypatch):
        m = _load_module(monkeypatch)
        mock_server = MagicMock()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = lambda s: mock_server
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            m.send_emails()

        actual_recipients = [c.args[1] for c in mock_server.sendmail.call_args_list]
        assert actual_recipients == m.RECIPIENTS

    def test_sendmail_sent_from_sender_email(self, monkeypatch):
        m = _load_module(monkeypatch)
        mock_server = MagicMock()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = lambda s: mock_server
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            m.send_emails()

        for c in mock_server.sendmail.call_args_list:
            assert c.args[0] == "sender@example.com"

    def test_smtp_connects_to_office365(self, monkeypatch):
        m = _load_module(monkeypatch)
        mock_server = MagicMock()

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value.__enter__ = lambda s: mock_server
            mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
            m.send_emails()

        mock_smtp.assert_called_once_with("smtp.office365.com", 587)

    def test_missing_env_var_raises_key_error(self, monkeypatch):
        monkeypatch.delenv("SENDER_EMAIL", raising=False)
        monkeypatch.delenv("SENDER_PASSWORD", raising=False)
        if "send_song_email" in sys.modules:
            del sys.modules["send_song_email"]

        with pytest.raises(KeyError):
            import send_song_email
