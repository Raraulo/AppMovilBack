# perfume_api/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth.models import Group
# Importaciones necesarias para el cálculo del total
from django.db.models import Sum, F 
from django.forms import BaseInlineFormSet 
from decimal import Decimal

from .models import Usuario, Producto, Cliente, Factura, DetalleFactura, Marca, Tipo, PasswordResetCode

# ==================== CONSTANTES ====================
IVA_RATE = Decimal('0.15')
IVA_FACTOR = Decimal('1.15')

# ==================== PERSONALIZACIÓN DEL ADMIN ====================
admin.site.site_header = "Maison Des Senteurs - Administración"
admin.site.site_title = "Admin Perfumería"
admin.site.index_title = "Panel de Control"

# ✅ Desregistrar el modelo Group
try:
    admin.site.unregister(Group)
except:
    pass

# ==================== INLINE CUSTOM FORMSET ====================
class DetalleFacturaFormSet(BaseInlineFormSet):
    """
    FormSet personalizado para calcular el precio_unitario (sin IVA) 
    y el subtotal antes de guardar el DetalleFactura.
    """
    def save_new(self, form, commit=True):
        instance = form.save(commit=False)
        
        producto = instance.producto
        cantidad = instance.cantidad or 0
        
        if producto and cantidad > 0:
            # 1. Obtener el precio de venta (guardado en el modelo Producto, incluye IVA)
            precio_con_iva = Decimal(str(producto.precio))
            
            # 2. Calcular el Precio Unitario (sin IVA)
            # precio_unitario se guardará en DetalleFactura como el precio base.
            precio_sin_iva = precio_con_iva / IVA_FACTOR
            
            # 3. Calcular el Subtotal (sin IVA)
            # El subtotal es precio_sin_iva * cantidad
            subtotal_sin_iva = precio_sin_iva * Decimal(str(cantidad))
            
            # Asignar los valores calculados
            instance.precio_unitario = precio_sin_iva.quantize(Decimal('0.00')) 
            instance.subtotal = subtotal_sin_iva.quantize(Decimal('0.00')) 
        else:
            instance.precio_unitario = Decimal('0.00')
            instance.subtotal = Decimal('0.00')
            
        if commit:
            instance.save()
            
        return instance

# ==================== INLINE PARA FACTURA ====================
# Definir el Inline para los detalles de la factura
class DetalleFacturaInline(admin.TabularInline):
    model = DetalleFactura
    extra = 1
    formset = DetalleFacturaFormSet # Usamos el formset personalizado
    # precio_unitario es ahora el precio sin IVA.
    fields = ('producto', 'cantidad', 'precio_unitario', 'subtotal') 
    readonly_fields = ('precio_unitario', 'subtotal',) # ¡Ahora son de solo lectura!

# ==================== USUARIO ====================
@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'email',
        'nombre_completo',
        'rol_badge',
        'estado_badge',
    ]
    search_fields = ['email', 'nombre', 'apellido']
    list_filter = ['rol', 'is_staff', 'is_active']
    readonly_fields = ['id']
    ordering = ['-id']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'email', 'direccion', 'celular')
        }),
        ('Permisos', {
            'fields': ('rol', 'is_staff', 'is_active'),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Nombre Completo'
    
    def rol_badge(self, obj):
        colores = {
            'admin': '#EF4444',
            'cliente': '#10B981',
            'empleado': '#3B82F6',
        }
        color = colores.get(obj.rol, '#6B7280')
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase;">{}</span>',
            color,
            obj.rol
        )
    rol_badge.short_description = 'Rol'
    
    def estado_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color:#10B981; color:white; padding:4px 12px; '
                'border-radius:12px; font-size:11px; font-weight:600;">Activo</span>'
            )
        return format_html(
            '<span style="background-color:#EF4444; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:600;">Inactivo</span>'
        )
    estado_badge.short_description = 'Estado'

