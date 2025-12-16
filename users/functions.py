"""
Helper functions for user authentication and account management.
"""
import uuid
import base64
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import EmailVerificationToken, PasswordResetToken, CustomUser
from rest_framework import serializers
from django.contrib.auth import authenticate


def create_user_with_verification(user):
    """
    Create verification token for user.
    
    Email is automatically sent via post_save signal.
    
    Args:
        user: CustomUser instance.
    
    Returns:
        dict: User data with id and email.
    """
    EmailVerificationToken.objects.filter(user=user).delete()
    EmailVerificationToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=timezone.now() + timedelta(hours=24)
    )
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


def set_access_token_cookie(response, access_token):
    """Set access token as HttpOnly cookie."""
    response.set_cookie(
        key='access_token',
        value=access_token,
        max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        samesite='Lax',
        secure=False
    )


def set_refresh_token_cookie(response, refresh_token):
    """Set refresh token as HttpOnly cookie."""
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
        httponly=True,
        samesite='Lax',
        secure=False
    )


def set_jwt_cookies(response, access_token, refresh_token):
    """Set JWT tokens as HttpOnly cookies on response."""
    set_access_token_cookie(response, access_token)
    set_refresh_token_cookie(response, refresh_token)
    return response


def create_password_reset_token(user):
    """
    Create password reset token for user.
    
    Email is automatically sent via post_save signal.
    
    Args:
        user: CustomUser instance.
    
    Returns:
        None
    """
    PasswordResetToken.objects.filter(user=user).delete()
    PasswordResetToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=timezone.now() + timedelta(hours=24)
    )


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


def decode_uid_and_get_user(uidb64):
    """Decode base64 user ID and retrieve user."""
    uid = int(base64.b64decode(uidb64).decode())
    return CustomUser.objects.get(id=uid)


def validate_token_not_expired(token_obj, error_message):
    """Check if token is expired and return error response if so."""
    from rest_framework.response import Response
    from rest_framework import status
    if token_obj.is_expired():
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    return None


def activate_user_account(user, verification_token):
    """Activate user account and delete verification token."""
    user.is_active = True
    user.is_email_verified = True
    user.save()
    verification_token.delete()


def update_user_password(user, new_password, reset_token):
    """Update user password and delete reset token."""
    user.set_password(new_password)
    user.save()
    reset_token.delete()
