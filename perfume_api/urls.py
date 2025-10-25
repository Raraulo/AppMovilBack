from rest_framework import routers
from django.urls import path
from .views import (
    UsuarioViewSet,
    MarcaViewSet,
    TipoViewSet,
    ProductoViewSet,
    FacturaViewSet,
    DetalleFacturaViewSet,
    ClienteViewSet,
    productos_por_marca,
    agregar_a_favoritos,
    agregar_a_carrito,
    get_cliente,
    update_cliente,
)
from . import views_auth

# 🔹 Router con todos los ViewSets
router = routers.DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuarios")
router.register("marcas", MarcaViewSet)
router.register("tipos", TipoViewSet)
router.register("productos", ProductoViewSet)
router.register("facturas", FacturaViewSet)
router.register("detalles", DetalleFacturaViewSet)
router.register("clientes", ClienteViewSet)

urlpatterns = router.urls + [
    # 📦 Productos
    path("productos/marca/<int:marca_id>/", productos_por_marca, name="productos_por_marca"),

    # ❤️ Favoritos y 🛒 Carrito
    path("favoritos/agregar/", agregar_a_favoritos, name="agregar_a_favoritos"),
    path("carrito/agregar/", agregar_a_carrito, name="agregar_a_carrito"),

    # 🔐 Autenticación con código
    path("auth/send-code", views_auth.send_code, name="send_code"),
    path("auth/verify-code", views_auth.verify_code, name="verify_code"),
    path("auth/create-cliente", views_auth.create_cliente, name="create_cliente"),

    # 👤 Endpoints de Cliente adicionales (rutas distintas para no duplicar)
    path("clientes/secure/<int:pk>/", get_cliente, name="get_cliente"),
    path("clientes/secure/update/<int:pk>/", update_cliente, name="update_cliente"),
]