# ==================== MARCA ====================
@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'logo_preview', 'descripcion_corta', 'productos_count']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['id', 'logo_preview_large']
    
    fieldsets = (
        ('Información de la Marca', {
            'fields': ('nombre', 'descripcion', 'logo', 'logo_preview_large')
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="40" height="40" style="object-fit:contain; border-radius:6px; '
                'background:#f5f5f5; padding:4px;" />',
                obj.logo
            )
        return format_html('<span style="color:#999;">Sin logo</span>')
    logo_preview.short_description = 'Logo'
    
    def logo_preview_large(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" width="200" height="200" style="object-fit:contain; border-radius:8px; '
                'background:#f5f5f5; padding:8px; border:1px solid #ddd;" />',
                obj.logo
            )
        return "Sin logo"
    logo_preview_large.short_description = 'Vista Previa del Logo'
    
    def descripcion_corta(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return '-'
    descripcion_corta.short_description = 'Descripción'
    
    def productos_count(self, obj):
        count = obj.producto_set.count()
        return format_html(
            '<span style="background-color:#3B82F6; color:white; padding:4px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{} productos</span>',
            count
        )
    productos_count.short_description = 'Productos'

# ==================== TIPO ====================
@admin.register(Tipo)
class TipoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'descripcion_corta', 'productos_count']
    search_fields = ['nombre', 'descripcion']
    
    def descripcion_corta(self, obj):
        if obj.descripcion:
            return obj.descripcion[:50] + '...' if len(obj.descripcion) > 50 else obj.descripcion
        return '-'
    descripcion_corta.short_description = 'Descripción'
    
    def productos_count(self, obj):
        count = obj.producto_set.count()
        return format_html(
            '<span style="background-color:#8B5CF6; color:white; padding:4px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{} productos</span>',
            count
        )
    productos_count.short_description = 'Productos'

# ==================== PRODUCTO ====================
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'miniatura',
        'nombre',
        'marca',
        'tipo',
        'precio_formateado', # Este es el precio CON IVA
        'stock_badge',
        'genero_badge',
    ]
    search_fields = ['nombre', 'descripcion', 'marca__nombre', 'tipo__nombre']
    list_filter = ['genero', 'marca', 'tipo']
    readonly_fields = ['id', 'imagen_preview']
    ordering = ['-id']
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion', 'precio', 'stock')
        }),
        ('Clasificación', {
            'fields': ('genero', 'marca', 'tipo')
        }),
        ('Imagen', {
            'fields': ('url_imagen', 'imagen_preview')
        }),
    )
    
    def miniatura(self, obj):
        if obj.url_imagen:
            return format_html(
                '<img src="{}" width="60" height="60" style="object-fit:cover; border-radius:8px; '
                'box-shadow:0 2px 8px rgba(0,0,0,0.1);" />',
                obj.url_imagen
            )
        return format_html(
            '<div style="width:60px; height:60px; background:#f0f0f0; border-radius:8px; '
            'display:flex; align-items:center; justify-content:center; color:#999; font-size:10px;">'
            'Sin imagen</div>'
        )
    miniatura.short_description = 'Imagen'
    
    def imagen_preview(self, obj):
        if obj.url_imagen:
            return format_html(
                '<img src="{}" width="300" height="300" style="object-fit:contain; border-radius:8px; '
                'border:1px solid #ddd; padding:8px; background:#fafafa;" />',
                obj.url_imagen
            )
        return "Sin imagen"
    imagen_preview.short_description = 'Vista Previa'
    
    def precio_formateado(self, obj):
        precio = f"€{float(obj.precio):.2f}"
        return format_html(
            '<span style="font-weight:700; font-size:14px;">{}</span>',
            precio
        )
    precio_formateado.short_description = 'Precio (c/IVA)'
    precio_formateado.admin_order_field = 'precio'
    
    def stock_badge(self, obj):
        if obj.stock == 0:
            color = '#EF4444'
            texto = 'AGOTADO'
        elif obj.stock <= 5:
            color = '#F59E0B'
            texto = f'{obj.stock} unidades'
        else:
            color = '#10B981'
            texto = f'{obj.stock} unidades'
        
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            texto
        )
    stock_badge.short_description = 'Stock'
    stock_badge.admin_order_field = 'stock'
    
    def genero_badge(self, obj):
        colores = {
            'Masculino': '#3B82F6',
            'Femenino': '#EC4899',
            'Unisex': '#8B5CF6',
        }
        color = colores.get(obj.genero, '#6B7280')
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.genero
        )
    genero_badge.short_description = 'Género'

