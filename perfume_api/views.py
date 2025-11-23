# perfume_api/views.py
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
import io
import os
import base64
from xhtml2pdf import pisa
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.utils.crypto import get_random_string
from django.conf import settings

from .models import Usuario, Marca, Tipo, Producto, Factura, DetalleFactura, Cliente, PasswordResetCode
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
    serializer_class = ProductoSerializer


class FacturaViewSet(viewsets.ModelViewSet):
    queryset = Factura.objects.all()
    serializer_class = FacturaSerializer


class DetalleFacturaViewSet(viewsets.ModelViewSet):
    queryset = DetalleFactura.objects.all()
    serializer_class = DetalleFacturaSerializer


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]


# ======================================================
# 🔹 ENDPOINTS PERSONALIZADOS
# ======================================================

@api_view(["GET"])
def productos_por_marca(request, marca_id):
    productos = Producto.objects.filter(marca_id=marca_id)
    serializer = ProductoSerializer(productos, many=True)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agregar_a_favoritos(request):
    producto_id = request.data.get("producto_id")
    return Response({"mensaje": f"Producto {producto_id} añadido a favoritos"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def agregar_a_carrito(request):
    producto_id = request.data.get("producto_id")
    return Response({"mensaje": f"Producto {producto_id} añadido al carrito"})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cliente(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return Response({"message": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    serializer = ClienteSerializer(cliente)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def update_cliente(request, pk):
    try:
        cliente = Cliente.objects.get(pk=pk)
    except Cliente.DoesNotExist:
        return Response({"message": "Cliente no encontrado"}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    if data.get("password"):
        data["password"] = make_password(data["password"])
    else:
        data["password"] = cliente.password

    serializer = ClienteSerializer(cliente, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ======================================================
# 🔹 FUNCIÓN AUXILIAR: GENERAR PDF DE FACTURA CLÁSICO
# ======================================================
def generar_pdf_factura(factura):
    """
    Genera un PDF de la factura con diseño clásico idéntico al frontend
    """
    try:
        detalles = DetalleFactura.objects.filter(factura=factura)
        
        # Calcular IVA
        IVA_PORCENTAJE = 0.15
        total = float(factura.total)
        subtotal = total / (1 + IVA_PORCENTAJE)
        iva = total - subtotal
        
        # Configurar meses en español
        meses = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        mes_texto = meses[factura.fecha.month]
        fecha_formateada = f"{factura.fecha.day} de {mes_texto}, {factura.fecha.year}"
        
        # Convertir logo a base64
        logo_base64 = ""
        try:
            logo_path = os.path.join(settings.MEDIA_ROOT, 'images', 'logomaison.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as img_file:
                    logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            print(f"⚠️ No se pudo cargar el logo: {e}")
        
        # ✨ DISEÑO CLÁSICO IDÉNTICO AL FRONTEND
        html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Factura ORD-{factura.id:06d}</title>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}
    body {{
      font-family: 'Georgia', serif;
      padding: 50px;
      background: #fff;
      color: #1a1a1a;
    }}
    .header {{
      text-align: center;
      margin-bottom: 40px;
      border-bottom: 3px solid #000;
      padding-bottom: 25px;
    }}
    .logo {{
      font-size: 32px;
      font-weight: bold;
      margin-bottom: 8px;
      letter-spacing: 3px;
      color: #000;
    }}
    .logo-img {{
      width: 200px;
      height: auto;
      margin-bottom: 10px;
    }}
    .subtitle {{
      font-size: 14px;
      color: #666;
      font-style: italic;
      letter-spacing: 1px;
    }}
    .info-section {{
      display: table;
      width: 100%;
      margin-bottom: 35px;
      padding: 20px;
      background: #fafafa;
      border-radius: 8px;
    }}
    .info-row {{
      display: table-row;
    }}
    .info-box {{
      display: table-cell;
      width: 50%;
      padding: 10px;
      vertical-align: top;
    }}
    .info-box-right {{
      text-align: right;
    }}
    .info-title {{
      font-weight: bold;
      font-size: 11px;
      color: #666;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .info-value {{
      font-size: 15px;
      color: #000;
      line-height: 1.6;
    }}
    .info-value-small {{
      font-size: 13px;
      color: #666;
      line-height: 1.6;
    }}
    .section-title {{
      font-size: 18px;
      font-weight: bold;
      margin: 30px 0 20px 0;
      padding-bottom: 10px;
      border-bottom: 2px solid #000;
      text-transform: uppercase;
      letter-spacing: 2px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 35px;
    }}
    th {{
      background: #000;
      color: #fff;
      padding: 15px;
      text-align: left;
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    td {{
      padding: 15px;
      border-bottom: 1px solid #e8e8e8;
      font-size: 14px;
    }}
    tr:last-child td {{
      border-bottom: none;
    }}
    .product-name {{
      font-weight: bold;
      color: #000;
      margin-bottom: 4px;
    }}
    .product-details {{
      font-size: 12px;
      color: #666;
    }}
    .totals-section {{
      margin-top: 30px;
      padding: 25px;
      background: #fafafa;
      border-radius: 8px;
    }}
    .total-row {{
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      font-size: 15px;
    }}
    .total-label {{
      font-weight: 600;
      color: #333;
    }}
    .total-value {{
      font-weight: 600;
      color: #000;
    }}
    .final-total {{
      border-top: 3px solid #000;
      padding-top: 18px;
      margin-top: 15px;
      font-size: 20px;
      font-weight: bold;
    }}
    .final-total .total-value {{
      font-size: 24px;
      color: #000;
    }}
    .footer {{
      margin-top: 60px;
      text-align: center;
      font-size: 12px;
      color: #666;
      border-top: 1px solid #ddd;
      padding-top: 25px;
      line-height: 1.8;
    }}
    .footer-bold {{
      font-weight: bold;
      color: #000;
      margin-top: 8px;
    }}
    .text-center {{
      text-align: center;
    }}
    .text-right {{
      text-align: right;
    }}
  </style>
</head>
<body>
  <div class="header">
    {"<img src='data:image/png;base64," + logo_base64 + "' class='logo-img' />" if logo_base64 else "<div class='logo'>MAISON DES SENTEURS</div>"}
    <div class="subtitle">Perfumería de Lujo</div>
  </div>

  <div class="info-section">
    <div class="info-row">
      <div class="info-box">
        <div class="info-title">Factura No.</div>
        <div class="info-value">ORD-{factura.id:06d}</div>
      </div>
      <div class="info-box info-box-right">
        <div class="info-title">Fecha de Emisión</div>
        <div class="info-value">{fecha_formateada}</div>
      </div>
    </div>
  </div>

  <div class="info-section">
    <div class="info-row">
      <div class="info-box">
        <div class="info-title">Facturado a</div>
        <div class="info-value">
          {factura.cliente.nombre} {factura.cliente.apellido}
        </div>
"""

        # ✅ AGREGAR DATOS COMPLETOS DEL CLIENTE SI EXISTEN
        if factura.cliente.cedula:
            html_content += f"""
        <div class="info-value-small">CI: {factura.cliente.cedula}</div>
"""
        
        html_content += f"""
        <div class="info-value-small">{factura.cliente.email}</div>
"""
        
        if factura.cliente.celular:
            html_content += f"""
        <div class="info-value-small">Tel: {factura.cliente.celular}</div>
"""
        
        if factura.cliente.direccion:
            html_content += f"""
        <div class="info-value-small" style="margin-top: 8px;">{factura.cliente.direccion}</div>
"""

        # Método de pago
        metodo_pago_display = {
            'wawallet': 'WaWallet',
            'efectivo': 'Efectivo',
            'tarjeta': 'Tarjeta de Crédito'
        }.get(factura.metodo_pago, factura.metodo_pago.upper())

        html_content += f"""
      </div>
      <div class="info-box info-box-right">
        <div class="info-title">Método de Pago</div>
        <div class="info-value">{metodo_pago_display}</div>
      </div>
    </div>
  </div>

  <div class="section-title">Detalle de Productos</div>

  <table>
    <thead>
      <tr>
        <th style="width: 45%;">Producto</th>
        <th style="width: 15%; text-align: center;">Cantidad</th>
        <th style="width: 20%; text-align: right;">Precio Unit.</th>
        <th style="width: 20%; text-align: right;">Subtotal</th>
      </tr>
    </thead>
    <tbody>
"""

        # Agregar productos
        for detalle in detalles:
            producto = detalle.producto
            html_content += f"""
      <tr>
        <td>
          <div class="product-name">{producto.nombre}</div>
          <div class="product-details">{producto.marca.nombre if producto.marca else 'Sin marca'} - {producto.tipo.nombre if producto.tipo else 'Sin tipo'}</div>
        </td>
        <td style="text-align: center;">{detalle.cantidad}</td>
        <td style="text-align: right;">${detalle.precio_unitario:.2f}</td>
        <td style="text-align: right; font-weight: 600;">${detalle.subtotal:.2f}</td>
      </tr>
"""

        html_content += f"""
    </tbody>
  </table>

  <div class="totals-section">
    <div class="total-row">
      <div class="total-label">Subtotal:</div>
      <div class="total-value">${subtotal:.2f}</div>
    </div>
    <div class="total-row">
      <div class="total-label">IVA (15%):</div>
      <div class="total-value">${iva:.2f}</div>
    </div>
    <div class="total-row final-total">
      <div class="total-label">TOTAL:</div>
      <div class="total-value">${total:.2f}</div>
    </div>
  </div>

  <div class="footer">
    <p>Gracias por su compra en Maison Des Senteurs</p>
    <p class="footer-bold">Perfumería de Lujo</p>
    <p style="margin-top: 12px;">Esta es una factura electrónica válida</p>
  </div>
</body>
</html>
"""
        
        # Generar PDF
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)
        
        if pisa_status.err:
            print(f"❌ Error en pisa.CreatePDF: {pisa_status.err}")
            return None
        
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
        
    except Exception as e:
        print(f"❌ Error generando PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def enviar_factura_por_email(factura):
    """
    Envía la factura por correo electrónico al cliente
    """
    try:
        pdf_content = generar_pdf_factura(factura)
        
        if not pdf_content:
            print("❌ No se pudo generar el PDF")
            return False
        
        subject = f'Factura ORD-{factura.id:06d} - Maison Des Senteurs'
        message = f"""
Estimado/a {factura.cliente.nombre} {factura.cliente.apellido},

Gracias por su compra en Maison Des Senteurs.

Adjunto encontrará su factura correspondiente a la orden ORD-{factura.id:06d}.

Detalles de la compra:
- Total: ${factura.total:.2f}
- Método de pago: {factura.metodo_pago.upper()}
- Fecha: {factura.fecha.strftime('%d/%m/%Y %H:%M')}

¡Esperamos volver a verle pronto!

Atentamente,
Maison Des Senteurs
Perfumería de Lujo
"""
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email='maisondeparfumsprofesional@gmail.com',
            to=[factura.cliente.email],
        )
        
        email.attach(
            f'Factura_ORD-{factura.id:06d}.pdf',
            pdf_content,
            'application/pdf'
        )
        
        email.send()
        
        print(f"✅ Factura enviada a {factura.cliente.email}")
        return True
        
    except Exception as e:
        print(f"❌ Error enviando factura: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


# ======================================================
# 🔹 ENDPOINT PARA PROCESAR VENTAS
# ======================================================

@api_view(['POST'])
@permission_classes([AllowAny])
@transaction.atomic
def procesar_venta(request):
    try:
        usuario_id = request.data.get('usuario_id')
        productos_data = request.data.get('productos', [])
        metodo_pago = request.data.get('metodo_pago', 'efectivo')
        cliente_data = request.data.get('cliente', {})  # ✅ RECIBIR DATOS DEL CLIENTE
        
        if not usuario_id:
            return Response({"error": "El usuario_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not productos_data:
            return Response({"error": "Debe enviar al menos un producto"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        # ✅ CREAR O ACTUALIZAR CLIENTE CON TODOS LOS DATOS
        cliente, created = Cliente.objects.update_or_create(
            email=cliente_data.get('email', usuario.email),
            defaults={
                'nombre': cliente_data.get('nombre', 'Cliente'),
                'apellido': cliente_data.get('apellido', usuario.email.split('@')[0]),
                'cedula': cliente_data.get('cedula', str(usuario.id).zfill(10)),
                'direccion': cliente_data.get('direccion', ''),  # ✅ NUEVO
                'celular': cliente_data.get('celular', ''),      # ✅ NUEVO
                'password': 'temp123',
                'sexo': 'Hombre',
            }
        )
        
        total = 0
        detalles = []
        
        for item in productos_data:
            producto_id = item.get('id')
            cantidad = item.get('cantidad', 1)
            
            if not producto_id:
                return Response({"error": "Cada producto debe tener un ID"}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                producto = Producto.objects.select_for_update().get(id=producto_id)
            except Producto.DoesNotExist:
                return Response({"error": f"Producto con ID {producto_id} no encontrado"}, status=status.HTTP_404_NOT_FOUND)
            
            if producto.stock < cantidad:
                return Response({
                    "error": f"Stock insuficiente para {producto.nombre}",
                    "disponible": producto.stock,
                    "solicitado": cantidad
                }, status=status.HTTP_400_BAD_REQUEST)
            
            subtotal = producto.precio * cantidad
            total += subtotal
            
            detalles.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio_unitario': producto.precio,
                'subtotal': subtotal
            })
        
        factura = Factura.objects.create(
            cliente=cliente,
            fecha=timezone.now(),
            total=total,
            metodo_pago=metodo_pago
        )
        
        for detalle in detalles:
            DetalleFactura.objects.create(
                factura=factura,
                producto=detalle['producto'],
                cantidad=detalle['cantidad'],
                precio_unitario=detalle['precio_unitario'],
                subtotal=detalle['subtotal']
            )
            
            detalle['producto'].stock -= detalle['cantidad']
            detalle['producto'].save()
        
        email_enviado = enviar_factura_por_email(factura)
        
        return Response({
            "success": True,
            "factura_id": factura.id,
            "numero_orden": f"ORD-{factura.id:06d}",
            "total": float(total),
            "fecha": factura.fecha.isoformat(),
            "cliente": cliente.nombre + " " + cliente.apellido,
            "metodo_pago": metodo_pago,
            "email_enviado": email_enviado,
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": f"Error al procesar la venta: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================================================
# 🔹 ENDPOINT PARA OBTENER FACTURAS DEL USUARIO
# ======================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_facturas_usuario(request, usuario_id):
    try:
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            cliente = Cliente.objects.get(email=usuario.email)
        except Cliente.DoesNotExist:
            return Response({"facturas": []}, status=status.HTTP_200_OK)
        
        facturas = Factura.objects.filter(cliente=cliente).order_by('-fecha')
        
        facturas_data = []
        for factura in facturas:
            detalles = DetalleFactura.objects.filter(factura=factura)
            
            productos = []
            for detalle in detalles:
                productos.append({
                    'id': detalle.producto.id,
                    'nombre': detalle.producto.nombre,
                    'marca': detalle.producto.marca.nombre if detalle.producto.marca else 'Sin marca',
                    'tipo': detalle.producto.tipo.nombre if detalle.producto.tipo else 'Sin tipo',
                    'imagen': detalle.producto.url_imagen or '',
                    'cantidad': detalle.cantidad,
                    'precio_unitario': float(detalle.precio_unitario),
                    'subtotal': float(detalle.subtotal),
                })
            
            # ✅ INCLUIR TODOS LOS DATOS DEL CLIENTE
            facturas_data.append({
                'id': factura.id,
                'numero_orden': f"ORD-{factura.id:06d}",
                'fecha': factura.fecha.isoformat(),
                'total': float(factura.total),
                'metodo_pago': factura.metodo_pago,
                'productos': productos,
                'cliente': {
                    'nombre': cliente.nombre,
                    'apellido': cliente.apellido,
                    'email': cliente.email,
                    'cedula': cliente.cedula if hasattr(cliente, 'cedula') else '',      # ✅ NUEVO
                    'direccion': cliente.direccion if hasattr(cliente, 'direccion') else '',  # ✅ NUEVO
                    'celular': cliente.celular if hasattr(cliente, 'celular') else '',        # ✅ NUEVO
                }
            })
        
        return Response({"facturas": facturas_data}, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return Response({"error": f"Error al obtener facturas: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ======================================================
# 🔹 ENDPOINTS DE RECUPERACIÓN DE CONTRASEÑA
# ======================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    try:
        email = request.data.get('email', '').strip().lower()
        
        if not email:
            return Response({"message": "El email es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"message": "Este correo no está registrado"}, status=status.HTTP_404_NOT_FOUND)
        
        code = get_random_string(length=6, allowed_chars='0123456789')
        
        PasswordResetCode.objects.filter(usuario=usuario, used=False).delete()
        
        PasswordResetCode.objects.create(
            usuario=usuario,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        try:
            subject = 'Código de Recuperación - Maison Des Senteurs'
            message = f"""
Hola,

Has solicitado restablecer tu contraseña en Maison Des Senteurs.

Tu código de verificación es: {code}

Este código expira en 10 minutos.

Si no solicitaste este cambio, ignora este mensaje.

Atentamente,
Maison Des Senteurs
"""
            
            email_obj = EmailMessage(
                subject=subject,
                body=message,
                from_email='maisondeparfumsprofesional@gmail.com',
                to=[email],
            )
            email_obj.send()
            
        except Exception as e:
            print(f"❌ Error enviando email: {str(e)}")
        
        return Response({"message": "Código enviado exitosamente", "email": email}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"message": f"Error al procesar solicitud: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_verify(request):
    try:
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()
        
        if not email or not code:
            return Response({"message": "Email y código son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"message": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        reset_code = PasswordResetCode.objects.filter(
            usuario=usuario,
            code=code,
            expires_at__gt=timezone.now(),
            used=False
        ).first()
        
        if not reset_code:
            return Response({"message": "Código inválido o expirado"}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"message": "Código verificado correctamente", "email": email}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"message": f"Error al verificar código: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    try:
        email = request.data.get('email', '').strip().lower()
        code = request.data.get('code', '').strip()
        new_password = request.data.get('new_password', '')
        
        if not email or not code or not new_password:
            return Response({"message": "Email, código y nueva contraseña son requeridos"}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({"message": "La contraseña debe tener al menos 8 caracteres"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"message": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        reset_code = PasswordResetCode.objects.filter(
            usuario=usuario,
            code=code,
            expires_at__gt=timezone.now(),
            used=False
        ).first()
        
        if not reset_code:
            return Response({"message": "Código inválido o expirado"}, status=status.HTTP_400_BAD_REQUEST)
        
        usuario.password = make_password(new_password)
        usuario.save()
        
        reset_code.used = True
        reset_code.save()
        
        return Response({"message": "Contraseña actualizada exitosamente", "email": email}, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({"message": f"Error al cambiar contraseña: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# perfume_api/views.py
# ... (todo tu código anterior) ...

# ======================================================
# 🔹 ENDPOINT PARA VER PDF DESDE ADMIN
# ======================================================
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

@api_view(['GET'])
@permission_classes([AllowAny])
def admin_factura_pdf(request, factura_id):
    """
    Genera y muestra el PDF de una factura directamente en el navegador
    """
    try:
        factura = get_object_or_404(Factura, id=factura_id)
        
        # Generar PDF
        pdf_content = generar_pdf_factura(factura)
        
        if not pdf_content:
            return HttpResponse(
                "Error al generar el PDF. Revisa los logs del servidor.",
                status=500
            )
        
        # Devolver PDF para visualización en navegador
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Factura_ORD-{factura.id:06d}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"❌ Error generando PDF para admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)
