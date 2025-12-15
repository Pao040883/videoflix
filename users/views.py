"""
User views.
"""
import uuid
import base64
import logging
from django.utils import timezone
from datetime import timedelta
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.conf import settings
from django.http import JsonResponse
from django.contrib.auth import login, logout as django_logout
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, EmailVerificationToken, PasswordResetToken
from users.utils import send_verification_email, send_password_reset_email

logger = logging.getLogger(__name__)


from users.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    API view for user registration with email verification.
    
    This view handles new user account creation. After successful registration,
    an email verification token is generated and a confirmation email is sent
    to the user's email address. The user account remains inactive until verified.
    
    Attributes:
        queryset: All CustomUser objects.
        serializer_class: RegisterSerializer for validation.
        permission_classes: [AllowAny] - No authentication required for registration.
    """
    queryset = CustomUser.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        Create a new user account with email verification.
        
        Creates a new user, generates an email verification token, and sends
        a verification email. The entire operation is wrapped in a database
        transaction to ensure data consistency.
        
        Args:
            request: HTTP request containing email, password, and confirmed_password.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            Response: HTTP 201 with success message if registration succeeds.
            Response: HTTP 400 with validation errors if registration fails.
        
        Raises:
            ValidationError: If passwords don't match or email already exists.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                user = serializer.save()
                # Create verification token and link
                EmailVerificationToken.objects.filter(user=user).delete()
                token_obj = EmailVerificationToken.objects.create(
                    user=user,
                    token=str(uuid.uuid4()),
                    expires_at=timezone.now() + timedelta(hours=24)
                )
                uidb64 = base64.b64encode(str(user.id).encode()).decode()
                verification_link = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uidb64}&token={token_obj.token}"
                
                # Email sending must succeed, otherwise rollback user creation
                send_verification_email(user, verification_link)
                
            return Response(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email
                    },
                    "message": "Registration successful. Please check your email to verify your account."
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {
                    "error": "Registration failed. Could not send verification email. Please try again later.",
                    "detail": str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(generics.GenericAPIView):
    """
    API view for user authentication and JWT token generation.
    
    This view authenticates users and generates JWT access and refresh tokens.
    Tokens are set as secure HttpOnly cookies to prevent XSS attacks. Only
    users with verified email addresses can log in.
    
    Attributes:
        serializer_class: LoginSerializer for credential validation.
        permission_classes: [AllowAny] - No authentication required for login.
    """
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        """
        Authenticate user and issue JWT tokens.
        
        Validates user credentials, verifies email confirmation status,
        generates JWT access and refresh tokens, and sets them as HttpOnly
        cookies with appropriate security settings.
        
        Args:
            request: HTTP request containing email and password.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        
        Returns:
            Response: HTTP 200 with user data if authentication succeeds.
            Response: HTTP 400 with error message if authentication fails.
        
        Raises:
            ValidationError: If credentials are invalid or email not verified.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Establish session so subsequent requests include credentials
        login(request, user)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        response = Response(
            {
                "detail": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.email
                }
            },
            status=status.HTTP_200_OK
        )
        
        # Set HttpOnly cookies for JWT tokens
        response.set_cookie(
            key='access_token',
            value=access_token,
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            samesite='Lax',
            secure=False  # Set to True in production with HTTPS
        )
        response.set_cookie(
            key='refresh_token',
            value=refresh_token,
            max_age=settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            samesite='Lax',
            secure=False  # Set to True in production with HTTPS
        )
        
        return response


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def activate_account(request, uidb64, token):
    """
    Activate user account via email verification link.
    
    Decodes the base64-encoded user ID, validates the verification token,
    and activates the user account if the token is valid and not expired.
    
    Args:
        request: HTTP request object.
        uidb64: Base64-encoded user ID.
        token: Email verification token string.
    
    Returns:
        Response: HTTP 200 if account activated successfully.
        Response: HTTP 400 if token is invalid or expired.
    
    Raises:
        User.DoesNotExist: If user ID is invalid.
    """
    try:
        uid = int(base64.b64decode(uidb64).decode())
        user = CustomUser.objects.get(id=uid)
        verification_token = EmailVerificationToken.objects.get(
            user=user,
            token=token
        )

        if verification_token.is_expired():
            return Response(
                {"error": "Verification link expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_active = True
        user.is_email_verified = True
        user.save()
        verification_token.delete()

        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK
        )
    except (CustomUser.DoesNotExist, EmailVerificationToken.DoesNotExist, ValueError):
        return Response(
            {"error": "Invalid verification link."},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout(request):
    """
    Log out authenticated user and clear JWT cookies.
    
    Performs Django session logout and removes access and refresh token cookies
    by deleting them from the response.
    
    Args:
        request: HTTP request from authenticated user.
    
    Returns:
        Response: HTTP 200 with success message.
    """
    django_logout(request)
    response = Response(
        {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
        status=status.HTTP_200_OK
    )
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset(request):
    """
    Initiate password reset process by sending reset email.
    
    Validates the user's email, generates a password reset token,
    and sends an email with a password reset link. Invalidates any
    existing reset tokens for the user.
    
    Args:
        request: HTTP request containing user email.
    
    Returns:
        Response: HTTP 200 with success message.
    
    Note:
        Returns success even for non-existent emails (via serializer validation)
        to prevent email enumeration attacks.
    """
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    user = CustomUser.objects.get(email=email)

    PasswordResetToken.objects.filter(user=user).delete()
    reset_token = PasswordResetToken.objects.create(
        user=user,
        token=str(uuid.uuid4()),
        expires_at=timezone.now() + timedelta(hours=24)
    )

    uidb64 = base64.b64encode(str(user.id).encode()).decode()
    reset_link = f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uidb64}&token={reset_token.token}"
    send_password_reset_email(user, reset_link)

    return Response(
        {"detail": "An email has been sent to reset your password."},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def password_reset_confirm(request, uidb64, token):
    """
    Confirm password reset and update user password.
    
    Validates the password reset token, verifies it hasn't expired,
    and updates the user's password to the new value. Deletes the
    reset token after successful password update.
    
    Args:
        request: HTTP request containing new_password and confirm_password.
        uidb64: Base64-encoded user ID.
        token: Password reset token string.
    
    Returns:
        Response: HTTP 200 if password updated successfully.
        Response: HTTP 400 if token invalid, expired, or passwords don't match.
    
    Raises:
        User.DoesNotExist: If user ID is invalid.
    """
    try:
        uid = int(base64.b64decode(uidb64).decode())
        user = CustomUser.objects.get(id=uid)
        reset_token = PasswordResetToken.objects.get(
            user=user,
            token=token
        )

        if reset_token.is_expired():
            return Response(
                {"error": "Reset link expired."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        reset_token.delete()

        return Response(
            {"detail": "Your Password has been successfully reset."},
            status=status.HTTP_200_OK
        )
    except (CustomUser.DoesNotExist, PasswordResetToken.DoesNotExist, ValueError):
        return Response(
            {"error": "Invalid reset link."},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """
    Retrieve authenticated user's profile data.
    
    Returns the current user's profile information including email,
    verification status, and other account details.
    
    Args:
        request: HTTP request from authenticated user.
    
    Returns:
        Response: HTTP 200 with serialized user data.
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)
