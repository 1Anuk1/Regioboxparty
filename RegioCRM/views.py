from django.conf import settings
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from datetime import datetime
from decimal import Decimal, InvalidOperation
from RegioCore.models import CLIENTE, CATEGORIA, PRODUCTO, COTIZACION, DETALLE_COTIZACION
import string, random, os

# Create your views here.
PASSWORD_SECRETA = "123"

# Vista para inicio de sesión
def login_crm(request):
    error = None
    if request.method == "POST":
        password = request.POST.get('password')
        
        if password == PASSWORD_SECRETA:
            request.session['crm_logged_in'] = True
            return redirect('regiocrm:dashboard_crm')
        else:
            error = "Contraseña incorrecta."
    
    return render(request, 'regiocrm/login.html', {'error': error})

# Vista para cerrar sesión
def logout_crm(request):
    request.session.flush()
    return redirect('regiocrm:login_crm')

# Decorador para proteger vistas
def crm_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get('crm_logged_in'):
            return view_func(request, *args, **kwargs)
        return redirect('regiocrm:login_crm')
    return wrapper

# Vista para el inicio (dashboard)
@crm_login_required
def dashboard_crm(request):
    # KPIs
    total_clientes = CLIENTE.objects.filter(activo=True).count()
    clientes_mes = CLIENTE.objects.filter(activo=True,fecha_registro__month=datetime.now().month).count()
    total_cotizaciones = COTIZACION.objects.filter(activo=True).count()
    cot_aprobadas = COTIZACION.objects.filter(activo=True, estado='aprobado').count()

    # Clientes por origen
    clientes_origen = CLIENTE.objects.values('origen').annotate(total=Count('idCliente'))
    origen_labels = [c['origen'].capitalize() for c in clientes_origen]
    origen_values = [c['total'] for c in clientes_origen]

    # Productos más cotizados (top 5)
    productos_top = DETALLE_COTIZACION.objects.values('producto__nombre').annotate(total_cotizaciones=Count('idDetCotizacion')).order_by('-total_cotizaciones')[:5]
    productos_labels = [p['producto__nombre'] for p in productos_top]
    productos_values = [p['total_cotizaciones'] for p in productos_top]

    # Últimas 5 cotizaciones
    ultimas_cotizaciones = COTIZACION.objects.filter(activo=True).order_by('-fecha_solicitud')[:5]

    # Cotizaciones por estado
    estado_labels = ['Pendiente', 'Aprobada', 'Rechazada', 'Revisado']
    estado_values = [
        COTIZACION.objects.filter(estado='pendiente').count(),
        COTIZACION.objects.filter(estado='aprobado').count(),
        COTIZACION.objects.filter(estado='rechazado').count(),
        COTIZACION.objects.filter(estado='revisado').count(),
    ]

    # Cotizaciones por origen
    cot_origen = COTIZACION.objects.values('origen').annotate(total=Count('idCotizacion'))
    cot_origen_labels = [c['origen'].capitalize() for c in cot_origen]
    cot_origen_values = [c['total'] for c in cot_origen]

    context = {
        'total_clientes': total_clientes,
        'clientes_mes': clientes_mes,
        'total_cotizaciones': total_cotizaciones,
        'cot_aprobadas': cot_aprobadas,
        'origen_labels': origen_labels,
        'origen_values': origen_values,
        'productos_labels': productos_labels,
        'productos_values': productos_values,
        'ultimas_cotizaciones': ultimas_cotizaciones,
        'estado_labels': estado_labels,
        'estado_values': estado_values,
        'cot_origen_labels': cot_origen_labels,
        'cot_origen_values': cot_origen_values,
    }
    
    return render(request, 'regiocrm/dashboard.html', context)

