"""
User serializers.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import CustomUser


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Validates user registration data including email uniqueness and password
    confirmation. Ensures passwords match and meet minimum length requirements.
    
    Attributes:
        password: Write-only field with minimum 8 characters.
        confirmed_password: Write-only field for password confirmation.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    confirmed_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = CustomUser
        fields = ['email', 'password', 'confirmed_password']

    def validate(self, data):
        """Validate that password and confirmed_password match."""
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return data

    def validate_email(self, value):
        """Validate that email is unique and not already registered."""
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Please check your inputs and try again."
            )
        return value

    def create(self, validated_data):
        """Create a new inactive user with hashed password."""
        validated_data.pop('confirmed_password')
        password = validated_data.pop('password')
        email = validated_data['email']
        # Mirror email into username so authentication with email works while username field exists.
        user = CustomUser(username=email, **validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user authentication.
    
    Validates login credentials and ensures email is verified before
    allowing authentication.
    
    Attributes:
        email: User's email address.
        password: Write-only password field.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        """Authenticate user and verify email confirmation status."""
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError(
                "Please check your inputs and try again."
            )
        if not user.is_email_verified:
            raise serializers.ValidationError(
                "Please confirm your email first."
            )
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data.
    
    Provides read-only access to user information including email,
    name, verification status, and account creation date.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_email_verified', 'created_at']
        read_only_fields = ['id', 'is_email_verified', 'created_at']


class PasswordResetSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    
    Validates that the provided email belongs to an existing user.
    
    Attributes:
        email: Email address for password reset.
    """
    email = serializers.EmailField()

    def validate_email(self, value):
        """Validate that email exists in the database."""
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Please check your inputs and try again."
            )
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    
    Validates new password and confirmation match, and meet minimum
    length requirements.
    
    Attributes:
        new_password: Write-only field with minimum 8 characters.
        confirm_password: Write-only field for password confirmation.
    """
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        """Validate that new_password and confirm_password match."""
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return data

