"""
User admin.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import CustomUser, EmailVerificationToken, PasswordResetToken


class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Email Verification', {'fields': ('is_email_verified',)}),
    )
    list_display = ('email', 'username', 'is_email_verified', 'is_active', 'created_at')
    list_filter = ('is_email_verified', 'is_active', 'created_at')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(EmailVerificationToken)
admin.site.register(PasswordResetToken)