# Vista para el apartado de clientes
@crm_login_required
def clientes_crm(request):
    # Función para obtener clientes y aplicar paginación
    def obtener_clientes():
        clientes = CLIENTE.objects.all().order_by('-activo', 'idCliente')
        paginator = Paginator(clientes, 10)
        page_number = request.GET.get('page')
        return paginator.get_page(page_number)

    # Función para generar contraseña temporal
    def generar_password(longitud=10):
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(random.choice(chars) for _ in range(longitud))

    # Función para envío de correo
    def enviar_correo_bienvenida(cliente, password_temp, request):
        subject = "Bienvenido a Regio Box Party"
        to = [cliente.correo]
        from_email = settings.EMAIL_HOST_USER

        login_url = request.build_absolute_uri("/login/")  # link al login del portal

        html_message = render_to_string("regiocrm/texto_correo_bienvenida.html", {
            "cliente": cliente,
            "password": password_temp,
            "login_url": login_url
        })

        email_message = EmailMultiAlternatives(subject, html_message, from_email, to)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

    # Cambiar estado de cliente (borrado lógico o reactivación)
    for parametro, estado in [('delete_id', False), ('activate_id', True)]:
        cliente_id = request.GET.get(parametro)
        if cliente_id:
            cliente = CLIENTE.objects.filter(idCliente=cliente_id).first()
            if cliente:
                cliente.activo = estado
                cliente.save()
            return redirect('regiocrm:clientes_crm')

    # Añadir o editar cliente
    if request.method == "POST":
        cliente_id = request.POST.get('cliente_id')
        nombre = request.POST.get('nombre', '').strip()
        apellido = request.POST.get('apellido', '').strip()
        correo = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        errores = []

        # Validaciones básicas
        if not nombre: errores.append("El nombre es obligatorio.")
        if not apellido: errores.append("El apellido es obligatorio.")

        # Validar correo
        validator = EmailValidator()
        try:
            validator(correo)
        except ValidationError:
            errores.append("El correo no es válido.")

        # Validar teléfono
        if telefono:
            permitido = set("0123456789 +-")
            if not all(c in permitido for c in telefono):
                errores.append("El teléfono solo puede contener números, espacios, + o guiones.")
            numeros = ''.join(c for c in telefono if c.isdigit())
            if len(numeros) < 8 or len(numeros) > 15:
                errores.append("El teléfono debe tener entre 8 y 15 dígitos.")

        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
        # Revisar duplicados considerando el borrado lógico
        cliente_existente = CLIENTE.objects.filter(correo=correo).exclude(idCliente=cliente_id).first()
        if cliente_existente:
            if cliente_existente.activo:
                errores.append("El correo ya está registrado.")
            else:
                # Reactivar cliente inactivo
                if not cliente_id:
                    cliente_existente.activo = True
                    cliente_existente.nombre = nombre
                    cliente_existente.apellido = apellido
                    cliente_existente.telefono = telefono
                    cliente_existente.save()
                    if is_ajax:
                        return JsonResponse({'success': True, 'mensaje': 'Cliente reactivado y actualizado correctamente.'})
                    return redirect('regiocrm:clientes_crm')

        # Si hay errores, renderizamos con datos
        if errores:
            if is_ajax:
                return JsonResponse({'success': False, 'errores': errores}, status=400)
            else:
                clientes_page = obtener_clientes()
                return render(request, 'regiocrm/clientes.html', {
                    'errores': errores,
                    'form_data': request.POST,
                    'clientes': clientes_page
                })

        # Procesamos sin errores
        if cliente_id:
            # Editar cliente existente
            cliente = CLIENTE.objects.filter(idCliente=cliente_id).first()
            if cliente:
                cliente.nombre = nombre
                cliente.apellido = apellido
                cliente.correo = correo
                cliente.telefono = telefono
                cliente.save()
        else:
            # Crear cliente nuevo
            password_temp = generar_password()
            cliente = CLIENTE(
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                acepta_terminos=True,
                activo=True,
                origen='crm'
            )
            cliente.set_password(password_temp)
            cliente.save()
            # Enviar correo de bienvenida
            enviar_correo_bienvenida(cliente, password_temp, request)

        if is_ajax:
            return JsonResponse({'success': True, 'mensaje': 'Cliente actualizado correctamente.'})

        return redirect('regiocrm:clientes_crm')

    # Mostrar clientes
    clientes_page = obtener_clientes()
    return render(request, 'regiocrm/clientes.html', {'clientes': clientes_page})

# Vista para el apartado del catálogo
@crm_login_required
def catalogo_crm(request):
    categorias = CATEGORIA.objects.filter(activo=True).order_by('nombre')
    productos_qs = PRODUCTO.objects.all().order_by("nombre")
    acordeon_abierto = request.GET.get("acordeon", "")

    search = request.GET.get("search", "").strip()
    if search:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=search) | Q(categoria__nombre__icontains=search)
        )

    # Paginación
    paginator = Paginator(productos_qs, 6)
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    return render(request, "regiocrm/catalogo.html", {
        "categorias": categorias,
        "productos": productos,
        "acordeon_abierto": acordeon_abierto,
        "errores_cat": [],
        "errores_prod": [],
        "categoria_guardada": False,
        "producto_guardado": False,
        "mensaje_guardado": "",
        "search": search
    })

# Vista para la gestión de categorías
@crm_login_required
def catalogo_categorias_crm(request):
    categorias = CATEGORIA.objects.filter(activo=True).order_by('nombre')
    productos_qs = PRODUCTO.objects.all().order_by('nombre')
    errores_cat = []
    categoria_guardada = False
    mensaje_guardado = ""
    acordeon_abierto = "categorias"

    search = request.GET.get("search", "").strip()
    if search:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=search) | Q(categoria__nombre__icontains=search)
        )

    # Paginación
    paginator = Paginator(productos_qs, 6)
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        id_categoria = request.POST.get("idCategoria")
        nombre = (request.POST.get("nombre") or "").strip()

        if tipo == "categoria":
            # Validaciones
            if not nombre:
                errores_cat.append("El nombre de la categoría no puede estar vacío.")
            else:
                qs_activa = CATEGORIA.objects.filter(nombre__iexact=nombre, activo=True)
                if id_categoria:
                    qs_activa = qs_activa.exclude(idCategoria=id_categoria)
                if qs_activa.exists():
                    errores_cat.append(f"Ya existe una categoría activa con el nombre '{nombre}'.")

            if not errores_cat:
                inactiva = CATEGORIA.objects.filter(nombre__iexact=nombre, activo=False).first()
                if inactiva:
                    if id_categoria:  # edición
                        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                            return JsonResponse({'success': False, 'conflict_inactive': True, 'id': inactiva.idCategoria,
                                'nombre': inactiva.nombre, 'message': f"Ya existe una categoría inactiva con el nombre '{nombre}'. ¿Deseas reactivarla?"}, status=400)
                        else:
                            errores_cat.append(f"Existe una categoría inactiva con el nombre '{nombre}'. Debes reactivarla.")
                    else:  # creación automática
                        inactiva.activo = True
                        inactiva.save()
                        categoria_guardada = True
                        mensaje_guardado = f"Categoría '{nombre}' guardada correctamente."
                        id_categoria = inactiva.idCategoria

            if not errores_cat and not categoria_guardada:
                if id_categoria:
                    cat = CATEGORIA.objects.filter(idCategoria=id_categoria).first()
                    if cat:
                        cat.nombre = nombre
                        cat.save()
                        categoria_guardada = True
                        mensaje_guardado = "Categoría editada correctamente."
                    else:
                        errores_cat.append("No se encontró la categoría a editar.")
                else:
                    nueva = CATEGORIA.objects.create(nombre=nombre)
                    categoria_guardada = True
                    mensaje_guardado = f"Categoría '{nombre}' guardada correctamente."
                    id_categoria = nueva.idCategoria

            # Respuesta AJAX
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if errores_cat:
                    return JsonResponse({'success': False, 'errors': errores_cat}, status=400)
                if categoria_guardada:
                    return JsonResponse({'success': True, 'nombre': nombre, 'message': mensaje_guardado, 'idCategoria': id_categoria})
                
        elif tipo == "eliminar_categoria" and id_categoria:
            cat = CATEGORIA.objects.filter(idCategoria=id_categoria).first()
            if cat:
                cat.activo = False
                cat.save()
                # Desactivar todos los productos de esa categoría
                PRODUCTO.objects.filter(categoria=cat, activo=True).update(activo=False)
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'idCategoria': cat.idCategoria})

        elif tipo == "reactivar_categoria" and id_categoria:
            cat = CATEGORIA.objects.filter(idCategoria=id_categoria).first()
            if cat:
                cat.activo = True
                cat.save()
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': True, 'idCategoria': cat.idCategoria, 'nombre': cat.nombre})

    return render(request, "regiocrm/catalogo.html", {
        "categorias": categorias,
        "productos": productos,
        "errores_cat": errores_cat,
        "categoria_guardada": categoria_guardada,
        "mensaje_guardado": mensaje_guardado,
        "acordeon_abierto": acordeon_abierto,
        "search": search
    })

