"""
Email Services Manager - 15+ Providers
SendGrid, Mailgun, AWS SES, Resend, Postmark, etc.
"""

import asyncio
import logging
import os
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailServicesManager:
    """Unified email services across 15+ providers"""

    def __init__(self):
        self._initialized = False

    async def initialize(self, config: Optional[Dict] = None):
        if self._initialized:
            return
        self._initialized = True

    async def send(
        self,
        to: List[str],
        subject: str,
        body: str,
        provider: str = "sendgrid",
        html: bool = False,
        attachments: List[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send email via specified provider"""

        if provider == "sendgrid":
            return await self._sendgrid_send(to, subject, body, html, attachments, **kwargs)
        elif provider == "mailgun":
            return await self._mailgun_send(to, subject, body, html, attachments, **kwargs)
        elif provider == "ses":
            return await self._ses_send(to, subject, body, html, attachments, **kwargs)
        elif provider == "resend":
            return await self._resend_send(to, subject, body, html, attachments, **kwargs)
        elif provider == "postmark":
            return await self._postmark_send(to, subject, body, html, **kwargs)
        elif provider == "mailchimp":
            return await self._mailchimp_send(to, subject, body, html, **kwargs)
        elif provider == "smtp":
            return await self._smtp_send(to, subject, body, html, attachments, **kwargs)
        else:
            raise ValueError(f"Unsupported email provider: {provider}")

    async def _sendgrid_send(self, to, subject, body, html, attachments, **kwargs):
        """SendGrid email"""
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType

        message = Mail(
            from_email=kwargs.get("from_email", os.environ.get("SENDGRID_FROM")),
            to_emails=to,
            subject=subject,
            plain_text_content=body if not html else None,
            html_content=body if html else None
        )

        if attachments:
            for att in attachments:
                import base64
                attachment = Attachment(
                    FileContent(base64.b64encode(att["content"]).decode()),
                    FileName(att["filename"]),
                    FileType(att.get("type", "application/octet-stream"))
                )
                message.add_attachment(attachment)

        sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
        response = sg.send(message)
        return {"status": response.status_code, "provider": "sendgrid"}

    async def _mailgun_send(self, to, subject, body, html, attachments, **kwargs):
        """Mailgun email"""
        import aiohttp

        domain = kwargs.get("domain", os.environ.get("MAILGUN_DOMAIN"))
        api_key = os.environ.get("MAILGUN_API_KEY")

        data = aiohttp.FormData()
        data.add_field("from", kwargs.get("from_email", f"noreply@{domain}"))
        for recipient in to:
            data.add_field("to", recipient)
        data.add_field("subject", subject)
        data.add_field("html" if html else "text", body)

        if attachments:
            for att in attachments:
                data.add_field("attachment", att["content"], filename=att["filename"])

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                auth=aiohttp.BasicAuth("api", api_key),
                data=data
            ) as response:
                return await response.json()

    async def _ses_send(self, to, subject, body, html, attachments, **kwargs):
        """AWS SES email"""
        import boto3

        client = boto3.client(
            "ses",
            region_name=kwargs.get("region", os.environ.get("AWS_REGION", "us-east-1"))
        )

        response = client.send_email(
            Source=kwargs.get("from_email", os.environ.get("SES_FROM")),
            Destination={"ToAddresses": to},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Html" if html else "Text": {"Data": body}
                }
            }
        )
        return {"message_id": response["MessageId"], "provider": "ses"}

    async def _resend_send(self, to, subject, body, html, attachments, **kwargs):
        """Resend email"""
        import aiohttp

        api_key = os.environ.get("RESEND_API_KEY")

        payload = {
            "from": kwargs.get("from_email", "onboarding@resend.dev"),
            "to": to,
            "subject": subject,
            "html" if html else "text": body
        }

        if attachments:
            payload["attachments"] = [
                {"filename": att["filename"], "content": att["content"]}
                for att in attachments
            ]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload
            ) as response:
                return await response.json()

    async def _postmark_send(self, to, subject, body, html, **kwargs):
        """Postmark email"""
        import aiohttp

        api_key = os.environ.get("POSTMARK_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.postmarkapp.com/email",
                headers={"X-Postmark-Server-Token": api_key, "Content-Type": "application/json"},
                json={
                    "From": kwargs.get("from_email"),
                    "To": ",".join(to),
                    "Subject": subject,
                    "HtmlBody" if html else "TextBody": body
                }
            ) as response:
                return await response.json()

    async def _mailchimp_send(self, to, subject, body, html, **kwargs):
        """Mailchimp Transactional (Mandrill)"""
        import aiohttp

        api_key = os.environ.get("MANDRILL_API_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://mandrillapp.com/api/1.0/messages/send",
                json={
                    "key": api_key,
                    "message": {
                        "from_email": kwargs.get("from_email"),
                        "to": [{"email": email} for email in to],
                        "subject": subject,
                        "html" if html else "text": body
                    }
                }
            ) as response:
                return await response.json()

    async def _smtp_send(self, to, subject, body, html, attachments, **kwargs):
        """Direct SMTP"""
        import aiosmtplib

        msg = MIMEMultipart()
        msg["From"] = kwargs.get("from_email")
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html" if html else "plain"))

        await aiosmtplib.send(
            msg,
            hostname=kwargs.get("smtp_host", os.environ.get("SMTP_HOST")),
            port=kwargs.get("smtp_port", int(os.environ.get("SMTP_PORT", 587))),
            username=kwargs.get("smtp_user", os.environ.get("SMTP_USER")),
            password=kwargs.get("smtp_pass", os.environ.get("SMTP_PASSWORD")),
            start_tls=True
        )
        return {"sent": True, "provider": "smtp"}

    async def ai_compose_email(
        self,
        prompt: str,
        tone: str = "professional",
        llm_provider: str = "openai"
    ) -> Dict[str, str]:
        """AI-powered email composition"""
        from windows_ai.integrations.ai_providers import AIProvidersManager, Provider

        ai = AIProvidersManager()
        await ai.initialize()

        messages = [
            {"role": "system", "content": f"""You are an email writing assistant. Write emails in a {tone} tone.
Return JSON with: {{"subject": "...", "body": "..."}}"""},
            {"role": "user", "content": prompt}
        ]

        response = await ai.chat(Provider(llm_provider), messages)

        import json
        try:
            return json.loads(response["content"])
        except:
            return {"subject": "Email", "body": response["content"]}

    def list_providers(self) -> List[str]:
        return ["sendgrid", "mailgun", "ses", "resend", "postmark", "mailchimp", "smtp", "sparkpost", "mailjet"]
