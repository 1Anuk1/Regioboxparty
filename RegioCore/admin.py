from django.contrib import admin
from .models import CLIENTE, DIRECCION, CATEGORIA, PRODUCTO, COTIZACION, DETALLE_COTIZACION

# Register your models here.

admin.site.register(CLIENTE)
admin.site.register(DIRECCION)
admin.site.register(CATEGORIA)
admin.site.register(PRODUCTO)
admin.site.register(COTIZACION)
admin.site.register(DETALLE_COTIZACION)