# ==================== CLIENTE ====================
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'nombre_completo',
        'email',
        'cedula',
        'celular',
        'sexo_badge',
        'facturas_count',
    ]
    search_fields = ['nombre', 'apellido', 'email', 'cedula', 'celular']
    list_filter = ['sexo']
    readonly_fields = ['id']
    ordering = ['-id']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido', 'cedula', 'sexo')
        }),
        ('Contacto', {
            'fields': ('email', 'celular', 'direccion')
        }),
        ('Seguridad', {
            'fields': ('password',),
            'classes': ('collapse',)
        }),
    )
    
    def nombre_completo(self, obj):
        return f"{obj.nombre} {obj.apellido}"
    nombre_completo.short_description = 'Cliente'
    nombre_completo.admin_order_field = 'nombre'
    
    def sexo_badge(self, obj):
        colores = {
            'Hombre': '#3B82F6',
            'Mujer': '#EC4899',
        }
        color = colores.get(obj.sexo, '#6B7280')
        return format_html(
            '<span style="background-color:{}; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color,
            obj.sexo
        )
    sexo_badge.short_description = 'Sexo'
    
    def facturas_count(self, obj):
        count = obj.factura_set.count()
        if count == 0:
            return format_html('<span style="color:#999;">Sin compras</span>')
        return format_html(
            '<span style="background-color:#10B981; color:white; padding:4px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{} compras</span>',
            count
        )
    facturas_count.short_description = 'Compras'

