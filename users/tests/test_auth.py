"""
Authentication tests for user registration, login, logout, and password reset.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser, EmailVerificationToken, PasswordResetToken
import base64


class UserRegistrationTests(TestCase):
    """Test user registration functionality."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = '/api/register/'

    def test_user_registration_success(self):
        """Test successful user registration."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'confirmed_password': 'TestPass123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CustomUser.objects.filter(email='test@example.com').exists())

    def test_user_registration_password_mismatch(self):
        """Test registration fails with mismatched passwords."""
        data = {
            'email': 'test@example.com',
            'password': 'TestPass123!',
            'confirmed_password': 'DifferentPass123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailVerificationTests(TestCase):
    """Test email verification functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        from django.utils import timezone
        from datetime import timedelta
        self.token = EmailVerificationToken.objects.create(
            user=self.user, 
            token='test-token',
            expires_at=timezone.now() + timedelta(hours=24)
        )

    def test_email_verification_success(self):
        """Test successful email verification."""
        uid = base64.b64encode(str(self.user.id).encode()).decode()
        url = f'/api/activate/{uid}/{self.token.token}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)


class LoginLogoutTests(TestCase):
    """Test user login and logout functionality."""

    def setUp(self):
        """Set up test client and verified user."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.is_email_verified = True
        self.user.save()
        self.login_url = '/api/login/'
        self.logout_url = '/api/logout/'

    def test_login_success(self):
        """Test successful login."""
        data = {'email': 'test@example.com', 'password': 'TestPass123!'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

    def test_login_unverified_email(self):
        """Test login fails for unverified email."""
        self.user.is_email_verified = False
        self.user.save()
        data = {'email': 'test@example.com', 'password': 'TestPass123!'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_success(self):
        """Test successful logout."""
        self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'TestPass123!'})
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TokenRefreshTests(TestCase):
    """Test JWT token refresh functionality."""

    def setUp(self):
        """Set up test client and verified user."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.is_email_verified = True
        self.user.save()
        self.login_url = '/api/login/'
        self.refresh_url = '/api/token/refresh/'

    def test_token_refresh_success(self):
        """Test successful token refresh."""
        # Login to get refresh token
        self.client.post(self.login_url, {'email': 'test@example.com', 'password': 'TestPass123!'})
        # Refresh token
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)

    def test_token_refresh_without_refresh_token(self):
        """Test token refresh fails without refresh token."""
        response = self.client.post(self.refresh_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InvalidInputTests(TestCase):
    """Test validation for invalid inputs."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = '/api/register/'

    def test_registration_invalid_email(self):
        """Test registration fails with invalid email."""
        data = {
            'email': 'not-an-email',
            'password': 'TestPass123!',
            'confirmed_password': 'TestPass123!'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_weak_password(self):
        """Test registration fails with weak password."""
        data = {
            'email': 'test@example.com',
            'password': '123',
            'confirmed_password': '123'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        user.is_email_verified = True
        user.save()
        data = {'email': 'test@example.com', 'password': 'WrongPassword!'}
        response = self.client.post('/api/login/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTests(TestCase):
    """Test password reset functionality."""

    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='OldPass123!'
        )
        self.reset_url = '/api/password_reset/'

    def test_password_reset_request(self):
        """Test password reset email request."""
        data = {'email': 'test@example.com'}
        response = self.client.post(self.reset_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())

    def test_password_reset_confirm(self):
        """Test password reset confirmation."""
        from django.utils import timezone
        from datetime import timedelta
        token = PasswordResetToken.objects.create(
            user=self.user, 
            token='reset-token',
            expires_at=timezone.now() + timedelta(hours=24)
        )
        uid = base64.b64encode(str(self.user.id).encode()).decode()
        url = f'/api/password_confirm/{uid}/{token.token}/'
        data = {'new_password': 'NewPass123!', 'confirm_password': 'NewPass123!'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
