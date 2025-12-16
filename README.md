# 🎬 Videoflix Backend API

A Django REST API backend for a Netflix-like video streaming platform with HLS (HTTP Live Streaming) support, JWT authentication, and background video processing.

## 🎯 Frontend Example

An example frontend implementation using vanilla JavaScript is available at:
**https://github.com/Developer-Akademie-Backendkurs/project.Videoflix**

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Video Processing](#video-processing)
- [Project Structure](#project-structure)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

## ✨ Features

### Authentication & User Management
- 🔐 **JWT Authentication** with HttpOnly cookies (XSS protection)
- 📧 **Email Verification** for new accounts
- 🔑 **Password Reset** via email
- 👤 **User Profile** management
- 🔄 **Token Refresh** mechanism

### Video Streaming
- 🎥 **HLS Streaming** with adaptive bitrate
- 📱 **Multiple Quality Options** (480p, 720p, 1080p)
- 🎞️ **Segment-based Loading** for efficient streaming
- 🖼️ **Automatic Thumbnail Generation**
- ⏱️ **Video Duration Detection**

### Background Processing
- ⚙️ **Django RQ** for asynchronous video processing
- 🔄 **Redis Queue** management
- 📊 **Job Status Monitoring** via Django RQ dashboard

### Additional Features
- 🗂️ **Genre/Category** management
- 🚀 **Redis Caching** for video lists
- 📝 **Comprehensive Logging**
- 🔒 **CORS Configuration** for frontend integration
- 🌐 **Static File Serving** with WhiteNoise

## 🛠️ Tech Stack

| Category | Technology |
|----------|-----------|
| **Framework** | Django 4.2.8 |
| **API** | Django REST Framework |
| **Authentication** | Simple JWT (djangorestframework-simplejwt) |
| **Database** | PostgreSQL |
| **Cache & Queue** | Redis |
| **Background Jobs** | Django RQ (RQ Worker) |
| **Video Processing** | FFmpeg |
| **Static Files** | WhiteNoise |
| **Deployment** | Docker, Docker Compose, Gunicorn |
| **Email** | SMTP (Strato) |

## 📦 Prerequisites

- Docker Desktop installed
- Docker Compose installed
- Git installed
- SMTP email credentials (for email verification)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd backend
```

### 2. Configure Environment Variables

Copy the `.env.template` file and rename it to `.env`:

```bash
cp .env.template .env
```

Edit the `.env` file with your configuration:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,web

# Database
DB_NAME=videoflix_db
DB_USER=videoflix_user
DB_PASSWORD=your-secure-password
DB_HOST=db
DB_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Email Configuration
EMAIL_HOST=smtp.strato.de
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=your-email@example.com

# Frontend URL (for email links)
FRONTEND_URL=http://127.0.0.1:5500

# Django Superuser
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=adminpassword
```

### 3. Build and Start Docker Containers

```bash
docker-compose up --build
```

This will:
- ✅ Build the Django application image
- ✅ Start PostgreSQL database
- ✅ Start Redis server
- ✅ Run migrations
- ✅ Create superuser
- ✅ Start RQ worker for background jobs
- ✅ Start Gunicorn server on port 8000

## ⚙️ Configuration

### CORS Settings

Configure allowed origins in `.env`:

```env
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
CSRF_TRUSTED_ORIGINS=http://localhost:4200,http://127.0.0.1:4200
```

### JWT Token Settings

Access token lifetime: **5 minutes**  
Refresh token lifetime: **7 days**

Tokens are stored in **HttpOnly cookies** for security.

## 🎮 Running the Application

### Start All Services

```bash
docker-compose up
```

### Stop All Services

```bash
docker-compose down
```

### Restart Specific Service

```bash
docker-compose restart web
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f redis
```

### Access Django Admin

Navigate to: `http://localhost:8000/admin`

Default credentials (from `.env`):
- Username: `admin`
- Password: `adminpassword`

### Access Django RQ Dashboard

Navigate to: `http://localhost:8000/django-rq/`

Monitor background video processing jobs.

## 📡 API Documentation

Base URL: `http://localhost:8000/api/`

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/register/` | Register new user | ❌ |
| POST | `/api/login/` | Login user | ❌ |
| POST | `/api/logout/` | Logout user | ✅ |
| POST | `/api/token/refresh/` | Refresh access token | ❌ |
| GET | `/api/activate/<uidb64>/<token>/` | Activate account | ❌ |
| POST | `/api/password_reset/` | Request password reset | ❌ |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Confirm password reset | ❌ |
| GET | `/api/user/` | Get user profile | ✅ |

### Video Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/video/` | List all published videos | ✅ |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | Get HLS manifest | ✅ |
| GET | `/api/video/<id>/<resolution>/<segment>` | Get video segment | ✅ |

### Example Requests

#### Register User

```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword",
    "confirmed_password": "securepassword"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword"
  }'
```

#### Get Video List

```bash
curl http://localhost:8000/api/video/ \
  -H "Cookie: access_token=your_token_here"
```

## 🎞️ Video Processing

### How it Works

1. **Upload Video** via Django Admin
2. **Background Processing** triggered automatically:
   - Extract video duration
   - Generate thumbnail (at 5 seconds)
   - Transcode to HLS format (3 qualities)
3. **Video Published** and ready for streaming

### Video Quality Presets

| Quality | Resolution | Bitrate | Max Rate | Buffer Size |
|---------|-----------|---------|----------|-------------|
| **480p** | 854x480 | 1500k | 1750k | 3500k |
| **720p** | 1280x720 | 3500k | 4000k | 8000k |
| **1080p** | 1920x1080 | 6500k | 7500k | 15000k |

### HLS Configuration

- **Segment Duration**: 10 seconds
- **Segment Format**: MPEG-TS (.ts)
- **Playlist Type**: Dynamic (on-demand loading)
- **Flags**: `independent_segments`

## 📁 Project Structure

```
backend/
├── logs/                      # Application logs
├── media/                     # User-uploaded media
│   ├── videos/               # Original video files
│   ├── thumbnails/           # Generated thumbnails
│   └── hls/                  # HLS streaming files
├── static/                    # Static files
│   └── images/               # Static images (e.g., email logo)
├── staticfiles/              # Collected static files
├── templates/                # Email templates
│   └── emails/
│       ├── verify_email.html
│       └── reset_password.html
├── users/                    # User app
│   ├── models.py            # CustomUser, Tokens
│   ├── views.py             # Authentication views (all endpoints)
│   ├── serializers.py       # User serializers
│   ├── functions.py         # Authentication helper functions
│   ├── utils.py             # Email utilities
│   ├── images/              # Static images (e.g., logo)
│   └── urls.py              # User routes
├── videos/                   # Video app
│   ├── models.py            # Video, Genre, HLSQuality
│   ├── views.py             # Video streaming views
│   ├── serializers.py       # Video serializers
│   ├── functions.py         # Video helper functions
│   ├── tasks.py             # Background tasks (Django RQ)
│   ├── utils.py             # Video processing utilities
│   ├── signals.py           # Django signals
│   └── urls.py              # Video routes
├── videoflix/                # Project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL config
│   └── wsgi.py              # WSGI config
├── docker-compose.yml        # Docker services
├── backend.Dockerfile        # Docker image
├── backend.entrypoint.sh     # Container startup script
├── requirements.txt          # Python dependencies
├── manage.py                 # Django management
└── .env                      # Environment variables
```

## 🔧 Development

### Database Migrations

```bash
# Create migrations
docker-compose exec web python manage.py makemigrations

# Apply migrations
docker-compose exec web python manage.py migrate
```

### Create Superuser (Manual)

```bash
docker-compose exec web python manage.py createsuperuser
```

### Django Shell

```bash
docker-compose exec web python manage.py shell
```

### Collect Static Files

```bash
docker-compose exec web python manage.py collectstatic --noinput
```

### Run Tests

```bash
docker-compose exec web python manage.py test
```

## 🐛 Troubleshooting

### RQ Worker Not Running

Check RQ dashboard: `http://localhost:8000/django-rq/`

If worker is inactive:
```bash
docker-compose restart web
```

### Redis Connection Issues

Check Redis container:
```bash
docker-compose logs redis
```

Restart Redis:
```bash
docker-compose restart redis
```

### Video Processing Stuck

1. Check RQ dashboard for failed jobs
2. Check worker logs:
```bash
docker-compose logs web | grep rqworker
```

### Database Connection Errors

Recreate database:
```bash
docker-compose down -v
docker-compose up --build
```

### Email Not Sending

Verify `.env` email settings:
- Correct SMTP host and port
- Valid email credentials
- TLS/SSL settings match provider

Test email configuration in Django shell:
```python
from django.core.mail import send_mail
send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

## 📝 Notes

### Code Quality Standards

- ✅ All functions max 14 lines (excluding docstrings)
- ✅ Comprehensive docstrings on all classes, methods, and functions
- ✅ Modular design with helper function modules
- ✅ Clear separation of concerns (views, models, serializers, utils)
- ✅ Type hints and proper error handling

### Security Considerations

- ✅ JWT tokens stored in HttpOnly cookies (XSS protection)
- ✅ CSRF protection enabled
- ✅ Password hashing with Django's default PBKDF2
- ✅ Email verification required for activation
- ⚠️ Change `SECRET_KEY` in production
- ⚠️ Set `DEBUG=False` in production
- ⚠️ Use HTTPS in production (set cookies as `Secure`)

### Production Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Update `ALLOWED_HOSTS` with your domain
3. Configure proper HTTPS/SSL
4. Use strong `SECRET_KEY`
5. Set cookie `Secure=True` in `settings.py`
6. Configure proper CORS origins
7. Use production-grade Redis instance
8. Set up proper logging and monitoring

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Built with ❤️ using Django REST Framework**
