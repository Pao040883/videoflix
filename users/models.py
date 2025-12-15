"""
User models.
"""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """User manager that uses email as the identifier but keeps username for compatibility."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a user with the given email and password."""
        if not email:
            raise ValueError("The email field must be set")
        email = self.normalize_email(email)
        username = extra_fields.pop('username', None) or email
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Custom user model using email as the primary identifier.
    
    Extends Django's AbstractUser to use email-based authentication instead
    of username. The username field is retained for compatibility with existing
    Django components but is not required or unique.
    
    Attributes:
        username: Optional username field (kept for compatibility).
        email: Unique email address used for authentication.
        is_email_verified: Boolean flag indicating if email has been verified.
        created_at: Timestamp of account creation.
        updated_at: Timestamp of last account update.
        USERNAME_FIELD: Set to 'email' for email-based authentication.
        REQUIRED_FIELDS: Empty list since email is the USERNAME_FIELD.
    """
    # Keep username field for compatibility with existing scripts, but authenticate via email.
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=False,
        blank=True,
        null=True,
    )
    email = models.EmailField(_("email address"), unique=True)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='customuser_set'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='customuser_set'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ['-created_at']

    def __str__(self):
        return self.email


class EmailVerificationToken(models.Model):
    """
    Token model for email verification during user registration.
    
    Stores a unique verification token for each user to confirm their email
    address. Tokens are valid for 24 hours after creation.
    
    Attributes:
        user: OneToOne relationship with CustomUser.
        token: Unique UUID token string.
        created_at: Timestamp of token creation.
        expires_at: Timestamp when token expires (24 hours after creation).
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='verification_token')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = _("email verification token")
        verbose_name_plural = _("email verification tokens")

    def is_expired(self):
        """
        Check if the verification token has expired.
        
        Returns:
            bool: True if current time exceeds expires_at, False otherwise.
        """
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Verification token for {self.user.email}"


class PasswordResetToken(models.Model):
    """
    Token model for password reset functionality.
    
    Stores a unique reset token for each user requesting a password reset.
    Tokens are valid for 24 hours after creation.
    
    Attributes:
        user: OneToOne relationship with CustomUser.
        token: Unique UUID token string.
        created_at: Timestamp of token creation.
        expires_at: Timestamp when token expires (24 hours after creation).
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='reset_token')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        verbose_name = _("password reset token")
        verbose_name_plural = _("password reset tokens")

    def is_expired(self):
        """
        Check if the reset token has expired.
        
        Returns:
            bool: True if current time exceeds expires_at, False otherwise.
        """
        from django.utils import timezone
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Reset token for {self.user.email}"
