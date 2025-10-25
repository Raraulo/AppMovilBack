from django.contrib import admin
from .models import Usuario, Producto, Cliente, Factura, DetalleFactura, Marca, Tipo

admin.site.site_header = "Maison de Parfums"
admin.site.site_title = "Panel de Administración"
admin.site.index_title = "Sitio administrativo"

# ---------- USUARIO ----------
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "rol", "is_staff", "is_active")
    search_fields = ("email",)
    list_filter = ("rol", "is_staff", "is_active")
    list_editable = ("rol", "is_staff", "is_active")


# ---------- PRODUCTO ----------
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "precio", "stock", "genero", "marca", "tipo")
    search_fields = ("nombre", "descripcion")
    list_filter = ("genero", "marca", "tipo")
    list_editable = ("precio", "stock", "genero", "marca", "tipo")
    list_display_links = ("id", "nombre")


# ---------- CLIENTE ----------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "apellido", "email", "celular", "cedula")
    search_fields = ("nombre", "apellido", "email", "cedula")


# ---------- FACTURA ----------
@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "fecha", "total")
    search_fields = ("cliente__nombre",)
    list_filter = ("fecha",)


# ---------- DETALLE FACTURA ----------
@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = ("id", "factura", "producto", "cantidad", "precio_unitario", "subtotal")
    search_fields = ("producto__nombre", "factura__cliente__nombre")


# ---------- MARCA ----------
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "logo")
    search_fields = ("nombre",)


# ---------- TIPO ----------
@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)