# ==================== FACTURA (AJUSTADA) ====================
@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    inlines = [DetalleFacturaInline] 
    
    list_display = [
        'numero_orden_display',
        'cliente_nombre_completo',
        'fecha',
        'total_formateado',
        'subtotal_sin_iva_formateado', # Mostrar Subtotal sin IVA
        'iva_calculado_formateado',     # Mostrar IVA
        'metodo_pago_badge',
        'items_count',
        'ver_pdf_button',
    ]
    list_filter = ['metodo_pago', 'fecha']
    search_fields = [
        'cliente__nombre',
        'cliente__apellido',
        'cliente__email',
        'id',
    ]
    date_hierarchy = 'fecha'
    # 'total' es de solo lectura porque se calcula
    readonly_fields = ['fecha', 'total'] 
    ordering = ['-fecha']
    
    fieldsets = (
        ('Información de la Factura', {
            # Mostramos el total final aquí.
            'fields': ('cliente', 'fecha', 'metodo_pago', 'total') 
        }),
    )
    
    # ------------------ Lógica de Cálculo ------------------
    def save_model(self, request, obj, form, change):
        # Es crucial inicializar 'total' a 0 antes de guardar si es la primera vez
        if obj.total is None:
            obj.total = Decimal('0.00')
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        # Primero, llama a la función base para guardar los detalles
        super().save_formset(request, form, formset, change)
        
        factura = form.instance
        
        # Solo calcular si el formset es el de DetalleFactura
        if formset.model == DetalleFactura:
            # 1. Sumar los SUBTOTALES (que son SIN IVA)
            agregacion = DetalleFactura.objects.filter(factura=factura).aggregate(
                subtotal_total=Sum('subtotal') # Suma los subtotales (SIN IVA)
            )
            
            subtotal_total = agregacion['subtotal_total'] or Decimal('0.00')
            
            # 2. Calcular el TOTAL (con IVA)
            # Total = Subtotal Total * 1.15
            total_final = (subtotal_total * IVA_FACTOR).quantize(Decimal('0.00'))
            
            # Si el total ha cambiado, actualizar y guardar la factura
            if factura.total != total_final:
                factura.total = total_final
                # Usamos update_fields para actualizar solo el campo necesario
                factura.save(update_fields=['total'])
    # --------------------------------------------------------
    
    def numero_orden_display(self, obj):
        orden = f"ORD-{obj.id:06d}"
        return format_html(
            '<span style="font-family:monospace; font-weight:700;">{}</span>',
            orden
        )
    numero_orden_display.short_description = 'N° Orden'
    numero_orden_display.admin_order_field = 'id'
    
    def cliente_nombre_completo(self, obj):
        return f"{obj.cliente.nombre} {obj.cliente.apellido}"
    cliente_nombre_completo.short_description = 'Cliente'
    cliente_nombre_completo.admin_order_field = 'cliente__nombre'
    
    # Nuevo: Mostrar Subtotal sin IVA
    def subtotal_sin_iva_formateado(self, obj):
        # Recalcular el subtotal total (suma de subtotales) para la visualización
        subtotal_total = obj.detallefactura_set.aggregate(
            subtotal_total=Sum('subtotal')
        )['subtotal_total'] or Decimal('0.00')
        
        subtotal_formateado = f"€{subtotal_total.quantize(Decimal('0.00'))}"
        return format_html(
            '<span style="font-weight:400; font-size:14px; color:#555;">{}</span>',
            subtotal_formateado
        )
    subtotal_sin_iva_formateado.short_description = 'Subtotal (s/IVA)'
    
    # Nuevo: Mostrar IVA
    def iva_calculado_formateado(self, obj):
        # Recalcular el subtotal total (suma de subtotales)
        subtotal_total = obj.detallefactura_set.aggregate(
            subtotal_total=Sum('subtotal')
        )['subtotal_total'] or Decimal('0.00')
        
        # Calcular IVA: Subtotal Total * 0.15
        iva = (subtotal_total * IVA_RATE).quantize(Decimal('0.00'))
        
        iva_formateado = f"€{iva}"
        return format_html(
            '<span style="font-weight:400; font-size:14px; color:#F59E0B;">{}</span>',
            iva_formateado
        )
    iva_calculado_formateado.short_description = f'IVA ({IVA_RATE*100}%)'
    
    def total_formateado(self, obj):
        total = f"€{obj.total.quantize(Decimal('0.00'))}"
        return format_html(
            '<span style="font-weight:700; font-size:15px; color:#10B981;">{}</span>',
            total
        )
    total_formateado.short_description = 'Total (c/IVA)'
    total_formateado.admin_order_field = 'total'
    
    def metodo_pago_badge(self, obj):
        colores = {
            'wawallet': '#8B5CF6',
            'efectivo': '#10B981',
            'tarjeta': '#3B82F6',
        }
        iconos = {
            'wawallet': '💳',
            'efectivo': '💵',
            'tarjeta': '🏦',
        }
        color = colores.get(obj.metodo_pago, '#6B7280')
        icono = iconos.get(obj.metodo_pago, '💰')
        return format_html(
            '<span style="background-color:{}; color:white; padding:6px 14px; '
            'border-radius:12px; font-size:11px; font-weight:600; text-transform:uppercase;">'
            '{} {}</span>',
            color,
            icono,
            obj.metodo_pago
        )
    metodo_pago_badge.short_description = 'Método de Pago'
    
    def items_count(self, obj):
        count = obj.detallefactura_set.count()
        return format_html(
            '<span style="background-color:#6B7280; color:white; padding:4px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{} items</span>',
            count
        )
    items_count.short_description = 'Productos'
    
    def ver_pdf_button(self, obj):
        # Asume que 'admin_factura_pdf' está definido en tus urls
        url = reverse('admin_factura_pdf', args=[obj.id]) 
        return format_html(
            '<a class="button" style="background-color:#10B981; color:white; padding:10px 18px; '
            'border-radius:8px; text-decoration:none; font-weight:600; display:inline-flex; '
            'align-items:center; gap:6px; transition:all 0.3s ease;" '
            'href="{}" target="_blank">'
            '<span style="font-size:16px;">📄</span> Ver PDF'
            '</a>',
            url
        )
    ver_pdf_button.short_description = 'Acciones'

