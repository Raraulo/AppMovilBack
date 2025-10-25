# perfume_api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password

from .models import Usuario, Marca, Tipo, Producto, Factura, DetalleFactura, Cliente
from .serializers import (
    UsuarioSerializer,
    MarcaSerializer,
    TipoSerializer,
    ProductoSerializer,
    FacturaSerializer,
    DetalleFacturaSerializer,
    ClienteSerializer,
)

# ======================================================
# 🔹 VIEWSETS - CRUD Automático
# ======================================================

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer


class MarcaViewSet(viewsets.ModelViewSet):
    queryset = Marca.objects.all()
    serializer_class = MarcaSerializer


class TipoViewSet(viewsets.ModelViewSet):
    queryset = Tipo.objects.all()
    serializer_class = TipoSerializer


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer  # Público (lecturas permitidas por settings)


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer


class DetalleFacturaViewSet(viewsets.ModelViewSet):
    queryset = DetalleFactura.objects.all()
    serializer_class = DetalleFacturaSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    """
    - GET /api/clientes/           -> público (list)
    - GET /api/clientes/<id>/      -> público (retrieve)
    - POST/PUT/PATCH/DELETE        -> requieren autenticación
    """
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]  # default para acciones que no sean lectura

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

# ======================================================
# 🔹 ENDPOINTS PERSONALIZADOS
# ======================================================

@api_view(["GET"])
def productos_por_marca(request, marca_id):
    """📦 Devuelve productos filtrados por marca"""
    productos = Producto.objects.filter(marca_id=marca_id)
    serializer = ProductoSerializer(productos, many=True)
    return Response(serializer.data)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agregar_a_favoritos(request):
    """❤️ Agregar un producto a favoritos (lógica pendiente)"""
    producto_id = request.data.get("producto_id")
    return Response({"mensaje": f"Producto {producto_id} añadido a favoritos"})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agregar_a_carrito(request):
    """🛒 Agregar un producto al carrito (lógica pendiente)"""
    producto_id = request.data.get("producto_id")
    return Response({"mensaje": f"Producto {producto_id} añadido al carrito"})

# ======================================================
# 🔹 ENDPOINTS PARA CLIENTES (GET y PUT por ID)
# ======================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])  # 🔐 Requiere token
def get_cliente(request, pk):
    """📌 Obtiene un cliente por su ID (versión protegida)"""
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return Response({"message": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    serializer = ClienteSerializer(cliente)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(["PUT"])
@permission_classes([IsAuthenticated])  # 🔐 Requiere token
def update_cliente(request, pk):
    """✏️ Actualiza los datos de un cliente"""
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return Response({"message": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()

    # ✅ Si se envía nueva contraseña, la encriptamos
    if data.get("password"):
        data["password"] = make_password(data["password"])
    else:
        # Mantener la contraseña actual
        data["password"] = cliente.password

    serializer = ClienteSerializer(cliente, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
