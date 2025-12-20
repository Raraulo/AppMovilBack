# perfume_api/views_auth.py
import random
import json
from threading import Thread
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password, check_password
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rolepermissions.roles import get_user_roles
from perfume_api.models import Cliente, Usuario


# =========================
# 🔹 LOGIN CON JWT + ROLES (MEJORADO)
# =========================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # Verificar si el usuario existe
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({
                "detail": "Este correo no está registrado",
                "code": "user_not_found"
            })

        # Verificar si la contraseña es correcta
        if not check_password(password, user.password):
            raise serializers.ValidationError({
                "detail": "Contraseña incorrecta",
                "code": "invalid_password"
            })

        # Generar tokens
        refresh = RefreshToken.for_user(user)

        permisos = []
        for role in get_user_roles(user):
            permisos.extend(list(role.available_permissions.keys()))

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "id": user.id,
            "email": user.email,
            "username": user.email.split('@')[0],
            "rol": user.rol,
            "permisos": permisos
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# =========================
# 🔹 VERIFICAR SI USUARIO EXISTE (NUEVO)
# =========================
@csrf_exempt
def check_user_exists(request):
    """
    Verifica si un usuario existe sin exponer información sensible
    POST /api/check-user/
    Body: {"email": "usuario@example.com"}
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip().lower()
            
            if not email:
                return JsonResponse({'exists': False}, status=200)
            
            user_exists = Usuario.objects.filter(email=email).exists()
            
            return JsonResponse({'exists': user_exists}, status=200)
            
        except Exception as e:
            print(f"Error verificando usuario: {str(e)}")
            return JsonResponse({'exists': False}, status=200)
    
    return JsonResponse({"message": "Método no permitido"}, status=405)


# =========================
# 🔹 REGISTRO - MODO DESARROLLO (SIN VALIDACIÓN DE EMAIL)
# =========================
codes = {}


@csrf_exempt
def send_code(request):
    """
    📧 [MODO DEV] Registra email sin enviar código
    POST /api/auth/send-code/
    Body: {"email": "usuario@example.com"}
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip().lower()

            if not email:
                return JsonResponse({"message": "Correo requerido"}, status=400)

            # MODO DESARROLLO: Auto-aprobar sin enviar email
            code = "000000"  # Código fijo para desarrollo
            codes[email] = {"code": code, "timestamp": timezone.now()}

            print(f"[MODO DEV] Email registrado: {email} (sin envío de correo)")

            # RESPONDER INMEDIATAMENTE
            return JsonResponse({
                "message": "Código enviado correctamente",
                "email": email
            }, status=200)
            
        except Exception as e:
            print(f"Error generando código: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)


@csrf_exempt
def verify_code(request):
    """
    ✅ [MODO DEV] Verifica email sin validar código real
    POST /api/auth/verify-code/
    Body: {"email": "usuario@example.com", "code": "123456"}
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip().lower()
            code = data.get("code", "").strip()

            if not email:
                return JsonResponse(
                    {"message": "Email es requerido"}, 
                    status=400
                )

            # MODO DESARROLLO: Aprobar automáticamente
            print(f"[MODO DEV] Código verificado automáticamente para {email}")

            # Buscar si ya existe el cliente
            try:
                cliente = Cliente.objects.get(email=email)
                return JsonResponse({
                    "message": "Código válido - Cliente existente",
                    "cliente_exists": True,
                    "cliente": {
                        "id": cliente.id,
                        "nombre": cliente.nombre,
                        "apellido": cliente.apellido,
                        "email": cliente.email,
                        "celular": cliente.celular,
                        "sexo": cliente.sexo,
                    }
                }, status=200)
            except Cliente.DoesNotExist:
                return JsonResponse({
                    "message": "Código válido - Cliente nuevo",
                    "cliente_exists": False
                }, status=200)

        except Exception as e:
            print(f"Error verificando código: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)


@csrf_exempt
def create_cliente(request):
    """
    👤 [MODO DEV] Crea cliente sin validar código
    POST /api/auth/create-cliente/
    Body: {
        "email": "usuario@example.com",
        "password": "contraseña123",
        "nombre": "Juan",
        "apellido": "Pérez",
        "cedula": "1234567890",
        "celular": "0999999999",
        "direccion": "Av. Principal 123",
        "sexo": "Hombre"
    }
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email", "").strip().lower()

            # Verificar si el usuario ya existe
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse(
                    {"message": "El usuario ya existe"}, 
                    status=400
                )

            # Crear usuario
            usuario = Usuario.objects.create_user(
                email=email,
                password=data.get("password"),
                rol="cliente"
            )

            print(f"Usuario creado: {usuario.email}")

            # Crear cliente asociado
            cliente = Cliente.objects.create(
                nombre=data.get("nombre", "Cliente"),
                apellido=data.get("apellido", "Nuevo"),
                cedula=data.get("cedula", str(random.randint(1000000000, 9999999999))),
                direccion=data.get("direccion", ""),
                celular=data.get("celular", ""),
                email=email,
                sexo=data.get("sexo", "Hombre"),
                password=make_password(data.get("password")),
                email_verified_at=timezone.now()
            )

            print(f"Cliente creado: {cliente.nombre} {cliente.apellido}")

            return JsonResponse({
                "message": "Cliente creado exitosamente",
                "cliente": {
                    "id": cliente.id,
                    "nombre": cliente.nombre,
                    "apellido": cliente.apellido,
                    "email": cliente.email,
                }
            }, status=201)

        except Exception as e:
            print(f"Error creando cliente: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)
