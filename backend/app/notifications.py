from __future__ import annotations

import smtplib
from email.message import EmailMessage
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.config import settings


def send_email(to_email: str, subject: str, text: str) -> bool:
    """Send email through SMTP_URL. Raises only for malformed configuration; delivery failures return False."""
    if not settings.smtp_url:
        return False
    parsed = urlparse(settings.smtp_url)
    if parsed.scheme not in {"smtp", "smtps"} or not parsed.hostname:
        raise ValueError("SMTP_URL must use smtp:// or smtps://")
    port = parsed.port or (465 if parsed.scheme == "smtps" else 587)
    username = unquote(parsed.username or "")
    password = unquote(parsed.password or "")
    query = parse_qs(parsed.query)
    use_starttls = query.get("starttls", ["true"])[0].lower() in {"1", "true", "yes"}

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(text)
    try:
        client_cls = smtplib.SMTP_SSL if parsed.scheme == "smtps" else smtplib.SMTP
        with client_cls(parsed.hostname, port, timeout=10) as client:
            if parsed.scheme == "smtp" and use_starttls:
                client.starttls()
            if username:
                client.login(username, password)
            client.send_message(message)
        return True
    except (OSError, smtplib.SMTPException):
        return False


def send_sms(to_number: str, body: str) -> bool:
    if not (settings.twilio_account_sid and settings.twilio_auth_token and settings.twilio_from_number):
        return False
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
    try:
        response = httpx.post(
            url,
            data={"To": to_number, "From": settings.twilio_from_number, "Body": body},
            auth=(settings.twilio_account_sid, settings.twilio_auth_token),
            timeout=10,
        )
        return 200 <= response.status_code < 300
    except httpx.HTTPError:
        return False
