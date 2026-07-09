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

echo "==> Build completado ✅"
