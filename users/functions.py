"""
Helper functions for user authentication and account management.
"""
import uuid
import base64
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import EmailVerificationToken, PasswordResetToken, CustomUser
from users.utils import send_verification_email, send_password_reset_email
from rest_framework import serializers
from django.contrib.auth import authenticate


def create_user_with_verification(user):
    """
    Create verification token and send verification email.
    
    Args:
        user: CustomUser instance.
    
    Returns:
        dict: User data with id and email.
    """
    EmailVerificationToken.objects.filter(user=user).delete()
    token_obj = EmailVerificationToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=timezone.now() + timedelta(hours=24)
    )
    uidb64 = base64.b64encode(str(user.id).encode()).decode()
    verification_link = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uidb64}&token={token_obj.token}"
    send_verification_email(user, verification_link)
    
    return {
        "user": {
            "id": user.id,
            "email": user.email
        },
        "message": "Registration successful. Please check your email to verify your account."
    }


def generate_jwt_tokens(user):
    """
    Generate JWT access and refresh tokens for user.
    
    Args:
        user: CustomUser instance.
    
    Returns:
        tuple: (access_token, refresh_token) as strings.
    """
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    return access_token, refresh_token


def set_jwt_cookies(response, access_token, refresh_token):
    """
    Set JWT tokens as HttpOnly cookies on response.
    
    Args:
        response: Django Response object.
        access_token: Access token string.
        refresh_token: Refresh token string.
    
    Returns:
        Response: Modified response with cookies set.
    """
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        samesite='Lax',
        secure=False
    )
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        samesite='Lax',
        secure=False
    )
    return response


def create_password_reset_token(user):
    """
    Create password reset token and send reset email.
    
    Args:
        user: CustomUser instance.
    
    Returns:
        None
    """
    PasswordResetToken.objects.filter(user=user).delete()
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=timezone.now() + timedelta(hours=24)
    )
    uidb64 = base64.b64encode(str(user.id).encode()).decode()
    reset_link = f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uidb64}&token={reset_token.token}"
    send_password_reset_email(user, reset_link)


def validate_password_match(password, confirmed_password):
    """Validate password and confirmed_password match."""
    if password != confirmed_password:
        raise serializers.ValidationError({"password": "Passwords do not match."})


def validate_email_unique(email):
    """Validate email is unique and not already registered."""
    if CustomUser.objects.filter(email=email).exists():
        raise serializers.ValidationError("Please check your inputs and try again.")


def validate_user_authentication(email, password):
    """Authenticate user and return authenticated user."""
    user = authenticate(username=email, password=password)
    if not user:
        raise serializers.ValidationError("Please check your inputs and try again.")
    return user


def validate_email_verified(user):
    """Check if user's email is verified."""
    if not user.is_email_verified:
        raise serializers.ValidationError("Please confirm your email first.")
