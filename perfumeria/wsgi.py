# perfumeria/wsgi.py
"""
WSGI config for perfumeria project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# ✅ Si DJANGO_SETTINGS_MODULE ya está seteado (Render lo hace via variable de entorno),
# lo respeta. Si no, detecta si hay DATABASE_URL (producción genérica) o usa desarrollo local.
if not os.environ.get('DJANGO_SETTINGS_MODULE'):
    if os.environ.get('DATABASE_URL') or os.environ.get('RENDER'):
        # Estamos en Render (producción)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfumeria.settings_production')
    else:
        # Estamos en desarrollo local
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'perfumeria.settings')

application = get_wsgi_application()
