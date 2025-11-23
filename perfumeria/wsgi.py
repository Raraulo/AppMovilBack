# perfumeria/wsgi.py
"""
WSGI config for perfumeria project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# ✅ Detectar si estamos en Railway o en desarrollo local
# Railway establece automáticamente estas variables de entorno
if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('DATABASE_URL'):
    # Estamos en Railway (producción)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfumeria.settings_production')
else:
    # Estamos en desarrollo local
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfumeria.settings')

application = get_wsgi_application()