# Vista para la gestión de productos
@crm_login_required
def catalogo_productos_crm(request):
    productos_qs = PRODUCTO.objects.all().order_by('nombre')
    errores_prod = []
    producto_guardado = False
    mensaje_guardado = ""
    acordeon_abierto = "productos"

    search = request.GET.get("search", "").strip()
    if search:
        productos_qs = productos_qs.filter(
            Q(nombre__icontains=search) | Q(categoria__nombre__icontains=search) | Q(idProducto__icontains=search)
        )

    # Paginación
    paginator = Paginator(productos_qs, 6)
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    if request.method == "POST":
        tipo = request.POST.get("tipo")

        if tipo == "producto":
            # Datos del formulario
            id_producto = request.POST.get("idProducto")
            id_producto_string = (request.POST.get("idProducto_string") or "").strip()
            nombre = (request.POST.get("nombre") or "").strip()
            categoria_id = request.POST.get("categoria")
            descripcion = (request.POST.get("descripcion") or "").strip()
            precio = request.POST.get("precio")
            activo = request.POST.get("activo") == "on"
            imagen = request.FILES.get("imagen")

            # Validaciones
            if not id_producto_string:
                errores_prod.append("El ID del producto es obligatorio.")
            else:
                # Verificar si el ID ya existe (solo para nuevos productos)
                if not id_producto:  # Es un nuevo producto
                    if PRODUCTO.objects.filter(idProducto=id_producto_string).exists():
                        errores_prod.append("El ID del producto ya existe. Por favor, usa un ID único.")
                else:  # Es una edición
                    if PRODUCTO.objects.filter(idProducto=id_producto_string).exclude(idProducto=id_producto).exists():
                        errores_prod.append("El ID del producto ya existe. Por favor, usa un ID único.")

            if not nombre:
                errores_prod.append("El nombre del producto es obligatorio.")
            if not descripcion:
                errores_prod.append("La descripción es obligatoria.")

            cat = None
            if not categoria_id:
                errores_prod.append("Debes seleccionar una categoría.")
            else:
                try:
                    cat = CATEGORIA.objects.get(idCategoria=categoria_id)
                    # NO permitimos usar una categoría inactiva al crear o al editar
                    if not cat.activo:
                        errores_prod.append("No puedes asignar una categoría inactiva. Reactiva la categoría o elige otra activa.")
                except CATEGORIA.DoesNotExist:
                    errores_prod.append("Categoría no encontrada.")

            # Precio
            try:
                precio_val = Decimal(precio)
                if precio_val < 0:
                    errores_prod.append("El precio no puede ser negativo.")
            except (InvalidOperation, TypeError, ValueError):
                errores_prod.append("Precio inválido.")

            # Validar imagen si se sube
            if imagen:
                if imagen.size > 2 * 1024 * 1024:
                    errores_prod.append(f"La imagen no puede pesar más de 2 MB.")
                ext = imagen.name.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                    errores_prod.append("Formato de imagen no válido. Solo se permiten JPG, JPEG, PNG o GIF.")

            # Guardado solo si no hay errores
            if not errores_prod:
                if id_producto:  # Editar producto existente
                    try:
                        prod = PRODUCTO.objects.get(idProducto=id_producto)
                        
                        # Si por alguna razón el producto actual tiene categoría inactiva, exigimos cambiarla
                        if prod.categoria and not prod.categoria.activo and (not categoria_id or (categoria_id and int(categoria_id) == prod.categoria.idCategoria)):
                            errores_prod.append("Este producto está asociado a una categoría inactiva. Debes seleccionar una categoría activa para guardar los cambios.")
                        else:
                            # Si el ID cambió, necesitamos actualizar la instancia correctamente
                            if id_producto_string != id_producto:
                                # Creamos una nueva instancia con el nuevo ID y copiamos los datos
                                nuevo_prod = PRODUCTO(
                                    idProducto=id_producto_string,
                                    nombre=nombre,
                                    categoria=cat or prod.categoria,
                                    descripcion=descripcion,
                                    precio=precio_val or None,
                                    activo=activo,
                                    imagen=prod.imagen  # Mantener la imagen actual por defecto
                                )
                                
                                # Si hay una nueva imagen, la asignamos
                                if imagen:
                                    nuevo_prod.imagen = imagen
                                
                                # Guardamos el nuevo producto
                                nuevo_prod.save()
                                
                                # Eliminamos el producto antiguo
                                prod.delete()
                                
                                prod = nuevo_prod
                            else:
                                # Si el ID no cambió, actualizamos normalmente
                                prod.nombre = nombre
                                prod.categoria = cat or prod.categoria
                                prod.descripcion = descripcion
                                prod.precio = precio_val or None
                                prod.activo = activo
                                if imagen:
                                    prod.imagen = imagen
                                prod.save()
                            
                            producto_guardado = True
                            mensaje_guardado = f"Producto '{prod.nombre}' editado correctamente."
                            
                    except PRODUCTO.DoesNotExist:
                        errores_prod.append("Producto no encontrado.")
                        
                else:  # Crear nuevo producto
                    prod = PRODUCTO.objects.create(
                        idProducto=id_producto_string,  # Nuevo campo string
                        nombre=nombre,
                        categoria=cat,
                        descripcion=descripcion,
                        precio=precio_val or None,
                        activo=activo,
                        imagen=imagen
                    )
                    producto_guardado = True
                    mensaje_guardado = f"Producto '{prod.nombre}' guardado correctamente."

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if errores_prod:
                    return JsonResponse({"success": False, "errors": errores_prod})
                return JsonResponse({"success": True, "message": mensaje_guardado})

        # Cambiar entre activar/inactivar
        elif tipo == "cambiar_estado_producto":
            id_producto = request.POST.get("idProducto")
            if id_producto:
                try:
                    prod = PRODUCTO.objects.get(idProducto=id_producto)
                    accion_ok = False
                    # Si intentan activar y la categoría del producto está inactiva, impedirlo
                    if not prod.activo:  # se intenta activar
                        # si no tiene categoria o la categoria está inactiva, bloquear
                        if not prod.categoria or not getattr(prod.categoria, 'activo', False):
                            # Respuesta para AJAX
                            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                                return JsonResponse({"success": False, "errors": ["No se puede activar el producto porque su categoría está inactiva. Reactiva la categoría primero o edita la categoría del producto."]})
                            else:
                                errores_prod.append("No se puede activar el producto porque su categoría está inactiva. Reactiva la categoría primero o edita la categoría del producto.")
                        else:
                            prod.activo = True
                            prod.save()
                            accion_ok = True
                            mensaje_guardado = f"Producto '{prod.nombre}' ahora está publicado."
                    else:
                        # desactivar (si ya está activo)
                        prod.activo = False
                        prod.save()
                        accion_ok = True
                        mensaje_guardado = f"Producto '{prod.nombre}' ahora está no publicado."

                    # Sólo responder éxito si la acción se realizó
                    if accion_ok and request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({"success": True, "message": mensaje_guardado, "activo": prod.activo})
                    
                except PRODUCTO.DoesNotExist:
                    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                        return JsonResponse({"success": False, "errors": ["Producto no encontrado."]})

    if request.method == "GET":
        acordeon_abierto = request.GET.get("acordeon", "productos")

    return render(request, "regiocrm/catalogo.html", {
        "categorias": CATEGORIA.objects.filter(activo=True).order_by('nombre'),
        "productos": productos,
        "errores_prod": errores_prod,
        "producto_guardado": producto_guardado,
        "mensaje_guardado": mensaje_guardado,
        "acordeon_abierto": acordeon_abierto,
        "search": search
    })

