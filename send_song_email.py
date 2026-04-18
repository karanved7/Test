import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"  # Use a Gmail App Password

RECIPIENTS = [
    "jayshuet@gmail.com",
    "jyeshved@gmail.com",
]

SONG = {
    "title": "Bohemian Rhapsody",
    "artist": "Queen",
    "year": 1975,
    "why": (
        "A timeless rock opera blending ballad, opera, and hard rock. "
        "Unforgettable vocals, iconic guitar work, and a story that never gets old."
    ),
    "listen": "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
}


def build_message(recipient: str) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"A Great Song For You: {SONG['title']} by {SONG['artist']}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient

    body = (
        f"Hey there!\n\n"
        f"Here's a great song recommendation:\n\n"
        f"  Title:  {SONG['title']}\n"
        f"  Artist: {SONG['artist']} ({SONG['year']})\n\n"
        f"  Why you'll love it:\n"
        f"  {SONG['why']}\n\n"
        f"  Listen here: {SONG['listen']}\n\n"
        f"Enjoy!\n"
    )
    msg.attach(MIMEText(body, "plain"))
    return msg


def send_emails():
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for recipient in RECIPIENTS:
            msg = build_message(recipient)
            server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
            print(f"Sent to {recipient}")


if __name__ == "__main__":
    send_emails()
