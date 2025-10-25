from pathlib import Path
import os

# 📂 BASE_DIR: Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔑 Llave secreta (NO usar esta en producción)
SECRET_KEY = 'django-insecure-b*o&%slu&o6s2ojwv--zt%71_h%wp+@i&jhf!!@yhx=8=322fh'

# ⚠️ En producción, pon DEBUG = False
DEBUG = True

# 🌍 Permitir todas las IPs en desarrollo
ALLOWED_HOSTS = [
    "*",
    # Aunque ALLOWED_HOSTS="*" permite todo, se recomienda añadir tu dominio Ngrok específico:
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
    'rest_framework',           # API REST
    'corsheaders',              # Permitir CORS
    'rolepermissions',          # Manejo de roles y permisos
    'django_filters',           # Filtros avanzados en API
    'perfume_api',              # Tu aplicación principal
]

# 🔹 Middleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",    # CORS debe estar antes de CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'perfumeria.urls'

# 🎨 Configuración de plantillas (si usas Django Templates)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
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
        'NAME': 'perfumeria_db',            # Nombre de tu BD
        'USER': 'root',                     # Usuario
        'PASSWORD': 'root123',              # Contraseña
        'HOST': 'localhost',                # O la IP del servidor MySQL
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
# Si quieres restringir, usa:
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:19006",
#     "http://127.0.0.1:19006",
# ]

# ** 🔑 CONFIGURACIÓN NECESARIA PARA NGROK (CSRF) **
# ESTO RESUELVE EL ERROR 403 (Prohibido)
# -----------------------------------------------------
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    # 1. URL ESPECÍFICA de tu sesión Ngrok actual
    'https://suanne-unamortized-denae.ngrok-free.dev', 
    # 2. Patrón con comodín para futuras sesiones de Ngrok (plan gratuito)
    'https://*.ngrok-free.dev' 
]
# -----------------------------------------------------
# ** FIN CONFIGURACIÓN NGROK **

# 🌎 Configuración de idioma y zona horaria
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Guayaquil'
USE_I18N = True
USE_TZ = True

# 📂 Archivos estáticos
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]

# 📂 Archivos multimedia
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 🔑 Campo por defecto para IDs automáticas
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ⚙️ Configuración de Django REST Framework con JWT
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
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

# 📧 Configuración de Email (para enviar códigos)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "maisondeparfumsprofesional@gmail.com" 
EMAIL_HOST_PASSWORD = "tdlj byrx fnbo htcv"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",    # Mantiene autenticación normal
    "perfume_api.backends.EmailBackend",            # 🔹 Usar email para login
]

# (El siguiente bloque es redundante, lo mantengo por si acaso, pero el anterior es el que se usa)
# AUTHENTICATION_BACKENDS = [
#     'django.contrib.auth.backends.ModelBackend',    # Mantener compatibilidad
#     'perfume_api.backends.EmailBackend',  # Nuestro backend personalizado
# ] 