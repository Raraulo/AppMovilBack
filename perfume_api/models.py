from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

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
        return self.create_user(email, password, **extra_fields)

# ----------- MODELO USUARIO PERSONALIZADO -----------
class Usuario(AbstractUser):
    username = None  # 🔹 Eliminamos username
    email = models.EmailField(unique=True)  # 🔹 Email será el identificador único
    rol = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrador'),
            ('empleado', 'Empleado'),
            ('cliente', 'Cliente'),
        ],
        default='cliente'
    )

    USERNAME_FIELD = "email"  # 🔹 Ahora el login será con email
    REQUIRED_FIELDS = []      # 🔹 No pedirá username

    objects = UsuarioManager()  # ✅ Usar nuestro manager personalizado

    def __str__(self):
        return f"{self.email} - {self.rol}"


# ---------- MARCAS ----------
class Marca(models.Model):
    nombre = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.nombre


# ---------- TIPOS ----------
class Tipo(models.Model):
    nombre = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre


# ---------- PRODUCTOS ----------
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE)
    tipo = models.ForeignKey(Tipo, on_delete=models.CASCADE)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    url_imagen = models.URLField(blank=True, null=True)
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    stock = models.IntegerField(default=0)
    genero = models.CharField(max_length=10, choices=[('Hombre','Hombre'),('Mujer','Mujer')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ---------- CLIENTES ----------
class Cliente(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    cedula = models.CharField(max_length=20, unique=True, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    celular = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    sexo = models.CharField(max_length=10, choices=[('Hombre','Hombre'),('Mujer','Mujer')])
    password = models.CharField(max_length=255)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# ---------- FACTURAS ----------
class Factura(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)


# ---------- DETALLE FACTURA ----------
class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)


# ---------- EMAIL VERIFICATION ----------
class EmailVerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email} - {self.code}"
