# perfumeria/settings_production.py
from .settings import *
import os
import dj_database_url


# ⚠️ Seguridad en producción
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("La variable de entorno SECRET_KEY es obligatoria en producción")


# Hosts permitidos (Render genera subdominios en .onrender.com)
ALLOWED_HOSTS = [
    '.onrender.com',
    'localhost',
    '127.0.0.1',
]


# ✅ Base de datos PostgreSQL (Supabase Transaction Pooler - puerto 6543)
# IMPORTANTE: conn_max_age=0 porque el Transaction Pooler (PgBouncer) 
# no soporta conexiones persistentes entre requests
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=0,
        conn_health_checks=False,
        ssl_require=True,
    )
}


# Archivos estáticos con WhiteNoise
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# WhiteNoise ya está en MIDDLEWARE desde settings.py — no duplicar
# (settings.py ya incluye 'whitenoise.middleware.WhiteNoiseMiddleware')


# CORS — Permitir todos los orígenes (para app móvil React Native)
CORS_ALLOW_ALL_ORIGINS = True


# CSRF para Render
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.ngrok-free.dev',
]


# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# ===== 📧 EMAIL CONFIGURATION (Resend) =====
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.resend.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'resend'
EMAIL_HOST_PASSWORD = os.environ.get('RESEND_API_KEY')
DEFAULT_FROM_EMAIL = 'onboarding@resend.dev'
SERVER_EMAIL = 'onboarding@resend.dev'
EMAIL_TIMEOUT = 30


# ===== 🔐 SEGURIDAD ADICIONAL PARA PRODUCCIÓN =====
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
