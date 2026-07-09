#!/usr/bin/env bash
# build.sh — Script de build para Render
# Configúralo en Render como: Build Command -> ./build.sh

set -o errexit  # Detener si hay un error

echo "==> Instalando dependencias..."
pip install -r requirements.txt

echo "==> Recolectando archivos estáticos..."
python manage.py collectstatic --no-input --settings=perfumeria.settings_production

echo "==> Aplicando migraciones..."
python manage.py migrate --settings=perfumeria.settings_production

echo "==> Creando superusuario si no existe..."
python manage.py shell --settings=perfumeria.settings_production <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='admin@admin.com').exists():
    print('Creando superusuario...')
    User.objects.create_superuser('admin@admin.com', 'admin123', nombre='Admin', apellido='Admin')
else:
    print('El superusuario ya existe.')
EOF

echo "==> Build completado ✅"