# Vista para el apartado de cotizaciones
@crm_login_required
def cotizaciones_crm(request):
    print("🔍 COTIZACIONES_CRM - Iniciando vista")
    clientes_qs = CLIENTE.objects.filter(activo=True).order_by('nombre')
    productos_qs = PRODUCTO.objects.filter(activo=True).order_by('nombre')
    cotizaciones_list = COTIZACION.objects.prefetch_related('detalles__producto').order_by('-fecha_solicitud')

    print(f"📊 Datos cargados - Clientes: {clientes_qs.count()}, Productos: {productos_qs.count()}, Cotizaciones: {cotizaciones_list.count()}")

    errores = []
    form_data = {}
    mostrar_exito = request.session.pop('mostrar_exito', False)

    cliente_op = [{'id': c.idCliente, 'nombre': f"{c.nombre} {c.apellido}", 'selected': False} for c in clientes_qs]
    tipo_entrega_op = [
        {'value': 'domicilio', 'label': 'Envío a domicilio', 'selected': False},
        {'value': 'recogida', 'label': 'Recogida en tienda', 'selected': False},
    ]
    estado_op = [
        {'value': 'pendiente', 'label': 'Pendiente', 'selected': False},
        {'value': 'revisado', 'label': 'Revisado', 'selected': False},
        {'value': 'aprobado', 'label': 'Aprobado', 'selected': False},
        {'value': 'rechazado', 'label': 'Rechazado', 'selected': False},
    ]

    # Listado paginado
    paginator = Paginator(cotizaciones_list, 10)
    page_number = request.GET.get('page')
    cotizaciones = paginator.get_page(page_number)

    if request.method == "POST":
        print("📨 COTIZACIONES_CRM - Método POST recibido")
        print(f"📦 POST data: {dict(request.POST)}")
        print(f"📦 FILES data: {dict(request.FILES)}")
        
        # VERIFICAR SI ES EDICIÓN
        if request.POST.get('editar_cotizacion'):
            print("🔄 COTIZACIONES_CRM - Modo EDICIÓN detectado")
            cotizacion_id = request.POST.get('cotizacion_id')
            tipo_entrega = request.POST.get('tipo_entrega')
            estado = request.POST.get('estado')
            comentarios = request.POST.get('comentarios', '').strip()
            
            print(f"📝 Datos edición - ID: {cotizacion_id}, Tipo entrega: {tipo_entrega}, Estado: {estado}")
            
            errores_edicion = []
            
            # Validaciones básicas para edición
            if tipo_entrega not in ['domicilio', 'recogida']:
                errores_edicion.append("Debe seleccionar un tipo de entrega válido.")
            if estado not in ['pendiente', 'revisado', 'aprobado', 'rechazado']:
                errores_edicion.append("Debe seleccionar un estado válido.")
                
            # Validar domicilio si aplica
            if tipo_entrega == 'domicilio':
                calle = request.POST.get('calle', '').strip()
                numero = request.POST.get('numero', '').strip()
                colonia = request.POST.get('colonia', '').strip()
                ciudad = request.POST.get('ciudad', '').strip()
                estado_domicilio = request.POST.get('estado_domicilio', '').strip()
                cp = request.POST.get('codigo_postal', '').strip()
                
                print(f"🏠 Datos domicilio - Calle: {calle}, Número: {numero}, Colonia: {colonia}, Ciudad: {ciudad}, Estado: {estado_domicilio}, CP: {cp}")
                
                if not calle:
                    errores_edicion.append("La calle es obligatoria.")
                if not numero:
                    errores_edicion.append("El número es obligatorio.")
                elif not numero.isdigit():
                    errores_edicion.append("El número debe contener solo dígitos.")
                if not colonia:
                    errores_edicion.append("La colonia es obligatoria.")
                if not ciudad:
                    errores_edicion.append("La ciudad/municipio es obligatorio.")
                if not estado_domicilio:
                    errores_edicion.append("El estado del domicilio es obligatorio.")
                if not cp:
                    errores_edicion.append("El código postal es obligatorio.")
                elif not cp.isdigit() or len(cp) != 5:
                    errores_edicion.append("El código postal debe tener 5 números.")
            
            # Validar productos editables
            productos_editar = request.POST.getlist('producto_editar')
            cantidades_editar = request.POST.getlist('cantidad_editar')
            
            print(f"📦 Productos recibidos - IDs: {productos_editar}, Cantidades: {cantidades_editar}")
            
            # Filtrar productos vacíos
            productos_filtrados = []
            cantidades_filtradas = []
            
            for i, prod_id in enumerate(productos_editar):
                if prod_id and cantidades_editar[i]:  # Solo incluir si ambos tienen valor
                    try:
                        cant = int(cantidades_editar[i])
                        if cant > 0:
                            productos_filtrados.append(prod_id)
                            cantidades_filtradas.append(cant)
                    except (ValueError, TypeError):
                        print(f"⚠️ Cantidad inválida ignorada - Producto: {prod_id}, Cantidad: {cantidades_editar[i]}")
                        pass  # Ignorar cantidades inválidas
            
            print(f"✅ Productos filtrados - IDs: {productos_filtrados}, Cantidades: {cantidades_filtradas}")
            
            if not productos_filtrados:
                errores_edicion.append("Debe agregar al menos un producto válido.")
            else:
                # Validar que todos los productos existan
                for i, prod_id in enumerate(productos_filtrados):
                    if not PRODUCTO.objects.filter(idProducto=prod_id, activo=True).exists():
                        errores_edicion.append(f"El producto en fila {i+1} no existe o no está activo.")
            
            # Si es AJAX, responder con JSON
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
            print(f"🌐 Es AJAX: {is_ajax}")
            
            if not errores_edicion:
                try:
                    print(f"🔍 Buscando cotización ID: {cotizacion_id}")
                    cotizacion = COTIZACION.objects.get(idCotizacion=cotizacion_id)
                    print(f"✅ Cotización encontrada: {cotizacion}")
                    
                    # Obtener productos actuales antes de eliminar
                    productos_actuales = list(cotizacion.detalles.values_list('producto_id', 'cantidad'))
                    print(f"📊 Productos actuales antes de editar: {productos_actuales}")
                    
                    # Actualizar datos básicos
                    cotizacion.tipo_entrega = tipo_entrega
                    cotizacion.estado = estado
                    cotizacion.comentarios = comentarios
                    
                    # Actualizar domicilio si es necesario
                    if tipo_entrega == 'domicilio':
                        cotizacion.calle = calle
                        cotizacion.numero = numero
                        cotizacion.colonia = colonia
                        cotizacion.ciudad = ciudad
                        cotizacion.estado_domicilio = estado_domicilio
                        cotizacion.codigo_postal = cp
                    else:
                        # Limpiar campos de domicilio si no es domicilio
                        cotizacion.calle = ''
                        cotizacion.numero = ''
                        cotizacion.colonia = ''
                        cotizacion.ciudad = ''
                        cotizacion.estado_domicilio = ''
                        cotizacion.codigo_postal = ''
                    
                    # ACTUALIZAR PRODUCTOS - SOLUCIÓN DEFINITIVA
                    print("🗑️ Eliminando productos existentes...")
                    detalles_eliminados = cotizacion.detalles.all().delete()
                    print(f"✅ Productos eliminados: {detalles_eliminados}")
                    
                    # Crear nuevos productos
                    total = Decimal('0.00')
                    
                    print(f"🆕 Creando {len(productos_filtrados)} nuevos productos...")
                    
                    for i, prod_id in enumerate(productos_filtrados):
                        producto = PRODUCTO.objects.get(idProducto=prod_id)
                        cantidad = cantidades_filtradas[i]
                        
                        precio_unitario = producto.precio or Decimal('0.00')
                        
                        print(f"➕ Creando detalle - Producto: {producto.nombre}, Cantidad: {cantidad}, Precio unitario: {precio_unitario}")
                        
                        # Crear detalle de cotización
                        detalle = DETALLE_COTIZACION.objects.create(
                            cotizacion=cotizacion,
                            producto=producto,
                            cantidad=cantidad,
                            precio_estimado=precio_unitario * cantidad
                        )
                        
                        print(f"✅ Detalle creado: {detalle}")
                        
                        total += precio_unitario * cantidad
                    
                    # Actualizar totales
                    cotizacion.total_estimado = total
                    
                    print(f"💰 Total actualizado: {total}")
                    
                    # Guardar cambios en la cotización
                    cotizacion.save()
                    print("💾 Cotización guardada exitosamente")
                    
                    if is_ajax:
                        print("📨 Enviando respuesta AJAX exitosa")
                        return JsonResponse({
                            'success': True, 
                            'mensaje': 'Cotización actualizada correctamente.'
                        })
                    else:
                        print("🔄 Redirigiendo con éxito")
                        request.session['mostrar_exito'] = True
                        return redirect('regiocrm:cotizaciones_crm')
                        
                except COTIZACION.DoesNotExist:
                    error_msg = "Cotización no encontrada."
                    print(f"❌ {error_msg}")
                    errores_edicion.append(error_msg)
                except PRODUCTO.DoesNotExist as e:
                    error_msg = "Uno o más productos no existen."
                    print(f"❌ {error_msg}: {e}")
                    errores_edicion.append(error_msg)
                except Exception as e:
                    error_msg = f"Error al actualizar: {str(e)}."
                    print(f"❌ {error_msg}")
                    errores_edicion.append(error_msg)
            
            print(f"❌ Errores de edición: {errores_edicion}")
            
            # Si hay errores, responder con ellos
            if is_ajax:
                print("📨 Enviando respuesta AJAX con errores")
                return JsonResponse({'success': False, 'errores': errores_edicion}, status=400)
            else:
                # Si no es AJAX, recargar la página con errores
                print("🔄 Redirigiendo con errores")
                request.session['errores_edicion'] = errores_edicion
                return redirect('regiocrm:cotizaciones_crm')
        
        # LÓGICA ORIGINAL PARA CREAR COTIZACIÓN
        else:
            print("🆕 COTIZACIONES_CRM - Modo CREACIÓN detectado")
            form_data = request.POST.copy()
            cliente_id = request.POST.get('cliente')
            tipo_entrega = request.POST.get('tipo_entrega')
            estado = request.POST.get('estado')
            comentarios = request.POST.get('comentarios', '').strip()

            print(f"📝 Datos creación - Cliente: {cliente_id}, Tipo entrega: {tipo_entrega}, Estado: {estado}")

            # Marcar selects preseleccionados
            for opcion in cliente_op:
                if str(opcion['id']) == str(cliente_id):
                    opcion['selected'] = True
            for opcion in tipo_entrega_op:
                if opcion['value'] == tipo_entrega:
                    opcion['selected'] = True
            for opcion in estado_op:
                if opcion['value'] == estado:
                    opcion['selected'] = True

            # Validaciones
            if not cliente_id:
                errores.append("Debe seleccionar un cliente.")
            if tipo_entrega not in ['domicilio', 'recogida']:
                errores.append("Debe seleccionar un tipo de entrega válido.")
            if estado not in ['pendiente', 'revisado', 'aprobado', 'rechazado']:
                errores.append("Debe seleccionar un estado válido.")

            # Validar domicilio si aplica
            if tipo_entrega == 'domicilio':
                calle = request.POST.get('calle', '').strip()
                numero = request.POST.get('numero', '').strip()
                colonia = request.POST.get('colonia', '').strip()
                ciudad = request.POST.get('ciudad', '').strip()
                estado_domicilio = request.POST.get('estado_domicilio', '').strip()
                cp = request.POST.get('codigo_postal', '').strip()
                
                if not calle:
                    errores.append("La calle es obligatoria.")
                if not numero:
                    errores.append("El número es obligatorio.")
                elif not numero.isdigit():
                    errores.append("El número debe contener solo dígitos.")
                if not colonia:
                    errores.append("La colonia es obligatoria.")
                if not ciudad:
                    errores.append("La ciudad/municipio es obligatorio.")
                if not estado_domicilio:
                    errores.append("El estado del domicilio es obligatorio.")
                if not cp:
                    errores.append("El código postal es obligatorio.")
                elif not cp.isdigit() or len(cp) != 5:
                    errores.append("El código postal debe tener 5 números.")

            # Productos
            productos = request.POST.getlist('producto')
            cantidades = request.POST.getlist('cantidad')
            if not productos or all(p == '' for p in productos):
                errores.append("Debe agregar al menos un producto.")
            else:
                for i, prod_id in enumerate(productos):
                    if not prod_id:
                        errores.append(f"Producto en fila {i+1} no seleccionado.")
                    try:
                        cant = int(cantidades[i])
                        if cant <= 0:
                            errores.append(f"Cantidad inválida en producto {i+1}.")
                    except:
                        errores.append(f"Cantidad inválida en producto {i+1}.")

            # Guardar si no hay errores
            cliente = CLIENTE.objects.filter(idCliente=cliente_id).first()
            if not cliente and not errores:
                errores.append("Cliente no encontrado.")

            if not errores:
                print("✅ Creando nueva cotización...")
                cotizacion = COTIZACION.objects.create(
                    cliente=cliente,
                    tipo_entrega=tipo_entrega,
                    comentarios=comentarios,
                    origen='crm',
                    estado=estado,
                    calle=calle if tipo_entrega == 'domicilio' else '',
                    numero=numero if tipo_entrega == 'domicilio' else '',
                    colonia=colonia if tipo_entrega == 'domicilio' else '',
                    ciudad=ciudad if tipo_entrega == 'domicilio' else '',
                    estado_domicilio=estado_domicilio if tipo_entrega == 'domicilio' else '',
                    codigo_postal=cp if tipo_entrega == 'domicilio' else '',
                )

                print(f"✅ Cotización creada: {cotizacion}")

                # Guardar detalles y calcular totales
                total = Decimal('0.00')

                for i, prod_id in enumerate(productos):
                    producto = PRODUCTO.objects.filter(idProducto=prod_id).first()
                    cantidad = int(cantidades[i])
                    if producto:
                        precio_unitario = producto.precio or 0
                        detalle = DETALLE_COTIZACION.objects.create(
                            cotizacion=cotizacion,
                            producto=producto,
                            cantidad=cantidad,
                            precio_estimado=Decimal(precio_unitario) * cantidad
                        )
                        print(f"✅ Detalle creado: {detalle}")
                        total += Decimal(precio_unitario) * cantidad

                cotizacion.total_estimado = total
                cotizacion.save()

                print(f"💰 Total calculado: {total}")

                # Guardar flag de éxito en session y redirigir
                request.session['mostrar_exito'] = True
                print("🔄 Redirigiendo con éxito")
                return redirect('regiocrm:cotizaciones_crm')
            else:
                print(f"❌ Errores en creación: {errores}")

    # FUERA DEL BLOQUE POST - Render normal para GET
    print("📄 COTIZACIONES_CRM - Renderizando template GET")
    return render(request, 'regiocrm/cotizaciones.html', {
        'clientes': clientes_qs,
        'productos': productos_qs,
        'cliente_op': cliente_op,
        'tipo_entrega_op': tipo_entrega_op,
        'estado_op': estado_op,
        'cotizaciones': cotizaciones,
        'errores': errores,
        'form_data': form_data,
        'mostrar_exito': mostrar_exito,
    })

