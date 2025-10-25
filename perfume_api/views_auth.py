import random
import json
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
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
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"message": "Correo requerido"}, status=400)

            code = str(random.randint(10000, 99999))
            codes[email] = {"code": code, "timestamp": timezone.now()}

            send_mail(
                subject="Código de verificación",
                message=f"Tu código de verificación es: {code}",
                from_email="tu_correo@gmail.com",
                recipient_list=[email],
                fail_silently=False,
            )
            return JsonResponse({"message": "Código enviado"})
        except Exception as e:
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)

#fdfjkdj

@csrf_exempt
def verify_code(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            code = data.get("code")

            if email in codes and codes[email]["code"] == code:
                return JsonResponse({"message": "Código válido"})
            return JsonResponse({"message": "Código inválido"}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)


@csrf_exempt
def create_cliente(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if email not in codes:
                return JsonResponse({"message": "Código no verificado"}, status=400)

            if Usuario.objects.filter(email=email).exists():
                return JsonResponse({"message": "El usuario ya existe"}, status=400)

            # ✅ Crear usuario sin username
            usuario = Usuario.objects.create_user(
                email=email,
                password=data.get("password"),
                rol="cliente"
            )

            # ✅ Crear cliente asociado
            cliente = Cliente.objects.create(
                nombre=data.get("nombre", "SinNombre"),
                apellido=data.get("apellido", "Cliente"),
                cedula=data.get("cedula", str(random.randint(1000000000, 9999999999))),
                direccion=data.get("direccion", ""),
                celular=data.get("celular", ""),
                email=email,
                sexo=data.get("sexo", "Hombre"),
                password=usuario.password,
                email_verified_at=timezone.now()
            )

            return JsonResponse({"message": "Cliente creado", "id": cliente.id})

        except Exception as e:
            print("⚠️ ERROR create_cliente:", str(e))
            return JsonResponse({"message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Método no permitido"}, status=405)
