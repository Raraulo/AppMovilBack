# perfume_api/views.py
from datetime import datetime, timedelta
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import io
import os
import re
import base64
import resend  # ✅ NUEVO
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.conf import settings

# ✅ Configurar Resend API Key
resend.api_key = os.environ.get('RESEND_API_KEY', '')

# ✅ REPORTLAB para PDFs
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from .models import (
    Usuario, 
    Marca, 
    Tipo, 
    Producto, 
    Factura, 
    DetalleFactura, 
    Cliente, 
    PasswordResetCode,
    EmailVerification
)
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
# ✅ ENDPOINTS DE VERIFICACIÓN DE EMAIL CON RESEND API
# ======================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def send_verification_code(request):
    """
    📧 Envía un código de verificación al email del usuario usando Resend API
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return Response({
            'message': 'Email requerido'
        }, status=400)
    
    # Validar formato de email
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    if not re.match(email_regex, email):
        return Response({
            'message': 'Formato de email inválido'
        }, status=400)
    
    # Verificar si el email ya está registrado
    if Cliente.objects.filter(email=email).exists():
        return Response({
            'message': 'Este correo ya está registrado. Inicia sesión',
            'exists': True
        }, status=400)
    
    # Generar código de 6 dígitos
    code = EmailVerification.generate_code()
    
    # Eliminar códigos previos del mismo email
    EmailVerification.objects.filter(email=email).delete()
    
    # Crear nuevo registro de verificación
    EmailVerification.objects.create(email=email, code=code)
    
    # Enviar email con Resend API
    try:
        params = {
            "from": "Maison de Parfums <onboarding@resend.dev>",
            "to": [email],
            "subject": "Código de verificación - Maison de Parfums",
            "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #333; text-align: center;">Código de verificación</h2>
                    <p style="color: #666;">Hola,</p>
                    <p style="color: #666;">Tu código de verificación es:</p>
                    <div style="background-color: #f5f5f5; padding: 30px; text-align: center; margin: 30px 0; border-radius: 10px;">
                        <h1 style="color: #000; font-size: 42px; letter-spacing: 10px; margin: 0; font-weight: bold;">{code}</h1>
                    </div>
                    <p style="color: #666;">Este código expira en <strong>10 minutos</strong>.</p>
                    <p style="color: #666;">Si no solicitaste este código, ignora este mensaje.</p>
                    <br>
                    <p style="color: #666;">Saludos,<br><strong>Maison de Parfums</strong></p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">Perfumería de Lujo</p>
                </div>
            """
        }
        
        resend.Emails.send(params)
        
        return Response({
            'message': 'Código enviado correctamente',
            'exists': False
        }, status=200)
        
    except Exception as e:
        print(f"❌ Error enviando email: {str(e)}")
        return Response({
            'message': f'Error al enviar email: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email_code(request):
    """
    ✅ Verifica el código de verificación ingresado por el usuario
    """
    email = request.data.get('email', '').lower().strip()
    code = request.data.get('code', '').strip()
    
    if not email or not code:
        return Response({
            'message': 'Email y código son requeridos',
            'verified': False
        }, status=400)
    
    try:
        # Buscar el código más reciente para este email
        verification = EmailVerification.objects.filter(
            email=email,
            code=code,
            is_verified=False
        ).latest('created_at')
        
        # Verificar si el código expiró
        if verification.is_expired():
            return Response({
                'message': 'El código ha expirado. Solicita uno nuevo',
                'verified': False
            }, status=400)
        
        # Marcar como verificado
        verification.is_verified = True
        verification.save()
        
        return Response({
            'message': 'Email verificado correctamente',
            'verified': True
        }, status=200)
        
    except EmailVerification.DoesNotExist:
        return Response({
            'message': 'Código inválido o ya utilizado',
            'verified': False
        }, status=400)

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
# 🔹 FUNCIÓN: GENERAR PDF CON REPORTLAB
# ======================================================

def generar_pdf_factura(factura):
    """
    Genera un PDF de la factura con ReportLab
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
        
        # Crear PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 50, "MAISON DES SENTEURS")
        c.setFont("Helvetica-Oblique", 12)
        c.drawCentredString(width/2, height - 70, "Perfumería de Lujo")
        
        # Línea separadora
        c.line(50, height - 90, width - 50, height - 90)
        
        # Información de factura
        y = height - 130
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Factura No:")
        c.setFont("Helvetica", 12)
        c.drawString(150, y, f"ORD-{factura.id:06d}")
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y, "Fecha:")
        c.setFont("Helvetica", 12)
        c.drawString(450, y, fecha_formateada)
        
        # Cliente
        y -= 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Cliente:")
        c.setFont("Helvetica", 12)
        c.drawString(110, y, f"{factura.cliente.nombre} {factura.cliente.apellido}")
        
        y -= 20
        c.drawString(110, y, factura.cliente.email)
        
        if factura.cliente.cedula:
            y -= 20
            c.drawString(110, y, f"CI: {factura.cliente.cedula}")
        
        if factura.cliente.celular:
            y -= 20
            c.drawString(110, y, f"Tel: {factura.cliente.celular}")
        
        if factura.cliente.direccion:
            y -= 20
            c.drawString(110, y, f"Dir: {factura.cliente.direccion[:50]}")
        
        # Método de pago
        y -= 30
        metodo_pago_display = {
            'wawallet': 'WaWallet',
            'efectivo': 'Efectivo',
            'tarjeta': 'Tarjeta de Crédito'
        }.get(factura.metodo_pago, factura.metodo_pago.upper())
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(400, y, "Método de Pago:")
        c.setFont("Helvetica", 12)
        c.drawString(500, y, metodo_pago_display)
        
        # Tabla de productos
        y -= 50
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Detalle de Productos")
        
        y -= 30
        # Headers de tabla
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, y, "Producto")
        c.drawString(300, y, "Cantidad")
        c.drawString(370, y, "Precio Unit.")
        c.drawString(470, y, "Subtotal")
        
        # Línea bajo headers
        c.line(50, y - 5, width - 50, y - 5)
        
        # Productos
        y -= 25
        c.setFont("Helvetica", 10)
        for detalle in detalles:
            producto = detalle.producto
            c.drawString(50, y, producto.nombre[:40])
            c.drawString(300, y, str(detalle.cantidad))
            c.drawString(370, y, f"${detalle.precio_unitario:.2f}")
            c.drawString(470, y, f"${detalle.subtotal:.2f}")
            y -= 20
            
            if y < 150:
                c.showPage()
                y = height - 100
                c.setFont("Helvetica", 10)
        
        # Totales
        y -= 30
        c.line(350, y, width - 50, y)
        y -= 25
        
        c.setFont("Helvetica", 12)
        c.drawString(370, y, "Subtotal:")
        c.drawString(470, y, f"${subtotal:.2f}")
        
        y -= 20
        c.drawString(370, y, "IVA (15%):")
        c.drawString(470, y, f"${iva:.2f}")
        
        y -= 20
        c.line(350, y + 5, width - 50, y + 5)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(370, y - 10, "TOTAL:")
        c.drawString(470, y - 10, f"${total:.2f}")
        
        # Footer
        c.setFont("Helvetica-Oblique", 10)
        c.drawCentredString(width/2, 50, "Gracias por su compra en Maison Des Senteurs")
        c.drawCentredString(width/2, 35, "Perfumería de Lujo")
        
        c.save()
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
        cliente_data = request.data.get('cliente', {})
        
        if not usuario_id:
            return Response({"error": "El usuario_id es requerido"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not productos_data:
            return Response({"error": "Debe enviar al menos un producto"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
        
        cliente, created = Cliente.objects.update_or_create(
            email=cliente_data.get('email', usuario.email),
            defaults={
                'nombre': cliente_data.get('nombre', 'Cliente'),
                'apellido': cliente_data.get('apellido', usuario.email.split('@')[0]),
                'cedula': cliente_data.get('cedula', str(usuario.id).zfill(10)),
                'direccion': cliente_data.get('direccion', ''),
                'celular': cliente_data.get('celular', ''),
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
                    'cedula': cliente.cedula if hasattr(cliente, 'cedula') else '',
                    'direccion': cliente.direccion if hasattr(cliente, 'direccion') else '',
                    'celular': cliente.celular if hasattr(cliente, 'celular') else '',
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

# ======================================================
# 🔹 ENDPOINT PARA VER PDF DESDE ADMIN
# ======================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def admin_factura_pdf(request, factura_id):
    """
    Genera y muestra el PDF de una factura directamente en el navegador
    """
    try:
        factura = get_object_or_404(Factura, id=factura_id)
        
        pdf_content = generar_pdf_factura(factura)
        
        if not pdf_content:
            return HttpResponse(
                "Error al generar el PDF. Revisa los logs del servidor.",
                status=500
            )
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Factura_ORD-{factura.id:06d}.pdf"'
        
        return response
        
    except Exception as e:
        print(f"❌ Error generando PDF para admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error: {str(e)}", status=500)
