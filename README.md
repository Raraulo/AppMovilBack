# AppMovilBack

Backend desarrollado con **Django** y **Django REST Framework** para una aplicación móvil de perfumería. Proporciona una API REST para la gestión de usuarios, clientes, productos, ventas, facturación, autenticación y administración del sistema.

---

## Table of Contents

- Overview
- Features
- Technology Stack
- Project Structure
- Data Models
- API Endpoints
- Installation
- Environment Variables
- Deployment
- Project Highlights

---

# Overview

AppMovilBack es el backend de una aplicación móvil de perfumería. La API permite administrar el catálogo de productos, gestionar clientes, procesar ventas, generar facturas y ofrecer autenticación segura mediante JWT.

El proyecto está preparado tanto para desarrollo local como para despliegue en producción.

---

# Features

### Authentication

- Email authentication
- JWT Authentication
- Refresh Tokens
- Email verification
- Password recovery
- Role-based authorization

### User Roles

- Administrator
- Employee
- Customer

### Product Management

- Brands
- Perfume categories
- Products
- Inventory management
- Stock validation

### Sales

- Sales processing
- Invoice generation
- PDF invoices
- Email delivery

### Administration

- Django Admin
- Administrative Dashboard
- Sales statistics
- Customer metrics
- Product metrics

---

# Technology Stack

| Category | Technologies |
|-----------|-------------|
| Language | Python |
| Framework | Django 4.2 |
| API | Django REST Framework |
| Authentication | Simple JWT |
| Database (Development) | MySQL |
| Database (Production) | PostgreSQL / Supabase |
| Static Files | WhiteNoise |
| WSGI Server | Gunicorn |
| PDF Generation | ReportLab |
| Email Service | Resend |
| Data Analysis | Pandas |
| Charts | Plotly |
| Frontend Assets | Tailwind CSS |

---

# Project Structure

```text
AppMovilBack/
│
├── manage.py
├── requirements.txt
├── package.json
├── build.sh
├── Procfile
├── nixpacks.toml
│
├── perfumeria/
│   ├── settings.py
│   ├── settings_production.py
│   ├── urls.py
│   └── wsgi.py
│
├── perfume_api/
│   ├── admin.py
│   ├── dashboard_views.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── views.py
│   └── views_auth.py
│
├── static/
└── assets/
```

---

# Data Models

| Model | Description |
|--------|-------------|
| Usuario | Custom user model |
| Cliente | Customer information |
| Marca | Perfume brands |
| Tipo | Perfume categories |
| Producto | Products available for sale |
| Factura | Sales invoice |
| DetalleFactura | Invoice details |
| PasswordResetCode | Password recovery codes |
| EmailVerification | Email verification codes |

---

# API Endpoints

## Authentication

```http
POST /api/login/
POST /api/refresh/
POST /api/auth/send-code/
POST /api/auth/verify-code/
POST /api/auth/create-cliente/
POST /api/auth/check-user/
```

## Email Verification

```http
POST /api/auth/send-verification-code/
POST /api/auth/verify-email-code/
```

## Password Recovery

```http
POST /api/password-reset/request/
POST /api/password-reset/verify/
POST /api/password-reset/confirm/
```

## Resources

```http
/api/usuarios/
/api/clientes/
/api/productos/
/api/marcas/
/api/tipos/
/api/facturas/
/api/detalles/
```

## Sales

```http
GET  /api/productos/marca/<marca_id>/
POST /api/ventas/procesar/
GET  /api/usuarios/<usuario_id>/facturas/
```

## Administration

```http
/admin/
/api/admin/dashboard/
/api/admin/factura/<factura_id>/pdf/
```

---

# Installation

## Clone the repository

```bash
git clone <repository-url>
cd AppMovilBack
```

## Create a virtual environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

```bash
npm install
```

## Configure the database

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "perfumeria_db",
        "USER": "root",
        "PASSWORD": "root123",
        "HOST": "localhost",
        "PORT": "3306",
    }
}
```

## Apply migrations

```bash
python manage.py migrate
```

## Create a superuser

```bash
python manage.py createsuperuser
```

## Run the server

```bash
python manage.py runserver
```

## Compile Tailwind

```bash
npm run build:css
```

---

# Environment Variables

```env
SECRET_KEY=

DATABASE_URL=

RESEND_API_KEY=
```

---

# Deployment

The project is configured for deployment on Render.

Included configuration files:

- Procfile
- build.sh
- nixpacks.toml
- settings_production.py

### Build Command

```bash
./build.sh
```

### Start Command

```bash
gunicorn perfumeria.wsgi --workers 2 --threads 2 --timeout 120 --log-file -
```

---

# Project Highlights

- RESTful API
- JWT Authentication
- Role-based authorization
- Email verification
- Password recovery
- Inventory management
- Sales processing
- PDF invoice generation
- Email invoice delivery
- Administrative dashboard
- Development and production configuration

---

# Author

Backend developed for a mobile perfume store application using Django and Django REST Framework.
