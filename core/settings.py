"""
Django settings for CHRONOS Luxury Watches.
"""

from pathlib import Path
from datetime import timedelta
import environ
import os
import mimetypes

env = environ.Env(DEBUG=(bool, False))


def clean_env(name, default=''):
    value = env(name, default=default)
    return value.strip() if isinstance(value, str) else value

BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ─── Security ─────────────────────────────────────────────────
SECRET_KEY = clean_env('SECRET_KEY', default='django-insecure-fallback-key-change-in-production')
DEBUG = env('DEBUG', default=False)
ALLOWED_HOSTS = [host.strip() for host in env.list('ALLOWED_HOSTS', default=['*']) if host.strip()]
RENDER_EXTERNAL_HOSTNAME = clean_env('RENDER_EXTERNAL_HOSTNAME', default=None)
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
if not DEBUG:
    ALLOWED_HOSTS.extend(['.onrender.com', 'localhost', '127.0.0.1'])
    ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in env.list('CSRF_TRUSTED_ORIGINS', default=[]) if origin.strip()]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f'https://{RENDER_EXTERNAL_HOSTNAME}')
if not DEBUG:
    CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')
    CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(CSRF_TRUSTED_ORIGINS))
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# ─── Apps ─────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Local apps
    'accounts',
    'store',
    'orders',
    'dashboard',
    'payments',
    'otp_auth',
]

# ─── Middleware ────────────────────────────────────────────────
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

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'template'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.cart_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# ─── Database ─────────────────────────────────────────────────
import dj_database_url

DATABASE_URL = clean_env('DATABASE_URL', default='')
if RENDER_EXTERNAL_HOSTNAME and DATABASE_URL.startswith('sqlite'):
    DATABASE_URL = ''

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL or f'sqlite:///{BASE_DIR}/db.sqlite3',
        conn_max_age=600,
    )
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Auth ─────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internationalisation ─────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ─── Static & Media ───────────────────────────────────────────
STATIC_URL = '/static/'
mimetypes.add_type("text/css", ".css", True)
mimetypes.add_type("application/javascript", ".js", True)

STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── REST Framework ───────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

CORS_ALLOW_ALL_ORIGINS = True

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ─── Razorpay ─────────────────────────────────────────────────
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='rzp_test_placeholder')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='placeholder_secret')

# ─── Email Settings (SMTP and HTTP APIs) ──────────────────────
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = clean_env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = clean_env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = clean_env('DEFAULT_FROM_EMAIL', default='CHRONOS Luxury Watches <noreply@chronos.com>')
ADMIN_EMAIL = clean_env('ADMIN_EMAIL', default='admin@chronos.com') or 'admin@chronos.com'
EMAIL_TIMEOUT = 10

# API keys for HTTP-based custom email backends (to bypass Render's Free SMTP blocking)
BREVO_API_KEY = clean_env('BREVO_API_KEY', default='')
RESEND_API_KEY = clean_env('RESEND_API_KEY', default='')


# ─── Auto Admin ───────────────────────────────────────────────
ADMIN_USERNAME = clean_env('ADMIN_USERNAME', default='admin') or 'admin'
ADMIN_PASSWORD = clean_env('ADMIN_PASSWORD', default='admin') or 'admin'

# ─── OTP / SMS ────────────────────────────────────────────────
SMS_PROVIDER           = clean_env('SMS_PROVIDER', default='console').lower()
FAST2SMS_API_KEY       = clean_env('FAST2SMS_API_KEY', default='your_fast2sms_api_key_here')
TWILIO_ACCOUNT_SID     = clean_env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN      = clean_env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER    = clean_env('TWILIO_PHONE_NUMBER', default='')
OTP_EXPIRY_MINUTES     = env.int('OTP_EXPIRY_MINUTES', default=5)
OTP_MAX_ATTEMPTS       = env.int('OTP_MAX_ATTEMPTS', default=5)
OTP_RATE_LIMIT_MINUTES = env.int('OTP_RATE_LIMIT_MINUTES', default=1)

# ─── Brand ────────────────────────────────────────────────────
BRAND_NAME = 'CHRONOS'
BRAND_TAGLINE = 'Precision. Elegance. Legacy.'
SITE_URL = clean_env('SITE_URL', default='http://localhost:8000')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
