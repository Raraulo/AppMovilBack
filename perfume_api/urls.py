# perfume_api/urls.py
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
    procesar_venta,
    obtener_facturas_usuario,
    password_reset_request,
    password_reset_verify,
    password_reset_confirm,
    admin_factura_pdf,
    send_verification_code,  # ✅ NUEVO
    verify_email_code,       # ✅ NUEVO
)
from . import views_auth
from . import dashboard_views  # ✅ IMPORTAR DASHBOARD


# ==================== ROUTER CON VIEWSETS ====================
router = routers.DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuarios")
router.register("marcas", MarcaViewSet)
router.register("tipos", TipoViewSet)
router.register("productos", ProductoViewSet)
router.register("facturas", FacturaViewSet)
router.register("detalles", DetalleFacturaViewSet)
router.register("clientes", ClienteViewSet)


# ==================== URLS PRINCIPALES ====================
urlpatterns = [
    # ✅ DASHBOARD PERSONALIZADO (debe ir ANTES de las rutas del router)
    path("admin/dashboard/", dashboard_views.custom_dashboard, name="custom_dashboard"),
    
    # 📄 VER PDF DESDE ADMIN
    path("admin/factura/<int:factura_id>/pdf/", admin_factura_pdf, name="admin_factura_pdf"),
    
] + router.urls + [
    
    # ==================== PRODUCTOS ====================
    path("productos/marca/<int:marca_id>/", productos_por_marca, name="productos_por_marca"),
    
    # ==================== FAVORITOS Y CARRITO ====================
    path("favoritos/agregar/", agregar_a_favoritos, name="agregar_a_favoritos"),
    path("carrito/agregar/", agregar_a_carrito, name="agregar_a_carrito"),
    
    # ==================== VERIFICACIÓN DE EMAIL (NUEVO REGISTRO) ✅ NUEVO ====================
    path("auth/send-verification-code/", send_verification_code, name="send_verification_code"),
    path("auth/verify-email-code/", verify_email_code, name="verify_email_code"),
    
    # ==================== AUTENTICACIÓN CON CÓDIGO ====================
    path("auth/send-code/", views_auth.send_code, name="send_code"),
    path("auth/verify-code/", views_auth.verify_code, name="verify_code"),
    path("auth/create-cliente/", views_auth.create_cliente, name="create_cliente"),
    
    # ==================== CLIENTES ====================
    path("clientes/secure/<int:pk>/", get_cliente, name="get_cliente"),
    path("clientes/secure/update/<int:pk>/", update_cliente, name="update_cliente"),
    
    # ==================== VENTAS ====================
    path("ventas/procesar/", procesar_venta, name="procesar_venta"),
    
    # ==================== FACTURAS ====================
    path("usuarios/<int:usuario_id>/facturas/", obtener_facturas_usuario, name="obtener_facturas_usuario"),
    
    # ==================== RECUPERACIÓN DE CONTRASEÑA ====================
    path("password-reset/request/", password_reset_request, name="password_reset_request"),
    path("password-reset/verify/", password_reset_verify, name="password_reset_verify"),
    path("password-reset/confirm/", password_reset_confirm, name="password_reset_confirm"),
]
