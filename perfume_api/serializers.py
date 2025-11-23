from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Usuario, Marca, Tipo, Producto, Cliente, Factura, DetalleFactura


# ---------- SERIALIZERS USUARIO ----------
class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "email", "rol"]  # 🔹 Eliminamos username


# ---------- SERIALIZERS MARCA Y TIPO ----------
class MarcaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marca
        fields = "__all__"


class TipoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo
        fields = "__all__"


# ---------- SERIALIZER PRODUCTO (Incluye nombres de marca y tipo) ----------
class ProductoSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="tipo.nombre", read_only=True)  # 🔹 Debe coincidir con el modelo
    marca_nombre = serializers.CharField(source="marca.nombre", read_only=True)
    url_imagen = serializers.SerializerMethodField()  # ✅ Método seguro

    class Meta:
        model = Producto
        fields = [
            "id",
            "nombre",
            "descripcion",
            "precio",
            "url_imagen",
            "stock",
            "genero",
            "created_at",
            "updated_at",
            "marca",
            "marca_nombre",
            "tipo",
            "tipo_nombre",
        ]

    def get_url_imagen(self, obj):
        """Devuelve URL de imagen o None si no existe"""
        if obj.imagen and hasattr(obj.imagen, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.imagen.url)
            return obj.imagen.url
        return None

    def validate_precio(self, value):
        if value <= 0:
            raise serializers.ValidationError("El precio debe ser mayor a 0.")
        return value

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError("El stock no puede ser negativo.")
        return value


# ---------- SERIALIZER CLIENTE (Crear y Editar) ----------
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True},
            "email": {"required": True},
        }

    def create(self, validated_data):
        # Encripta la contraseña antes de guardar
        if "password" in validated_data:
            validated_data["password"] = make_password(validated_data["password"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Si hay una nueva contraseña, la encripta
        if "password" in validated_data and validated_data["password"]:
            validated_data["password"] = make_password(validated_data["password"])
        else:
            validated_data["password"] = instance.password  # Mantener la anterior

        return super().update(instance, validated_data)


# ---------- FACTURA Y DETALLES ----------
class FacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Factura
        fields = "__all__"


class DetalleFacturaSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleFactura
        fields = "__all__"


# ---------- REGISTRO DE USUARIOS Y EMPLEADOS ----------
class RegistroUsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "email", "password", "rol"]  # 🔹 Sin username
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        if "rol" not in validated_data:
            validated_data["rol"] = "cliente"
        return super().create(validated_data)


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "email", "password", "rol"]  # 🔹 Sin username
        extra_kwargs = {
            "password": {"write_only": True},
            "rol": {"read_only": True},
        }

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        validated_data["rol"] = "empleado"
        return super().create(validated_data)
