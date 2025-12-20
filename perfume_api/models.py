# perfume_api/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import random



# Define los roles para evitar repetición
ROLES = [
    ('admin', 'Administrador'),
    ('empleado', 'Empleado'),
    ('cliente', 'Cliente'),
]



# ----------- MANAGER PERSONALIZADO -----------
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user



    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "admin")



        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
            
        return self.create_user(email, password, **extra_fields)



# ----------- MODELO USUARIO PERSONALIZADO -----------
class Usuario(AbstractUser):
    username = None  # 🔹 Eliminamos username
    email = models.EmailField(unique=True)  # 🔹 Email será el identificador único
    
    # 🌟 CAMPOS AÑADIDOS PARA SOPORTAR EL ADMIN DE DJANGO
    nombre = models.CharField(max_length=150, blank=True, null=True)
    apellido = models.CharField(max_length=150, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    celular = models.CharField(max_length=15, blank=True, null=True)
    # edad NO incluido, si lo necesitas debes añadirlo aquí: models.IntegerField(null=True, blank=True)
    
    rol = models.CharField(
        max_length=20,
        choices=ROLES,
        default='cliente'
    )



    USERNAME_FIELD = "email"  # 🔹 Ahora el login será con email
    REQUIRED_FIELDS = ['nombre', 'apellido'] # 🔹 Pedirá nombre y apellido al crear superusuario



    objects = UsuarioManager()  # ✅ Usar nuestro manager personalizado



    def __str__(self):
        return f"{self.email} - {self.rol}"



# ---------- MARCAS ----------
class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)
    # 🌟 CAMPO AÑADIDO PARA EL ADMIN
    descripcion = models.TextField(blank=True, null=True) 



    def __str__(self):
        return self.nombre



# ---------- TIPOS ----------
class Tipo(models.Model):
    nombre = models.CharField(max_length=50)
    # 🌟 CAMPO AÑADIDO PARA EL ADMIN
    descripcion = models.TextField(blank=True, null=True)



    def __str__(self):
        return self.nombre



# ---------- PRODUCTOS ----------
class Producto(models.Model):
    GENERO_CHOICES = [
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
        ('Unisex', 'Unisex'), # Se añade opción Unisex para mayor flexibilidad
    ]
    
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    url_imagen = models.URLField(blank=True, null=True)
    # imagen = models.ImageField(upload_to="productos/", blank=True, null=True) # Mantengo solo url_imagen si usas un servicio externo
    stock = models.IntegerField(default=0)
    genero = models.CharField(max_length=10, choices=GENERO_CHOICES, default='Unisex')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.nombre



# ---------- CLIENTES ----------
class Cliente(models.Model):
    SEXO_CHOICES = [
        ('Hombre', 'Hombre'),
        ('Mujer', 'Mujer'),
    ]
    
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    celular = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES)
    password = models.CharField(max_length=255)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return f"{self.nombre} {self.apellido} - {self.email}"



# ---------- FACTURAS ----------
class Factura(models.Model):
    PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta de Crédito/Débito'),
        ('wawallet', 'WaWallet'),
        ('transferencia', 'Transferencia Bancaria'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(
        max_length=50,
        choices=PAGO_CHOICES,
        default='efectivo'
    )
    
    # ✅ NUEVOS CAMPOS PARA DESCUENTO DEL 15%
    descuento_aplicado = models.BooleanField(
        default=False,
        verbose_name="Descuento aplicado",
        help_text="Indica si se aplicó el descuento del 15% por compras mayores a $500"
    )
    monto_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Monto de descuento",
        help_text="Cantidad en dólares descontada (15% del subtotal)"
    )
    total_sin_descuento = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total sin descuento",
        help_text="Precio original antes de aplicar el descuento del 15%"
    )
    
    class Meta:
        verbose_name_plural = "Facturas"
        
    def __str__(self):
        return f"Factura #{self.id} - {self.cliente.nombre} {self.cliente.apellido}"



# ---------- DETALLE FACTURA ----------
class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)



    class Meta:
        verbose_name_plural = "Detalles de Factura"
        
    def __str__(self):
        return f"Detalle #{self.id} - Factura #{self.factura.id}"



# ---------- EMAIL VERIFICATION CODE (ANTIGUO) ----------
class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)



    def is_expired(self):
        # 💡 Usamos la función timedelta definida localmente para no reimportar.
        return timezone.now() > self.created_at + timedelta(minutes=10)



    def __str__(self):
        return f"{self.email} - {self.code}"



# ---------- ✅ EMAIL VERIFICATION (NUEVO - PARA REGISTRO) ----------
class EmailVerification(models.Model):
    """
    🔐 Modelo para verificación de email durante el registro
    """
    email = models.EmailField(verbose_name="Email")
    code = models.CharField(max_length=6, verbose_name="Código")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha creación")
    is_verified = models.BooleanField(default=False, verbose_name="Verificado")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Verificación de Email"
        verbose_name_plural = "Verificaciones de Email"
        db_table = 'email_verifications'
    
    def __str__(self):
        status = "Verificado" if self.is_verified else "Pendiente"
        return f"{self.email} - {self.code} ({status})"
    
    def is_expired(self):
        """Verifica si el código expiró (10 minutos)"""
        expiration_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiration_time
    
    @staticmethod
    def generate_code():
        """Genera un código aleatorio de 6 dígitos"""
        return str(random.randint(100000, 999999))



# ---------- ✅ PASSWORD RESET CODE ----------
class PasswordResetCode(models.Model):
    """
    🔐 Modelo para códigos de recuperación de contraseña
    """
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='reset_codes',
        verbose_name="Usuario"
    )
    code = models.CharField(
        max_length=6, 
        verbose_name="Código de verificación"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    expires_at = models.DateTimeField(
        verbose_name="Fecha de expiración"
    )
    used = models.BooleanField(
        default=False, 
        verbose_name="Código usado"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Código de Recuperación"
        verbose_name_plural = "Códigos de Recuperación"
        db_table = 'password_reset_codes'
    
    def __str__(self):
        status = "Usado" if self.used else "Activo"
        return f"Código {self.code} para {self.usuario.email} - {status}"
    
    def is_valid(self):
        """Verifica si el código aún es válido"""
        return not self.used and self.expires_at > timezone.now()
