"""
User views.
"""
import base64
import logging
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.conf import settings

from users.models import CustomUser, EmailVerificationToken, PasswordResetToken
from users.functions import (
    create_user_with_verification,
    generate_jwt_tokens,
    set_jwt_cookies,
    create_password_reset_token,
    decode_uid_and_get_user,
    validate_token_not_expired,
    activate_user_account,
    update_user_password,
    set_access_token_cookie
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
        """Create a new user account with email verification."""
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
        
        access_token, refresh_token = generate_jwt_tokens(user)
        
        response = Response(
            {"detail": "Login successful", "user": {"id": user.id, "username": user.email}},
            status=status.HTTP_200_OK
        )
        return set_jwt_cookies(response, access_token, refresh_token)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def activate_account(request, uidb64, token):
    """Activate user account via email verification link."""
    try:
        user = decode_uid_and_get_user(uidb64)
        verification_token = EmailVerificationToken.objects.get(user=user, token=token)
        error_response = validate_token_not_expired(verification_token, "Verification link expired.")
        if error_response:
            return error_response
        activate_user_account(user, verification_token)
        return Response({"message": "Account successfully activated."}, status=status.HTTP_200_OK)
    except (CustomUser.DoesNotExist, EmailVerificationToken.DoesNotExist, ValueError):
        return Response({"error": "Invalid verification link."}, status=status.HTTP_400_BAD_REQUEST)


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
    logger = logging.getLogger(__name__)
    logger.info(f"Logout request received - User: {request.user}, IP: {request.META.get('REMOTE_ADDR')}")
    
    refresh_token = request.COOKIES.get('refresh_token')
    logger.info(f"Refresh token present: {bool(refresh_token)}")
    
    if refresh_token:
        try:
            logger.info("Attempting to blacklist refresh token...")
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Refresh token successfully blacklisted")
        except Exception as e:
            logger.error(f"Error blacklisting token: {str(e)}", exc_info=True)
    
    logger.info("Preparing logout response with deleted cookies")
    response = Response(
        {"detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."},
        status=status.HTTP_200_OK
    )
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    logger.info("Logout completed successfully")
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
    """Confirm password reset and update user password."""
    try:
        user = decode_uid_and_get_user(uidb64)
        reset_token = PasswordResetToken.objects.get(user=user, token=token)
        error_response = validate_token_not_expired(reset_token, "Reset link expired.")
        if error_response:
            return error_response
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_user_password(user, serializer.validated_data['new_password'], reset_token)
        return Response({"detail": "Your Password has been successfully reset."}, status=status.HTTP_200_OK)
    except (CustomUser.DoesNotExist, PasswordResetToken.DoesNotExist, ValueError):
        return Response({"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)


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


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def token_refresh(request):
    """Refresh access token using refresh token from cookie."""
    refresh_token = request.COOKIES.get('refresh_token')
    if not refresh_token:
        return Response({"error": "Refresh token missing."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        token = RefreshToken(refresh_token)
        new_access_token = str(token.access_token)
        response = Response({"detail": "Token refreshed", "access": new_access_token}, status=status.HTTP_200_OK)
        set_access_token_cookie(response, new_access_token)
        return response
    except (TokenError, InvalidToken) as e:
        return Response({"error": "Invalid or expired refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
