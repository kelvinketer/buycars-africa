from pathlib import Path
from decouple import config
import os
import dj_database_url 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-replace-me-please')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*'] 

# --- CRITICAL FIX FOR RENDER FORMS ---
CSRF_TRUSTED_ORIGINS = [
    'https://buycars-africa.onrender.com',
]

# Application definition
INSTALLED_APPS = [
    # --- CLOUDINARY APPS (Must be at the top) ---
    'cloudinary_storage',
    'cloudinary',
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # --- UTILITIES ---
    'django.contrib.humanize',

    # Third Party Apps
    'rest_framework', 

    # Local Apps
    'users.apps.UsersConfig',   
    'cars.apps.CarsConfig',     
    'saas.apps.SaasConfig',
    'payments', # Payment App
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Critical for Static Files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'buycars_project.urls'

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

WSGI_APPLICATION = 'buycars_project.wsgi.application'

# --- DATABASE CONFIGURATION ---
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///' + str(BASE_DIR / 'db.sqlite3')),
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi' 
USE_I18N = True
USE_TZ = True

# --- STATIC FILES (CSS/JS - Managed by WhiteNoise) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# --- MEDIA FILES (Images - Managed by Cloudinary) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Configuration
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

# --- STORAGE CONFIGURATION (Django 5.0+ Standard) ---
STORAGES = {
    # UPDATED: Use Standard Django Storage (SAFE MODE)
    # This disables WhiteNoise compression during build to prevent crashes.
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    # Images stored on Cloudinary
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
}

# --- LEGACY SETTING (CRITICAL FIX) ---
# Must match the backend above.
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'


# --- AUTH SETTINGS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

LOGIN_REDIRECT_URL = 'dealer_dashboard'
LOGOUT_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

# --- EMAIL CONFIGURATION ---
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'BuyCars Africa <noreply@buycars.africa>'

# ========================================================
#             M-PESA DARAJA API CONFIGURATION
# ========================================================
# 1. ENVIRONMENT ('sandbox' for testing, 'production' for live)
MPESA_ENVIRONMENT = config('MPESA_ENVIRONMENT', default='sandbox')

# 2. API KEYS (Get these from Daraja Portal)
MPESA_CONSUMER_KEY = config('MPESA_CONSUMER_KEY', default='YOUR_SANDBOX_KEY')
MPESA_CONSUMER_SECRET = config('MPESA_CONSUMER_SECRET', default='YOUR_SANDBOX_SECRET')

# 3. IDENTIFIERS (Till vs Store Number)
# MPESA_SHORTCODE = Your 'Store Number' (Used for Password Generation & Auth)
# Sandbox Default: 174379. Live: 9424318
MPESA_SHORTCODE = config('MPESA_SHORTCODE', default='174379')

# MPESA_TILL_NUMBER = Your 'Till Number' (Where money is sent - PartyB)
# Sandbox Default: 174379. Live: 7155132
MPESA_TILL_NUMBER = config('MPESA_TILL_NUMBER', default='174379')

# Passkey (Sandbox default provided; Production comes via Email)
MPESA_PASSKEY = config('MPESA_PASSKEY', default='bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')

# 4. TRANSACTION TYPE (CRITICAL SWITCH)
# Sandbox Default: 'CustomerPayBillOnline'
# Live Default (For Till): 'CustomerBuyGoodsOnline'
MPESA_TRANSACTION_TYPE = config('MPESA_TRANSACTION_TYPE', default='CustomerPayBillOnline')

# 5. URLS
if MPESA_ENVIRONMENT == 'production':
    MPESA_ACCESS_TOKEN_URL = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    MPESA_EXPRESS_URL = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
else:
    MPESA_ACCESS_TOKEN_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
    MPESA_EXPRESS_URL = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'

# 6. CALLBACK URL (Must be your LIVE Render URL)
MPESA_CALLBACK_URL = config('MPESA_CALLBACK_URL', default='https://buycars-africa.onrender.com/payments/callback/')

# --- AFRICA'S TALKING SMS CONFIGURATION ---
AFRICASTALKING_USERNAME = config('AFRICASTALKING_USERNAME', default='sandbox')
AFRICASTALKING_API_KEY = config('AFRICASTALKING_API_KEY', default='')