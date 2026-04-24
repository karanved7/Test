import os

# send_song_email reads SENDER_EMAIL and SENDER_PASSWORD at import time.
# These must be set before the module is imported, so we inject them here.
os.environ.setdefault("SENDER_EMAIL", "test@example.com")
os.environ.setdefault("SENDER_PASSWORD", "test-password")
