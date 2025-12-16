"""
Token refresh view.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.conf import settings
from users.functions import set_access_token_cookie


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
