from django.urls import path
from users.api.views import (
    register,
    login,
    logout,
    activate_account,
    password_reset,
    password_reset_confirm,
    user_profile,
    token_refresh,
)

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', login, name='login'),
    path('logout/', logout, name='logout'),
    path('token/refresh/', token_refresh, name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', activate_account, name='activate_account'),
    path('password_reset/', password_reset, name='password_reset'),
    path('password_confirm/<str:uidb64>/<str:token>/', password_reset_confirm, name='password_reset_confirm'),
    path('user/', user_profile, name='user_profile'),
]
