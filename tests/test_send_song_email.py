"""
Tests for send_song_email.py

Run with: pytest tests/test_send_song_email.py

NOTE: send_song_email reads SENDER_EMAIL and SENDER_PASSWORD at module import
time via os.environ[]. The conftest.py sets these before the import so tests
can run. The recommended fix is to move those reads inside send_emails() so
the module is safely importable and the values can be patched per-test.
"""
import smtplib
import pytest
from unittest.mock import MagicMock, patch, call

import send_song_email as sse


SENDER = "test@example.com"
PASSWORD = "test-password"


# ---------------------------------------------------------------------------
# build_message()
# ---------------------------------------------------------------------------

class TestBuildMessage:
    def test_recipient_set_in_to_header(self):
        msg = sse.build_message("alice@example.com")
        assert msg["To"] == "alice@example.com"

    def test_from_header_matches_sender_email(self):
        msg = sse.build_message("alice@example.com")
        assert msg["From"] == sse.SENDER_EMAIL

    def test_subject_contains_song_title_and_artist(self):
        msg = sse.build_message("alice@example.com")
        assert sse.SONG["title"] in msg["Subject"]
        assert sse.SONG["artist"] in msg["Subject"]

    def test_body_contains_all_song_fields(self):
        msg = sse.build_message("alice@example.com")
        # Extract the plain-text payload
        body = msg.get_payload(0).get_payload()
        assert sse.SONG["title"] in body
        assert sse.SONG["artist"] in body
        assert str(sse.SONG["year"]) in body
        assert sse.SONG["why"] in body
        assert sse.SONG["listen"] in body

    def test_different_recipients_produce_different_to_headers(self):
        msg_a = sse.build_message("alice@example.com")
        msg_b = sse.build_message("bob@example.com")
        assert msg_a["To"] == "alice@example.com"
        assert msg_b["To"] == "bob@example.com"

    def test_message_is_multipart_alternative(self):
        msg = sse.build_message("alice@example.com")
        assert msg.get_content_subtype() == "alternative"


# ---------------------------------------------------------------------------
# send_emails()
# ---------------------------------------------------------------------------

class TestSendEmails:
    def _mock_server(self):
        server = MagicMock()
        server.__enter__ = MagicMock(return_value=server)
        server.__exit__ = MagicMock(return_value=False)
        return server

    def test_connects_to_office365_on_port_587(self):
        server = self._mock_server()
        with patch("smtplib.SMTP", return_value=server) as mock_smtp:
            sse.send_emails()
        mock_smtp.assert_called_once_with("smtp.office365.com", 587)

    def test_starts_tls(self):
        server = self._mock_server()
        with patch("smtplib.SMTP", return_value=server):
            sse.send_emails()
        server.starttls.assert_called_once()

    def test_logs_in_with_sender_credentials(self):
        server = self._mock_server()
        with patch("smtplib.SMTP", return_value=server):
            sse.send_emails()
        server.login.assert_called_once_with(sse.SENDER_EMAIL, sse.SENDER_PASSWORD)

    def test_sends_to_every_recipient(self):
        server = self._mock_server()
        with patch("smtplib.SMTP", return_value=server):
            sse.send_emails()

        assert server.sendmail.call_count == len(sse.RECIPIENTS)
        called_recipients = [c[0][1] for c in server.sendmail.call_args_list]
        assert set(called_recipients) == set(sse.RECIPIENTS)

    def test_sendmail_from_address_is_sender(self):
        server = self._mock_server()
        with patch("smtplib.SMTP", return_value=server):
            sse.send_emails()

        for smtp_call in server.sendmail.call_args_list:
            from_addr = smtp_call[0][0]
            assert from_addr == sse.SENDER_EMAIL

    def test_smtp_login_failure_raises(self):
        server = self._mock_server()
        server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"auth failed")

        with patch("smtplib.SMTP", return_value=server):
            with pytest.raises(smtplib.SMTPAuthenticationError):
                sse.send_emails()

    def test_smtp_send_failure_raises(self):
        server = self._mock_server()
        server.sendmail.side_effect = smtplib.SMTPException("send failed")

        with patch("smtplib.SMTP", return_value=server):
            with pytest.raises(smtplib.SMTPException):
                sse.send_emails()


# ---------------------------------------------------------------------------
# Env var handling
# NOTE: These tests document a known design flaw. The fix is to move
# os.environ reads inside send_emails() instead of at module level.
# ---------------------------------------------------------------------------

class TestEnvVarHandling:
    def test_missing_sender_email_raises_on_import(self, monkeypatch):
        """
        KNOWN ISSUE: Because SENDER_EMAIL is read at module level, a missing
        var raises KeyError at import time, not at call time. This makes the
        module impossible to import safely in any environment without those
        vars set.

        Recommended fix:
            def send_emails():
                sender = os.environ["SENDER_EMAIL"]
                password = os.environ["SENDER_PASSWORD"]
                ...
        """
        pytest.skip(
            "Documenting design issue: env vars are read at module level. "
            "Refactor send_song_email.py to read them inside send_emails()."
        )
