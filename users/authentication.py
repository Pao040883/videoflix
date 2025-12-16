"""
Custom JWT authentication that reads tokens from HttpOnly cookies.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class JWTCookieAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads access token from HttpOnly cookie.
    
    Extends the default JWTAuthentication to support cookie-based tokens
    instead of Authorization header.
    """
    
    def authenticate(self, request):
        """
        Extract JWT token from 'access_token' cookie and authenticate.
        
        Args:
            request: HTTP request object.
        
        Returns:
            tuple: (user, validated_token) or None if no cookie found.
        """
        access_token = request.COOKIES.get('access_token')
        
        if access_token is None:
            return None
        
        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token
