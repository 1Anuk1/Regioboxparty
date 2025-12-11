from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.

ORIGENES = [
    ('web', 'Sitio Web'),
    ('crm', 'CRM interno'),
]

class CLIENTE(models.Model):
    idCliente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=15, null=True, blank=True)
    contraseña = models.CharField(max_length=128)
    acepta_terminos = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    origen = models.CharField(max_length=10, choices=ORIGENES, default='web')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'CLIENTE'
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self):
        return f"ID: {self.idCliente} - {self.nombre} {self.apellido}"

    # Método para guardar contraseña hasheada
    def set_password(self, raw_password):
        self.contraseña = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.contraseña)

class DIRECCION(models.Model):
    idDireccion = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(CLIENTE, on_delete=models.CASCADE, related_name="direcciones")
    calle = models.CharField(max_length=150)
    numero = models.CharField(max_length=10)
    colonia = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    estado = models.CharField(max_length=100)
    codigo_postal = models.CharField(max_length=10)
    dir_principal = models.BooleanField(default=False)  # Para marcar dirección principal
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DIRECCION'
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"

    def __str__(self):
        return f"ID: {self.idDireccion} - Cliente: {self.cliente.idCliente} / {self.calle} {self.numero}, {self.ciudad}"

class CATEGORIA(models.Model):
    idCategoria = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'CATEGORIA'
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return f"ID: {self.idCategoria} - {self.nombre}"
    
class PRODUCTO(models.Model):
    idProducto = models.CharField(primary_key=True, max_length=100)
    categoria = models.ForeignKey(CATEGORIA, on_delete=models.CASCADE, related_name='productos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='productos/', blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'PRODUCTO'
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"ID: {self.idProducto} - {self.nombre} (Categoría: {self.categoria.nombre})"
    
class COTIZACION(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('revisado', 'Revisado'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    TIPOS_ENTREGA = [
        ('domicilio', 'Envío a domicilio'),
        ('recogida', 'Recogida en tienda'),
    ]

    idCotizacion = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(CLIENTE, on_delete=models.CASCADE, related_name='cotizaciones')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    tipo_entrega = models.CharField(max_length=50, choices=TIPOS_ENTREGA)
    
    # Campos para guardar la dirección directamente
    calle = models.CharField(max_length=150, blank=True, null=True)
    numero = models.CharField(max_length=10, blank=True, null=True)
    colonia = models.CharField(max_length=100, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado_domicilio = models.CharField(max_length=100, blank=True, null=True)
    codigo_postal = models.CharField(max_length=10, blank=True, null=True)
    
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    comentarios = models.TextField(null=True, blank=True)
    origen = models.CharField(max_length=10, choices=ORIGENES, default='web')
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'COTIZACION'
        verbose_name = "Cotizacion"
        verbose_name_plural = "Cotizaciones"

    def __str__(self):
        return f"Cotización #{self.idCotizacion} - {self.cliente.nombre}"
    
class DETALLE_COTIZACION(models.Model):
    idDetCotizacion = models.AutoField(primary_key=True)
    cotizacion = models.ForeignKey(COTIZACION, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(PRODUCTO, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_estimado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'DETALLE_COTIZACION'
        verbose_name = "Detalle de Cotizacion"
        verbose_name_plural = "Detalles de Cotizaciones"

    def __str__(self):
        return f"Cotización #{self.cotizacion.idCotizacion} - {self.producto.nombre} x {self.cantidad}"