# ==================== DETALLE FACTURA ====================
# Este DetalleFacturaAdmin se mantiene para la vista de lista/cambio si se accede directamente.
@admin.register(DetalleFactura)
class DetalleFacturaAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'factura_numero',
        'producto_info',
        'cantidad_badge',
        'precio_unitario_formateado_sin_iva',
        'subtotal_formateado_sin_iva',
    ]
    list_filter = ['factura__fecha', 'producto__marca']
    search_fields = [
        'producto__nombre',
        'factura__cliente__nombre',
        'factura__id',
    ]
    readonly_fields = ['subtotal', 'precio_unitario'] # ¡De solo lectura!
    ordering = ['-factura__fecha']
    
    def factura_numero(self, obj):
        orden = f"ORD-{obj.factura.id:06d}"
        return format_html(
            '<a href="/admin/perfume_api/factura/{}/change/" style="font-family:monospace; '
            'font-weight:700; color:#3B82F6; text-decoration:none;">{}</a>',
            obj.factura.id,
            orden
        )
    factura_numero.short_description = 'Factura'
    
    def producto_info(self, obj):
        # Usamos el precio original del producto para mostrar.
        precio_con_iva = f"€{obj.producto.precio.quantize(Decimal('0.00'))}"
        return format_html(
            '<div style="display:flex; align-items:center; gap:10px;">'
            '<img src="{}" width="40" height="40" style="object-fit:cover; border-radius:6px;" />'
            '<div><strong>{}</strong><br><small style="color:#666;">{} | Precio Venta: {}</small></div>'
            '</div>',
            obj.producto.url_imagen if obj.producto.url_imagen else 'https://via.placeholder.com/40',
            obj.producto.nombre,
            obj.producto.marca.nombre if obj.producto.marca else 'Sin marca',
            precio_con_iva 
        )
    producto_info.short_description = 'Producto'
    
    def cantidad_badge(self, obj):
        return format_html(
            '<span style="background-color:#3B82F6; color:white; padding:6px 14px; '
            'border-radius:12px; font-size:13px; font-weight:700;">× {}</span>',
            obj.cantidad
        )
    cantidad_badge.short_description = 'Cantidad'
    
    def precio_unitario_formateado_sin_iva(self, obj):
        precio = f"€{obj.precio_unitario.quantize(Decimal('0.00'))}"
        return format_html('<span style="color:#999;">{}</span>', precio)
    precio_unitario_formateado_sin_iva.short_description = 'Precio Unit. (s/IVA)'
    
    def subtotal_formateado_sin_iva(self, obj):
        subtotal = f"€{obj.subtotal.quantize(Decimal('0.00'))}"
        return format_html(
            '<span style="font-weight:700; font-size:14px;">{}</span>',
            subtotal
        )
    subtotal_formateado_sin_iva.short_description = 'Subtotal (s/IVA)'
    subtotal_formateado_sin_iva.admin_order_field = 'subtotal'

# ==================== PASSWORD RESET CODE ====================
@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = [
        'usuario_email',
        'code_display',
        'created_at',
        'expires_at',
        'estado_badge',
    ]
    list_filter = ['used', 'created_at']
    search_fields = ['usuario__email', 'code']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    
    def usuario_email(self, obj):
        return obj.usuario.email
    usuario_email.short_description = 'Usuario'
    
    def code_display(self, obj):
        return format_html(
            '<span style="font-family:monospace; font-weight:700; font-size:18px; '
            'background:#f5f5f5; padding:8px 16px; border-radius:6px; letter-spacing:2px; color:#111;">{}</span>',
            obj.code
        )
    code_display.short_description = 'Código'
    
    def estado_badge(self, obj):
        if obj.used:
            return format_html(
                '<span style="background-color:#6B7280; color:white; padding:4px 12px; '
                'border-radius:12px; font-size:11px; font-weight:600;">USADO</span>'
            )
        if obj.expires_at < timezone.now():
            return format_html(
                '<span style="background-color:#EF4444; color:white; padding:4px 12px; '
                'border-radius:12px; font-size:11px; font-weight:600;">EXPIRADO</span>'
            )
        return format_html(
            '<span style="background-color:#10B981; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:11px; font-weight:600;">ACTIVO</span>'
        )
    estado_badge.short_description = 'Estado'