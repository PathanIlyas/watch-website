import requests
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.conf import settings

logger = logging.getLogger(__name__)

class BrevoEmailBackend(BaseEmailBackend):
    """
    Custom Django Email Backend for Brevo (Sendinblue) HTTP API.
    Used to bypass Render's outbound SMTP port blocking on Free Tier.
    """
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        api_key = getattr(settings, 'BREVO_API_KEY', '')
        if not api_key:
            logger.error("Brevo API key is not configured (BREVO_API_KEY).")
            return 0
            
        sent_count = 0
        headers = {
            'accept': 'application/json',
            'api-key': api_key,
            'content-type': 'application/json'
        }
        
        for message in email_messages:
            from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
            sender_name = "CHRONOS"
            sender_address = from_email
            
            if "<" in from_email and ">" in from_email:
                parts = from_email.split("<")
                sender_name = parts[0].strip()
                sender_address = parts[1].replace(">", "").strip()
                
            payload = {
                "sender": {
                    "name": sender_name,
                    "email": sender_address
                },
                "to": [{"email": recipient} for recipient in message.to],
                "subject": message.subject,
                "textContent": message.body
            }
            
            # Extract HTML content if present
            html_content = None
            if hasattr(message, 'alternatives') and message.alternatives:
                for alternative in message.alternatives:
                    if alternative[1] == 'text/html':
                        html_content = alternative[0]
                        break
            
            if html_content:
                payload['htmlContent'] = html_content
            else:
                payload['htmlContent'] = message.body.replace('\n', '<br>')

            try:
                response = requests.post(
                    'https://api.brevo.com/v3/smtp/email',
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
                else:
                    logger.error(f"Brevo API error: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Failed to send email via Brevo: {e}")
                
        return sent_count


class ResendEmailBackend(BaseEmailBackend):
    """
    Custom Django Email Backend for Resend HTTP API.
    Used to bypass Render's outbound SMTP port blocking on Free Tier.
    """
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
            
        api_key = getattr(settings, 'RESEND_API_KEY', '')
        if not api_key:
            logger.error("Resend API key is not configured (RESEND_API_KEY).")
            return 0
            
        sent_count = 0
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        for message in email_messages:
            from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
            payload = {
                "from": from_email,
                "to": list(message.to),
                "subject": message.subject,
                "text": message.body
            }
            
            # Extract HTML content if present
            html_content = None
            if hasattr(message, 'alternatives') and message.alternatives:
                for alternative in message.alternatives:
                    if alternative[1] == 'text/html':
                        html_content = alternative[0]
                        break
            
            if html_content:
                payload['html'] = html_content
            else:
                payload['html'] = message.body.replace('\n', '<br>')
                
            try:
                response = requests.post(
                    'https://api.resend.com/emails',
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
                else:
                    logger.error(f"Resend API error: {response.status_code} - {response.text}")
            except Exception as e:
                logger.error(f"Failed to send email via Resend: {e}")
                
        return sent_count
