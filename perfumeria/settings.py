# perfumeria/settings.py
from pathlib import Path
import os
from datetime import timedelta


# 📂 BASE_DIR: Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent


# 🔑 Llave secreta (cargada desde variable de entorno en producción)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-b*o&%slu&o6s2ojwv--zt%71_h%wp+@i&jhf!!@yhx=8=322fh')


# ⚠️ En producción, pon DEBUG = False
DEBUG = True


# 🌍 Permitir todas las IPs en desarrollo
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    'suanne-unamortized-denae.ngrok-free.dev'
]


# 📦 Aplicaciones instaladas
INSTALLED_APPS = [
    # Apps de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps adicionales
    'rest_framework',
    'corsheaders',
    'rolepermissions',
    'django_filters',
    'django_extensions',
    
    # Tu app
    'perfume_api',
]


# 🔹 Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = 'perfumeria.urls'


# 🎨 Configuración de plantillas
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "templates",
            BASE_DIR / "perfume_api" / "templates",
        ],
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


WSGI_APPLICATION = 'perfumeria.wsgi.application'


# 📦 Configuración de la base de datos MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'perfumeria_db',
        'USER': 'root',
        'PASSWORD': 'root123',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}


# 🔐 Modelo de usuario personalizado
AUTH_USER_MODEL = 'perfume_api.Usuario'


# 🌍 CORS (para React Native / Expo)
CORS_ALLOW_ALL_ORIGINS = True


# 🔑 CONFIGURACIÓN CSRF PARA NGROK
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'https://suanne-unamortized-denae.ngrok-free.dev',
    'https://*.ngrok-free.dev'
]


# 🌎 Configuración de idioma y zona horaria
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = False


# 📂 Archivos estáticos
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ✅ SOLO incluir directorios que existan
STATICFILES_DIRS = [
    BASE_DIR / "static",
]


# 📂 Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# 🔑 Campo por defecto para IDs automáticas
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ⚙️ Configuración de Django REST Framework con JWT
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
}


# ⏱️ Configuración de JWT (Simple JWT)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# ===== 📧 EMAIL CONFIGURATION (Resend SMTP) ===== 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY', '')
DEFAULT_FROM_EMAIL = 'onboarding@resend.dev'
SERVER_EMAIL = 'onboarding@resend.dev'
EMAIL_TIMEOUT = 30


# 🔐 Backends de autenticación
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "perfume_api.backends.EmailBackend",
]
