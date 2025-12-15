"""
User views.
"""
import base64
import logging
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import login, logout as django_logout
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import CustomUser, EmailVerificationToken, PasswordResetToken
from users.functions import (
    create_user_with_verification,
    generate_jwt_tokens,
    set_jwt_cookies,
    create_password_reset_token
)

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
        
        Args:
            request: HTTP request containing email, password, and confirmed_password.
        
        Returns:
            Response: HTTP 201 with success message if registration succeeds.
            Response: HTTP 500 if email sending fails.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                user = serializer.save()
                response_data = create_user_with_verification(user)
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": "Registration failed. Could not send verification email. Please try again later."},
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
        
        Args:
            request: HTTP request containing email and password.
        
        Returns:
            Response: HTTP 200 with user data and JWT cookies.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        login(request, user)
        access_token, refresh_token = generate_jwt_tokens(user)
        
        response = Response(
            {"detail": "Login successful", "user": {"id": user.id, "username": user.email}},
            status=status.HTTP_200_OK
        )
        return set_jwt_cookies(response, access_token, refresh_token)


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
    
    Performs Django session logout, blacklists refresh token, and removes
    access and refresh token cookies from the response.
    
    Args:
        request: HTTP request from authenticated user.
    
    Returns:
        Response: HTTP 200 with success message.
        Response: HTTP 400 if refresh token missing.
    """
    refresh_token = request.COOKIES.get('refresh_token')
    
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
    
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
    
    Args:
        request: HTTP request containing user email.
    
    Returns:
        Response: HTTP 200 with success message.
    """
    serializer = PasswordResetSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = CustomUser.objects.get(email=serializer.validated_data['email'])
    create_password_reset_token(user)
    
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
