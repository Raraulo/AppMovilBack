# perfumeria/settings_production.py
from .settings import *
import os
import dj_database_url


# ⚠️ Seguridad en producción
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', SECRET_KEY)


# Hosts permitidos
ALLOWED_HOSTS = ['*']


# ✅ Base de datos PostgreSQL (Railway)
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}


# Archivos estáticos con WhiteNoise
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Agregar WhiteNoise al middleware
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')


# CORS
CORS_ALLOW_ALL_ORIGINS = True


# CSRF para Railway
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ===== 📧 EMAIL CONFIGURATION (Gmail con SSL para Railway) ===== 
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465  # ✅ Puerto SSL
EMAIL_USE_SSL = True  # ✅ Usar SSL
EMAIL_USE_TLS = False  # ✅ Desactivar TLS
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'maisondeparfumsprofesional@gmail.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 30
