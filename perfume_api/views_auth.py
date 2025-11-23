# perfume_api/views_auth.py
import random
import json
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rolepermissions.roles import get_user_roles
from perfume_api.models import Cliente, Usuario


# =========================
# 🔹 LOGIN CON JWT + ROLES
# =========================
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        # Autenticación por email
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("❌ Credenciales incorrectas")

        refresh = RefreshToken.for_user(user)

        permisos = []
        for role in get_user_roles(user):
            permisos.extend(list(role.available_permissions.keys()))

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "id": user.id,
            "email": user.email,
            "rol": user.rol,
            "permisos": permisos
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# =========================
# 🔹 REGISTRO CON CÓDIGO
# =========================
codes = {}


@csrf_exempt
def send_code(request):
    """
    📧 Envía código de verificación
    POST /api/auth/send-code/
    Body: {"email": "usuario@example.com"}
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"message": "Correo requerido"}, status=400)

            # Generar código de 6 dígitos
            code = str(random.randint(100000, 999999))
            codes[email] = {"code": code, "timestamp": timezone.now()}

            print(f"📧 Código generado para {email}: {code}")

            # Enviar email
            send_mail(
                subject="Código de verificación - Maison Des Senteurs",
                message=f"Tu código de verificación es: {code}\n\nEste código expira en 10 minutos.",
                from_email="maisondeparfumsprofesional@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
            
            return JsonResponse({"message": "Código enviado exitosamente"}, status=200)
            
        except Exception as e:
            print(f"❌ Error enviando código: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)


@csrf_exempt
def verify_code(request):
    """
    ✅ Verifica código de verificación
    POST /api/auth/verify-code/
    Body: {"email": "usuario@example.com", "code": "123456"}
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            code = data.get("code")

            if not email or not code:
                return JsonResponse(
                    {"message": "Email y código son requeridos"}, 
                    status=400
                )

            # Verificar que existe el código
            if email not in codes:
                return JsonResponse(
                    {"message": "No se encontró código para este email"}, 
                    status=404
                )

            # Verificar que el código coincida
            if codes[email]["code"] != code:
                return JsonResponse(
                    {"message": "Código inválido"}, 
                    status=400
                )

            # Verificar que no haya expirado (10 minutos)
            timestamp = codes[email]["timestamp"]
            if (timezone.now() - timestamp).seconds > 600:
                del codes[email]
                return JsonResponse(
                    {"message": "Código expirado"}, 
                    status=400
                )

            print(f"✅ Código verificado para {email}")

            # ✅ Buscar si ya existe el cliente
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
            print(f"❌ Error verificando código: {str(e)}")
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)


@csrf_exempt
def create_cliente(request):
    """
    👤 Crea nuevo cliente
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
            email = data.get("email")

            # Verificar que el código fue validado
            if email not in codes:
                return JsonResponse(
                    {"message": "Código no verificado. Verifica el código primero."}, 
                    status=400
                )

            # Verificar si el usuario ya existe
            if Usuario.objects.filter(email=email).exists():
                return JsonResponse(
                    {"message": "El usuario ya existe"}, 
                    status=400
                )

            # ✅ Crear usuario
            usuario = Usuario.objects.create_user(
                email=email,
                password=data.get("password"),
                rol="cliente"
            )

            print(f"✅ Usuario creado: {usuario.email}")

            # ✅ Crear cliente asociado
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

            print(f"✅ Cliente creado: {cliente.nombre} {cliente.apellido}")

            # Eliminar código usado
            del codes[email]

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
            print(f"❌ Error creando cliente: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)
