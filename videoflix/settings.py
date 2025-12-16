"""
Django settings for videoflix project.
"""

from pathlib import Path
from decouple import config
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='your-secret-key-change-in-production')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'users',  # Must be before admin due to custom user model
    'django.contrib.admin',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_rq',
    'videos',
]

# Use the custom user model defined in the users app
AUTH_USER_MODEL = 'users.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'videoflix.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'videoflix.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='videoflix_db'),
        'USER': config('DB_USER', default='videoflix_user'),
        'PASSWORD': config('DB_PASSWORD', default='videoflix_password'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise static files storage with compression and caching
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'users.authentication.JWTCookieAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=25),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'AUTH_COOKIE_SECURE': not DEBUG,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_SAMESITE': 'Lax',
}

CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:4200,http://127.0.0.1:4200', cast=lambda v: [s.strip() for s in v.split(',')])

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://127.0.0.1:5500,http://localhost:5500', cast=lambda v: [s.strip() for s in v.split(',')])
CORS_ALLOW_CREDENTIALS = True

# CSRF cookie configuration for POST request protection
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False').lower() == 'true'
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='your-email@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='your-app-password')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@videoflix.de')

# Frontend URL for email links
FRONTEND_URL = config('FRONTEND_URL', default='http://127.0.0.1:5500')

RQ_QUEUES = {
    'default': {
        'HOST': os.environ.get("REDIS_HOST", default="redis"),
        'PORT': os.environ.get("REDIS_PORT", default=6379),
        'DB': os.environ.get("REDIS_DB", default=0),
        'PASSWORD': os.environ.get("REDIS_PASSWORD", default=None),
        'DEFAULT_TIMEOUT': 900,
        'REDIS_CLIENT_KWARGS': {},
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default=6379)}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        "KEY_PREFIX": "videoflix"
    }
}

VIDEO_UPLOAD_PATH = os.path.join(BASE_DIR, 'media', 'videos')
HLS_OUTPUT_PATH = os.path.join(BASE_DIR, 'media', 'hls')
THUMBNAIL_PATH = os.path.join(BASE_DIR, 'media', 'thumbnails')

os.makedirs(VIDEO_UPLOAD_PATH, exist_ok=True)
os.makedirs(HLS_OUTPUT_PATH, exist_ok=True)
os.makedirs(THUMBNAIL_PATH, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'videoflix.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}

os.makedirs(BASE_DIR / 'logs', exist_ok=True)
