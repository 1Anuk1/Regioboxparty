import os
import pandas as pd
from django.core.management.base import BaseCommand
from django.core.files import File
from django.db import transaction
from django.conf import settings
from RegioCore.models import PRODUCTO, CATEGORIA

class Command(BaseCommand):
    help = 'Importa productos desde el archivo Excel de RegioBox'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--sobrescribir',
            action='store_true',
            help='Sobrescribir productos existentes'
        )
    
    def handle(self, *args, **options):
        # Rutas específicas para tu caso
        ruta_excel = "Productos RegioBox 1.xlsx"
        ruta_imagenes = "Regio Box Imagenes cajas"
        sobrescribir = options['sobrescribir']
        
        if not os.path.exists(ruta_excel):
            self.stderr.write(self.style.ERROR(f'❌ Archivo Excel no encontrado: {ruta_excel}'))
            self.stdout.write("💡 Asegúrate de que el archivo esté en la raíz del proyecto")
            return
        
        if not os.path.exists(ruta_imagenes):
            self.stdout.write(self.style.WARNING(f'⚠️ Carpeta de imágenes no encontrada: {ruta_imagenes}'))
            self.stdout.write("💡 Se crearán productos sin imágenes")
        
        self.importar_productos(ruta_excel, ruta_imagenes, sobrescribir)
    
    def importar_productos(self, ruta_excel, ruta_imagenes, sobrescribir):
        try:
            # Leer el archivo Excel - empieza en A1 como dijiste
            self.stdout.write(f"📖 Leyendo archivo Excel: {ruta_excel}")
            df = pd.read_excel(ruta_excel)
            
            # Mapear nombres de columnas (los tuyos → los que espera el sistema)
            mapeo_columnas = {
                'IdProducto': 'idProducto',
                'Nombre': 'nombre', 
                'Categoría': 'categoria',
                'Descripción': 'descripcion',
                'Precio': 'precio'
            }
            
            # Renombrar columnas
            df = df.rename(columns=mapeo_columnas)
            
            self.stdout.write(f"📊 Encontradas {len(df)} filas para procesar")
            self.stdout.write("🔍 Columnas detectadas: " + ", ".join(df.columns.tolist()))
            
            productos_creados = 0
            productos_actualizados = 0
            errores = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Limpiar datos
                        id_producto = str(row['idProducto']).strip()
                        nombre_categoria = str(row['categoria']).strip()
                        nombre_producto = str(row['nombre']).strip()
                        
                        # Validar datos mínimos
                        if not id_producto or not nombre_producto or not nombre_categoria:
                            self.stdout.write(f"⏭️  Fila {index + 2}: Datos incompletos, saltando...")
                            continue
                        
                        # Buscar o crear categoría
                        categoria, cat_creada = CATEGORIA.objects.get_or_create(
                            nombre=nombre_categoria,
                            defaults={'activo': True}
                        )
                        
                        if cat_creada:
                            self.stdout.write(f"📁 Categoría creada: {nombre_categoria}")
                        
                        # Verificar si el producto existe
                        producto_existente = PRODUCTO.objects.filter(idProducto=id_producto).first()
                        
                        if producto_existente and not sobrescribir:
                            self.stdout.write(f"⏭️  Producto ya existe: {id_producto} - {nombre_producto}")
                            continue
                        
                        # Preparar datos del producto
                        datos_producto = {
                            'categoria': categoria,
                            'nombre': nombre_producto,
                            'descripcion': str(row.get('descripcion', '')).strip(),
                            'precio': self.validar_precio(row.get('precio')),
                            'activo': True  # Por defecto activo
                        }
                        
                        if producto_existente and sobrescribir:
                            # Actualizar producto existente
                            for campo, valor in datos_producto.items():
                                setattr(producto_existente, campo, valor)
                            producto = producto_existente
                            productos_actualizados += 1
                            accion = "ACTUALIZADO"
                        else:
                            # Crear nuevo producto
                            producto = PRODUCTO(
                                idProducto=id_producto,
                                **datos_producto
                            )
                            productos_creados += 1
                            accion = "CREADO"
                        
                        # BUSCAR IMAGEN AUTOMÁTICAMENTE
                        nombre_imagen = self.buscar_imagen_automaticamente(id_producto, nombre_producto, ruta_imagenes)
                        
                        if nombre_imagen:
                            ruta_imagen_completa = os.path.join(ruta_imagenes, nombre_imagen)
                            if os.path.exists(ruta_imagen_completa):
                                # Eliminar imagen anterior si existe
                                if producto.imagen:
                                    producto.imagen.delete(save=False)
                                
                                # Asignar nueva imagen
                                with open(ruta_imagen_completa, 'rb') as img_file:
                                    producto.imagen.save(nombre_imagen, File(img_file), save=False)
                                mensaje_imagen = f" + IMAGEN: {nombre_imagen}"
                            else:
                                mensaje_imagen = " - IMAGEN NO ENCONTRADA"
                                self.stdout.write(self.style.WARNING(f'   ⚠️ Imagen no encontrada: {ruta_imagen_completa}'))
                        else:
                            mensaje_imagen = " - SIN IMAGEN"
                            self.stdout.write(self.style.WARNING(f'   ⚠️ No se encontró imagen para: {nombre_producto}'))
                        
                        producto.save()
                        self.stdout.write(f"✅ {accion}: {id_producto} - {nombre_producto}{mensaje_imagen}")
                        
                    except Exception as e:
                        error_msg = f"Fila {index + 2}: {str(e)}"
                        errores.append(error_msg)
                        self.stderr.write(self.style.ERROR(f'❌ {error_msg}'))
                        continue
            
            # Mostrar resumen
            self.stdout.write("\n" + "="*50)
            self.stdout.write(self.style.SUCCESS("📊 RESUMEN DE IMPORTACIÓN"))
            self.stdout.write("="*50)
            self.stdout.write(f"✅ Productos creados: {productos_creados}")
            self.stdout.write(f"🔄 Productos actualizados: {productos_actualizados}")
            self.stdout.write(f"❌ Errores: {len(errores)}")
            
            if errores:
                self.stdout.write("\n📋 Errores detallados:")
                for error in errores:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
                    
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Error general: {str(e)}'))
    
    def validar_precio(self, precio):
        """Valida y convierte el precio"""
        if pd.isna(precio) or precio == '' or precio is None:
            return 0.0
        
        try:
            return float(precio)
        except (ValueError, TypeError):
            return 0.0
    
    def buscar_imagen_automaticamente(self, id_producto, nombre_producto, ruta_imagenes):
        """Busca automáticamente imágenes basándose en ID o nombre del producto"""
        if not os.path.exists(ruta_imagenes):
            return None
            
        # Extensiones de imagen permitidas
        extensiones = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        
        # Intentar encontrar por ID del producto
        for ext in extensiones:
            nombre_posible = f"{id_producto}{ext}"
            ruta_posible = os.path.join(ruta_imagenes, nombre_posible)
            if os.path.exists(ruta_posible):
                return nombre_posible
        
        # Intentar encontrar por nombre (limpio de caracteres especiales)
        nombre_limpio = "".join(c for c in nombre_producto if c.isalnum() or c in (' ', '-', '_')).rstrip()
        for ext in extensiones:
            nombre_posible = f"{nombre_limpio}{ext}"
            ruta_posible = os.path.join(ruta_imagenes, nombre_posible)
            if os.path.exists(ruta_posible):
                return nombre_posible
        
        # Buscar cualquier archivo que contenga el ID
        for archivo in os.listdir(ruta_imagenes):
            if id_producto.lower() in archivo.lower():
                for ext in extensiones:
                    if archivo.lower().endswith(ext):
                        return archivo
        
        return None 