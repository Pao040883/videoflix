"""
User signals for automatic email notifications.
"""
import base64
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from users.models import EmailVerificationToken, PasswordResetToken
from users.utils import send_verification_email, send_password_reset_email


@receiver(post_save, sender=EmailVerificationToken)
def send_verification_email_signal(sender, instance, created, **kwargs):
    """
    Send verification email when EmailVerificationToken is created.
    
    Automatically sends email with activation link after token creation.
    """
    if created:
        uidb64 = base64.b64encode(str(instance.user.id).encode()).decode()
        verification_link = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uidb64}&token={instance.token}"
        send_verification_email(instance.user, verification_link)


@receiver(post_save, sender=PasswordResetToken)
def send_password_reset_email_signal(sender, instance, created, **kwargs):
    """
    Send password reset email when PasswordResetToken is created.
    
    Automatically sends email with reset link after token creation.
    """
    if created:
        uidb64 = base64.b64encode(str(instance.user.id).encode()).decode()
        reset_link = f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uidb64}&token={instance.token}"
        send_password_reset_email(instance.user, reset_link)
