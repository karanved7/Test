import os
import pytest


@pytest.fixture(autouse=False)
def smtp_env(monkeypatch):
    """Provide required env vars for send_song_email module."""
    monkeypatch.setenv("SENDER_EMAIL", "test@example.com")
    monkeypatch.setenv("SENDER_PASSWORD", "secret")