# Obtener productos de una cotización
@crm_login_required
def obtener_productos_cotizacion(request, cotizacion_id):
    try:
        cotizacion = COTIZACION.objects.get(idCotizacion=cotizacion_id)
        detalles = cotizacion.detalles.select_related('producto').all()
        
        productos = []
        for detalle in detalles:
            producto_data = {
                'id': detalle.producto.idProducto,
                'nombre': detalle.producto.nombre,
                'cantidad': detalle.cantidad,
                'precio': str(detalle.precio_estimado) if detalle.precio_estimado else "0.00",
            }
            productos.append(producto_data)
        
        return JsonResponse({'success': True, 'productos': productos}) 
    except COTIZACION.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cotización no encontrada.'}, status=404)

# Obtener productos disponibles
@crm_login_required
def obtener_productos_disponibles(request):
    productos = PRODUCTO.objects.filter(activo=True).order_by('nombre')
    productos_data = [{'id': p.idProducto, 'nombre': p.nombre} for p in productos]
    
    return JsonResponse({'success': True,'productos': productos_data})

# Vista para descargar las cotizaciones desde el CRM
@crm_login_required
def descargar_cotizacion_pdf(request, cotizacion_id):
    try:
        cot = COTIZACION.objects.get(idCotizacion=cotizacion_id)
    except COTIZACION.DoesNotExist:
        return redirect('regiocrm:cotizaciones_crm')

    detalles = cot.detalles.all()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Cotizacion_{cot.idCotizacion}.pdf"'

    doc = SimpleDocTemplate(response, pagesize=letter, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    data = []

    # Estilos personalizados
    cot_style = ParagraphStyle(name='CotData', parent=styles['Normal'], fontSize=13, leading=16, alignment=2)
    titulos_style = ParagraphStyle(name='Titulos', parent=styles['Normal'], fontSize=11.5, leading=14, spaceAfter=6, alignment=0, fontName='Helvetica-Bold')
    texto_style = ParagraphStyle(name='Textos', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=2)
    total_style = ParagraphStyle(name='TotalStyle', parent=styles['Normal'], fontName='Helvetica-BoldOblique', fontSize=11, alignment=2)
    nota_footer_style = ParagraphStyle('NotaFooter', parent=styles['Normal'], fontSize=10, fontName='Helvetica-Bold', alignment=1)
    texto_footer_style = ParagraphStyle('Footer', parent=texto_style, alignment=1)

    # Encabezado
    logo_path = os.path.join(settings.BASE_DIR, 'RegioWeb', 'static', 'regioweb', 'img', 'logo.png')
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=35*mm, height=35*mm)
    else:
        logo = Paragraph('Regio Box Party', styles['Normal'])

    # Datos de cotización
    fecha_local = timezone.localtime(cot.fecha_solicitud)
    cot_paragraph = Paragraph(f"<b>Cotización:</b> #{cot.idCotizacion}<br/><b>Fecha:</b> {fecha_local.strftime('%d/%m/%Y %H:%M')}<br/><b>Estado:</b> {cot.get_estado_display().upper()}", cot_style)

    # Tabla de encabezado (logo a la izquierda, datos totalmente a la derecha)
    header_table = Table([[logo, cot_paragraph]], colWidths=[70*mm, 110*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), 
        ('ALIGN', (1,0), (1,0), 'RIGHT'), 
        ('LEFTPADDING', (1,0), (1,0), 0), 
        ('RIGHTPADDING', (1,0), (1,0), 0), 
        ('TOPPADDING', (0,0), (-1,-1), 0)
    ]))
    data.append(header_table)
    data.append(Spacer(1, 12))

    # Datos del cliente
    data.append(Paragraph('<b>Datos del Cliente</b>', titulos_style))
    data.append(Paragraph(f"<b>Nombre:</b> {cot.cliente.nombre} {cot.cliente.apellido}", texto_style))
    data.append(Paragraph(f"<b>Correo:</b> {cot.cliente.correo}", texto_style))
    if cot.cliente.telefono:
        data.append(Paragraph(f"<b>Teléfono:</b> {cot.cliente.telefono}", texto_style))
    data.append(Spacer(1, 10))

    # Productos
    data.append(Paragraph('<b>Productos de la Cotización</b>', titulos_style))
    if detalles.exists():
        for d in detalles:
            # Manejo de imagen del producto
            if d.producto.imagen and hasattr(d.producto.imagen, 'path'):
                img_path = d.producto.imagen.path
                if os.path.exists(img_path):
                    try:
                        img = Image(img_path, width=30*mm, height=30*mm)
                    except:
                        img = Paragraph('(Imagen no disponible)', styles['Normal'])
                else:
                    img = Paragraph('(Imagen no disponible)', styles['Normal'])
            else:
                img = Paragraph('(Sin imagen)', styles['Normal'])

            producto_info = f"""
            <b>{d.producto.nombre}</b><br/>
            {d.producto.descripcion or 'Sin descripción'}<br/><br/>
            <b>Precio unitario:</b> ${ (d.producto.precio or 0):,.2f} MXN<br/>
            <b>Cantidad:</b> {d.cantidad}<br/>
            <b>Total estimado:</b> ${ (d.precio_estimado or 0):,.2f} MXN
            """
            table_producto = Table([[img, Paragraph(producto_info, texto_style)]], colWidths=[45*mm, 135*mm])
            table_producto.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'), 
                ('LEFTPADDING', (0,0), (-1,-1), 50), 
                ('RIGHTPADDING', (0,0), (-1,-1), 0), 
                ('BOTTOMPADDING', (0,0), (-1,-1), 0)
            ]))

            data.append(table_producto)
            data.append(Spacer(1, 5))
    else:
        data.append(Paragraph("No hay productos en esta cotización.", texto_style))
    data.append(Spacer(1, 10))

    # Total
    if cot.total_estimado:
        data.append(Paragraph(f"<b>TOTAL ESTIMADO:</b> ${cot.total_estimado:,.2f} MXN", total_style))
    else:
        data.append(Paragraph("<b>TOTAL ESTIMADO:</b> No calculado", total_style))
    data.append(Spacer(1, 10))

    # Datos de entrega
    data.append(Paragraph('<b>Datos de Entrega</b>', titulos_style))
    data.append(Paragraph(f"<b>Tipo:</b> {cot.get_tipo_entrega_display()}", texto_style))
    
    if cot.tipo_entrega == 'domicilio' and cot.calle:
        direccion_completa = f"{cot.calle} {cot.numero}, {cot.colonia}, {cot.codigo_postal} {cot.ciudad}, {cot.estado_domicilio.title()}"
        data.append(Paragraph(f"<b>Dirección:</b> {direccion_completa}", texto_style))
        data.append(Paragraph("<i>**Nota: Este envío tiene un cobro extra por domicilio.</i>", texto_style))
    else:
        data.append(Paragraph("<b>Dirección:</b> José López Collado 2233, Ferrocarrilera, 64250 Monterrey, N.L.", texto_style))
    data.append(Spacer(1, 10))

    # Comentarios
    data.append(Paragraph('<b>Comentarios Adicionales</b>', titulos_style))
    if cot.comentarios:
        data.append(Paragraph(cot.comentarios, texto_style))
    else:
        data.append(Paragraph("Sin comentarios.", texto_style))
    data.append(Spacer(1, 50))

    # Footer
    data.append(Paragraph("NOTA: Esta cotización fue generada desde el sistema interno.", nota_footer_style))
    data.append(Paragraph("Contáctanos:<br /> Correo: regiobox@gmail.com | WhatsApp: 81-1234-5678 | Dirección: José López Collado 2233, Ferrocarrilera, Monterrey, N.L.", texto_footer_style))

    try:
        doc.build(data)
        return response
    except Exception as e:
        # En caso de error, redirigir a la página de cotizaciones
        return redirect('regiocrm:cotizaciones_crm')
    