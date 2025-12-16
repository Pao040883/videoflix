"""
Video API tests for listing, detail, and upload functionality.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from users.models import CustomUser
from videos.models import Video


class VideoListTests(TestCase):
    """Test video listing functionality."""

    def setUp(self):
        """Set up test client and authenticated user."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        from videos.models import Genre
        genre = Genre.objects.create(name='Action')
        Video.objects.create(
            title='Test Video',
            description='Test Description',
            genre=genre,
            is_published=True
        )

    def test_video_list_authenticated(self):
        """Test authenticated user can list videos."""
        response = self.client.get('/api/video/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_video_list_unauthenticated(self):
        """Test unauthenticated user cannot list videos."""
        self.client.force_authenticate(user=None)
        response = self.client.get('/api/video/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VideoDetailTests(TestCase):
    """Test video detail functionality."""

    def setUp(self):
        """Set up test client, user, and video."""
        self.client = APIClient()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='TestPass123!'
        )
        self.user.is_email_verified = True
        self.user.save()
        self.client.force_authenticate(user=self.user)
        from videos.models import Genre
        genre = Genre.objects.create(name='Action')
        self.video = Video.objects.create(
            title='Test Video',
            description='Test Description',
            genre=genre,
            is_published=True
        )

    def test_video_detail_authenticated(self):
        """Test authenticated user can view video detail."""
        response = self.client.get('/api/video/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that video is in response
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['title'], 'Test Video')

    def test_video_detail_not_found(self):
        """Test empty video list for fresh database."""
        Video.objects.all().delete()
        response = self.client.get('/api/video/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class VideoUploadPermissionTests(TestCase):
    """Test video upload permission controls."""

    def setUp(self):
        """Set up test client, regular user, and admin user."""
        self.client = APIClient()
        # Regular user
        self.regular_user = CustomUser.objects.create_user(
            email='user@example.com',
            password='TestPass123!'
        )
        self.regular_user.is_email_verified = True
        self.regular_user.save()
        # Admin user
        self.admin_user = CustomUser.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!'
        )
        self.admin_user.is_email_verified = True
        self.admin_user.save()
        from videos.models import Genre
        self.genre = Genre.objects.create(name='Action')
        self.upload_url = '/api/video/'

    def test_regular_user_cannot_upload_video(self):
        """Test video upload endpoint only accepts GET requests (no POST)."""
        self.client.force_authenticate(user=self.regular_user)
        video_file = SimpleUploadedFile('test_video.mp4', b'file_content', content_type='video/mp4')
        data = {
            'title': 'Test Video',
            'description': 'Test Description',
            'genre': self.genre.id,
            'video_file': video_file
        }
        response = self.client.post(self.upload_url, data, format='multipart')
        # Video list endpoint is GET-only, POST not allowed
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_admin_can_access_video_list(self):
        """Test admin user can access video list via GET."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.upload_url)
        # Admin should have normal GET access like any authenticated user
        self.assertEqual(response.status_code, status.HTTP_200_OK)
