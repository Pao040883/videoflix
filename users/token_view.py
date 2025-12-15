"""
Token refresh view.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.conf import settings


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def token_refresh(request):
    refresh_token = request.COOKIES.get('refresh_token')
    
    if not refresh_token:
        return Response(
            {"error": "Refresh token missing."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate refresh token and generate new access token
        token = RefreshToken(refresh_token)
        new_access_token = str(token.access_token)
        
        response = Response(
            {
                "detail": "Token refreshed",
                "access": new_access_token
            },
            status=status.HTTP_200_OK
        )
        
        # Set new access token as HttpOnly cookie
        response.set_cookie(
            key='access_token',
            value=new_access_token,
            max_age=settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            httponly=True,
            samesite='Lax',
            secure=False  # Set to True in production with HTTPS
        )
        
        return response
        
    except (TokenError, InvalidToken) as e:
        return Response(
            {"error": "Invalid or expired refresh token."},
            status=status.HTTP_401_UNAUTHORIZED
        )
