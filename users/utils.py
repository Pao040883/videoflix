"""
Utility functions for user authentication and email handling
"""
import base64
import logging
from email.mime.image import MIMEImage
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# Videoflix Logo as Base64 (PNG) - kept as single line to avoid syntax errors
VIDEOFLIX_LOGO_BASE64 = "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"


def load_logo_image():
    """Load logo image from file or Base64 fallback."""
    logo_path = finders.find('images/logo_videoflix.png')
    if not logo_path:
        logger.warning("Logo file not found, using Base64 fallback")
        return base64.b64decode(VIDEOFLIX_LOGO_BASE64)
    logger.info(f"Logo found at: {logo_path}")
    with open(logo_path, 'rb') as f:
        return f.read()


def create_mime_image(img_data):
    """Create MIMEImage with CID for email embedding."""
    image_cid = 'videoflix_logo@videoflix.com'
    image_mime = MIMEImage(img_data)
    image_mime.add_header('Content-ID', f'<{image_cid}>')
    image_mime.add_header('Content-Disposition', 'inline', filename='logo_videoflix.png')
    return image_mime, image_cid


def send_verification_email(user, verification_link):
    """Send account verification email to user"""
    logger.info(f"Starting to send verification email to {user.email}")
    try:
        img_data = load_logo_image()
        image_mime, image_cid = create_mime_image(img_data)
        html_content = render_to_string('emails/verify_email.html', {'user': user, 'verification_link': verification_link, 'image_cid': image_cid})
        text_content = f"Click the link below to verify your account:\n{verification_link}"
        email = EmailMultiAlternatives('Activate your Videoflix account', text_content, f"Videoflix <{settings.DEFAULT_FROM_EMAIL}>", [user.email])
        email.attach_alternative(html_content, "text/html")
        email.attach(image_mime)
        email.send()
        logger.info(f"Verification email sent successfully to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Error sending verification email to {user.email}: {e}", exc_info=True)
        raise


def send_password_reset_email(user, reset_link):
    """Send password reset email to user"""
    try:
        img_data = load_logo_image()
        image_mime, image_cid = create_mime_image(img_data)
        html_content = render_to_string("emails/reset_password.html", {"user": user, "reset_link": reset_link, "image_cid": image_cid})
        text_content = f"Click the link below to reset your password:\n{reset_link}"
        email = EmailMultiAlternatives("Videoflix - Reset your password", text_content, f"Videoflix <{settings.DEFAULT_FROM_EMAIL}>", [user.email])
        email.attach_alternative(html_content, "text/html")
        email.attach(image_mime)
        email.send()
        logger.info(f"Password reset email sent to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Error sending password reset email to {user.email}: {e}", exc_info=True)
        raise
