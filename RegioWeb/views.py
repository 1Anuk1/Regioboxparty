from django.conf import settings
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.core.validators import EmailValidator
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from RegioCore.models import CLIENTE, DIRECCION, CATEGORIA, PRODUCTO, COTIZACION, DETALLE_COTIZACION
from RegioWeb.utils import generar_token, validar_token
import os

# Create your views here.

# Vista para el registro
def registro_web(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre").strip()
        apellido = request.POST.get("apellido").strip()
        correo = request.POST.get("email").strip()
        telefono = request.POST.get("telefono").strip()
        password = request.POST.get("password")
        password_confirm = request.POST.get("confirmpass")
        acepta_terminos = request.POST.get("terms-cond") == "on"

        # Lista de errores y validaciones básicas
        errores = []
        
        if not acepta_terminos: errores.append("Debes aceptar los términos y condiciones.")
        if password != password_confirm: errores.append("Las contraseñas no coinciden.")
        
        # Validar seguridad de la contraseña con Django
        try:
            validate_password(password)
        except ValidationError as e:
            errores.extend(e.messages)
        
        # Verificar si el correo es válido y/o ya está registrado
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
            # Contar solo dígitos
            numeros = ''.join(c for c in telefono if c.isdigit())
            if len(numeros) < 8 or len(numeros) > 15:
                errores.append("El teléfono debe tener entre 8 y 15 dígitos.")

        # Pasamos la lista de errores al template con los valores rellenados
        if errores:
            if errores:
                return render(request, "registro.html", {
                    "errores": errores,
                    "nombre": nombre,
                    "apellido": apellido,
                    "correo": correo,
                    "telefono": telefono
                })
            
        # Lógica de duplicado / borrado lógico
        cliente_existente = CLIENTE.objects.filter(correo=correo).first()
        if cliente_existente:
            if cliente_existente.activo:
                errores.append("El correo ya está registrado.")
                return render(request, "registro.html", {
                    "errores": errores,
                    "nombre": nombre,
                    "apellido": apellido,
                    "correo": correo,
                    "telefono": telefono
                })
            else:
                # Reactivar cliente inactivo
                cliente_existente.activo = True
                cliente_existente.nombre = nombre
                cliente_existente.apellido = apellido
                cliente_existente.telefono = telefono
                cliente_existente.set_password(password)
                cliente_existente.save()
                return render(request, "registro.html", {
                    "registro_exitoso": True,
                    "correo": correo
                })

        # Si no existe, creamos cliente nuevo
        cliente = CLIENTE(
            nombre=nombre,
            apellido=apellido,
            correo=correo,
            telefono=telefono,
            acepta_terminos=acepta_terminos,
            activo=True,
            origen='web'
        )
        cliente.set_password(password)
        cliente.save()

        # Renderizar el modal de éxito
        return render(request, "registro.html", {
            "registro_exitoso": True,
            "correo": correo
        })
    
    return render(request, "registro.html")

# Vista para el login
def login_web(request):
    errores = []
    if request.method == "POST":
        correo = request.POST.get("email")
        password = request.POST.get("password")
        remember_me = request.POST.get("rememberMe") == "on"

        try:
            cliente = CLIENTE.objects.get(correo__iexact=correo, activo=True)
        except CLIENTE.DoesNotExist:
            errores.append("El correo o la contraseña son incorrectos.")
            return render(request, "login.html", {"errores": errores, "correo": correo})

        if not cliente.check_password(password):
            errores.append("El correo o la contraseña son incorrectos.")
            return render(request, "login.html", {"errores": errores, "correo": correo})

        # Iniciar sesión con Django sessions
        request.session['cliente_id'] = cliente.idCliente
        request.session['cliente_nombre'] = cliente.nombre
        request.session['cliente_apellido'] = cliente.apellido

        if remember_me:
            request.session.set_expiry(60 * 60 * 24 * 30)  # 30 días
        else:
            request.session.set_expiry(0)  # hasta cerrar navegador

        return redirect('regioweb:usuario')

    return render(request, "login.html")

# Decorador que asegura que el usuario esté logueado como cliente.
def login_required_cliente(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            messages.error(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('regioweb:login')
        
        # Verificar que el cliente exista y esté activo
        cliente = CLIENTE.objects.filter(idCliente=cliente_id, activo=True).first()
        if not cliente:
            request.session.flush()  # cerrar sesión
            messages.error(request, "Tu cuenta está inactiva o no existe.")
            return redirect('regioweb:login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Función para obtener el cliente
def obtener_cliente_desde_sesion(request):
    # Retorna el cliente de la sesión. Si no hay sesión o el cliente no existe, limpia la sesión y retorna None.
    cliente_id = request.session.get('cliente_id')
    if not cliente_id:
        return None

    # Solo devuelve clientes activos
    cliente = CLIENTE.objects.filter(idCliente=cliente_id, activo=True).first()
    if not cliente:
        request.session.flush()
        return None
    return cliente

# Vista para el perfil del usuario
@login_required_cliente
def usuario_web(request):
    cliente = obtener_cliente_desde_sesion(request)
    # Traer direcciones del cliente, principal primero
    direcciones = DIRECCION.objects.filter(cliente=cliente).order_by('-dir_principal', '-idDireccion')
    # Traer cotizaciones del cliente
    cotizaciones = COTIZACION.objects.filter(cliente=cliente).order_by('fecha_solicitud')
    return render(request, "usuario.html", {"cliente": cliente, "direcciones": direcciones, "cotizaciones": cotizaciones,})

# Vista para actualizar información personal del usuario
@login_required_cliente
def usuario_actualizar_info(request):
    if request.method != "POST":
        return redirect('regioweb:usuario')

    cliente = obtener_cliente_desde_sesion(request)
    if not cliente:
        return redirect('regioweb:login')

    # Obtenemos datos del formulario
    nombre = request.POST.get('nombre', '').strip()
    apellido = request.POST.get('apellido', '').strip()
    correo = request.POST.get('correo', '').strip()
    telefono = request.POST.get('telefono', '').strip()

    # Lista de errores y validaciones
    errores = []
    if not nombre: errores.append("El nombre es obligatorio.")
    if not apellido: errores.append("El apellido es obligatorio.")

    # Validar correo si se proporciona
    if correo:
        validator = EmailValidator()
        try:
            validator(correo)
        except ValidationError:
            errores.append("El correo no es válido.")

    # Si cambió el correo, verificar unicidad
    if correo and correo != cliente.correo and CLIENTE.objects.filter(correo=correo).exists():
        errores.append("El correo ya está registrado por otro usuario.")

    # Manejo de cambio de contraseña
    cambiar_pwd = request.POST.get('cambiar_contrasena') == 'on'
    if cambiar_pwd:
        actual_pwd = request.POST.get('contrasena-actual', '')
        nueva_pwd = request.POST.get('nueva-contrasena', '')
        confirm_pwd = request.POST.get('confirmar-contrasena', '')

        if not actual_pwd:
            errores.append("Debes ingresar tu contraseña actual para cambiarla.")
        else:
            if not cliente.check_password(actual_pwd):
                errores.append("La contraseña actual es incorrecta.")

        if not nueva_pwd or not confirm_pwd:
            errores.append("Debes ingresar la nueva contraseña y confirmarla.")
        elif nueva_pwd != confirm_pwd:
            errores.append("La nueva contraseña y su confirmación no coinciden.")
        else:
            # validar fuerza de contraseña (usa los validadores de Django)
            try:
                validate_password(nueva_pwd, user=None)
            except ValidationError as e:
                errores.extend(e.messages)

    # Si hay errores, los devolvemos
    if errores:
        context = {
            'cliente': cliente,
            'errores': errores
        }
        return render(request, "usuario.html", context)

    # Guardar cambios
    cliente.nombre = nombre
    cliente.apellido = apellido
    cliente.correo = correo
    cliente.telefono = telefono
    cliente.save()

    # Si cambió contraseña, guardarla
    if cambiar_pwd and nueva_pwd:
        cliente.set_password(nueva_pwd)

    # Actualizar sesión para reflejar cambios en navbar
    request.session['cliente_nombre'] = cliente.nombre
    request.session['cliente_apellido'] = cliente.apellido

    messages.success(request, "Información actualizada correctamente.", extra_tags="usuario")
    return redirect('regioweb:usuario')

# Vista para agregar dirección del usuario
@login_required_cliente
@transaction.atomic
def usuario_agregar_direccion(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": ["Método no permitido."]})
    cliente = obtener_cliente_desde_sesion(request)

    # Obtenemos datos del formulario
    calle = request.POST.get('calle', '').strip()
    numero = request.POST.get('numero', '').strip()
    colonia = request.POST.get('colonia', '').strip()
    ciudad = request.POST.get('ciudad', '').strip()
    estado = request.POST.get('estado', '').strip()
    cp = request.POST.get('codigo_postal', '').strip()
    principal = request.POST.get('principal') == 'on'

    # Lista de errores y validaciones
    errores = []
    if not calle: errores.append("La calle es obligatoria.")
    if not numero: errores.append("El número es obligatorio.")
    if numero and not numero.isdigit(): errores.append("El número debe contener solo dígitos.")
    if not colonia: errores.append("La colonia es obligatoria.")
    if not ciudad: errores.append("La ciudad es obligatoria.")
    if not estado: errores.append("El estado es obligatorio.")
    if not cp: errores.append("El código postal es obligatorio.")
    if cp and (not cp.isdigit() or len(cp) != 5): errores.append("El código postal debe tener 5 números.")

    # Si hay errores, los devolvemos
    if errores:
        return JsonResponse({"ok": False, "error": errores})

    # Si la nueva dirección será principal, desmarcamos la anterior
    if principal:
        DIRECCION.objects.filter(cliente=cliente, dir_principal=True).update(dir_principal=False)

    # Creamos la dirección
    DIRECCION.objects.create(
        cliente=cliente,
        calle=calle,
        numero=numero,
        colonia=colonia,
        ciudad=ciudad,
        estado=estado,
        codigo_postal=cp,
        dir_principal=principal
    )
    return JsonResponse({"ok": True, "msg": "Dirección agregada correctamente."})

# Vista para editar dirección del usuario
@login_required_cliente
@transaction.atomic
def usuario_editar_direccion(request, id_dir=None):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": ["Método no permitido."]})
    cliente = obtener_cliente_desde_sesion(request)

    # Prioriza el id de la URL (id_dir), si no existe lo toma del POST
    id_dir_real = id_dir or request.POST.get('id_dir')
    if not id_dir_real:
        return JsonResponse({"ok": False, "error": ["ID de dirección no proporcionado."]})

    direccion = DIRECCION.objects.filter(idDireccion=id_dir_real, cliente=cliente).first()
    if not direccion:
        return JsonResponse({"ok": False, "error": ["Dirección no encontrada."]})

    # Obtener campos
    calle = request.POST.get('calle', '').strip()
    numero = request.POST.get('numero', '').strip()
    colonia = request.POST.get('colonia', '').strip()
    ciudad = request.POST.get('ciudad', '').strip()
    estado = request.POST.get('estado', '').strip()
    cp = request.POST.get('codigo_postal', '').strip()
    principal = request.POST.get('principal') == 'on'

    # Lista de errores y validaciones
    errores = []
    if not calle: errores.append("La calle es obligatoria.")
    if not numero: errores.append("El número es obligatorio.")
    if numero and not numero.isdigit(): errores.append("El número debe contener solo dígitos.")
    if not colonia: errores.append("La colonia es obligatoria.")
    if not ciudad: errores.append("La ciudad es obligatoria.")
    if not estado: errores.append("El estado es obligatorio.")
    if not cp: errores.append("El código postal es obligatorio.")
    if cp and (not cp.isdigit() or len(cp) != 5): errores.append("El código postal debe tener 5 números.")


    if errores:
        return JsonResponse({"ok": False, "error": errores})
    
    # Actualizar dirección
    if principal:
        # Desmarcamos otras direcciones del cliente
        DIRECCION.objects.filter(cliente=cliente, dir_principal=True).update(dir_principal=False)

    direccion.calle = calle
    direccion.numero = numero
    direccion.colonia = colonia
    direccion.ciudad = ciudad
    direccion.estado = estado
    direccion.codigo_postal = cp
    direccion.dir_principal = principal
    direccion.save()

    return JsonResponse({"ok": True, "msg": "Dirección actualizada correctamente."})

# Vista para eliminar dirección del usuario
@login_required_cliente
@transaction.atomic
def usuario_eliminar_direccion(request, id_dir=None):
    if request.method != "POST":
        return redirect('/usuario/#direcciones')
    cliente = obtener_cliente_desde_sesion(request)

    # Obtenemos el id de la dirección
    id_dir_real = id_dir or request.POST.get('id_direccion')
    if not id_dir_real:
        messages.error(request, "No se proporcionó la dirección a eliminar.")
        return redirect('/usuario/#direcciones')

    # Buscar la dirección y comprobar que pertenezca al cliente
    direccion = DIRECCION.objects.filter(idDireccion=id_dir_real, cliente=cliente).first()
    if not direccion:
        messages.error(request, "Dirección no encontrada.")
        return redirect('/usuario/#direcciones')

    # Eliminar
    direccion.delete()
    messages.success(request, "Dirección eliminada correctamente.")

    return redirect('/usuario/#direcciones')  # Redirigimos y dejamos la pestaña Direcciones activa

# Vista para poner la dirección del usuario como principal
@login_required_cliente
@transaction.atomic
def usuario_direccion_principal(request, id_dir):
    if request.method != "POST":
        return redirect('/usuario/#direcciones')
    cliente = obtener_cliente_desde_sesion(request)

    direccion = DIRECCION.objects.filter(idDireccion=id_dir, cliente=cliente).first()
    if not direccion:
        messages.error(request, "Dirección no encontrada.")
        return redirect('/usuario/#direcciones')

    # Desmarcar otras y marcar esta
    DIRECCION.objects.filter(cliente=cliente, dir_principal=True).exclude(idDireccion=direccion.idDireccion).update(dir_principal=False)
    direccion.dir_principal = True
    direccion.save()

    messages.success(request, "Dirección marcada como principal.")
    return redirect('/usuario/#direcciones')

# Vista para el catálogo
def catalogo_web(request):
    categorias = CATEGORIA.objects.filter(activo=True).order_by('nombre')
    productos = PRODUCTO.objects.filter(activo=True).order_by('nombre')
    return render(request, "catalogo.html", {
        "categorias": categorias,
        "productos": productos
    })

# Vista para el carrito
def carrito_web(request):
    carrito = request.session.get('carrito', [])
    total = sum(item['precio_total'] for item in carrito)
    cliente = obtener_cliente_desde_sesion(request)
    
    # Marcar opción seleccionada
    tipo_entrega = request.session.get('tipo_entrega', 'domicilio')
    selected_domicilio = 'selected' if tipo_entrega == 'domicilio' else ''
    selected_recogida = 'selected' if tipo_entrega == 'recogida' else ''

    context = {
        'carrito': carrito,
        'total': total,
        'cliente': cliente,
        'tipo_entrega': tipo_entrega,
        'selected_domicilio': selected_domicilio,
        'selected_recogida': selected_recogida,
    }
    return render(request, 'carrito.html', context)

# Vista para agregar producto al carrito
@require_POST
def carrito_agregar_producto(request, producto_id):
    try:
        producto = PRODUCTO.objects.get(pk=producto_id)
    except PRODUCTO.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
        messages.error(request, "Producto no encontrado.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    carrito = request.session.get('carrito', [])

    for item in carrito:
        if item['producto']['idProducto'] == producto.idProducto:
            item['cantidad'] += 1
            item['precio_total'] = item['producto']['precio'] * item['cantidad']
            break
    else:
        carrito.append({
            'producto': {
                'idProducto': producto.idProducto,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'imagen': producto.imagen.url if producto.imagen else '',
                'precio': float(producto.precio),
            },
            'cantidad': 1,
            'precio_total': float(producto.precio),
        })

    request.session['carrito'] = carrito
    # Redirige a la página de donde vino
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok', 'total_items': sum(i['cantidad'] for i in carrito)})
    return redirect(request.META.get('HTTP_REFERER', '/'))

# Vista para actualizar la cantidad de producto en el carrito
@csrf_exempt
@require_POST
def carrito_actualizar_producto(request, producto_id, cantidad):
    carrito = request.session.get('carrito', [])
    for item in carrito:
        if item['producto']['idProducto'] == producto_id:
            item['cantidad'] = int(cantidad)
            item['precio_total'] = item['producto']['precio'] * int(cantidad)
            break
    request.session['carrito'] = carrito
    return JsonResponse({'status': 'ok'})

# Vista para eliminar producto del carrito
@require_POST
def carrito_eliminar_producto(request, producto_id):
    carrito = request.session.get('carrito', [])
    carrito = [item for item in carrito if item['producto']['idProducto'] != producto_id]
    request.session['carrito'] = carrito
    return redirect('regioweb:carrito')

# Vista para vacíar el carrito
@require_POST
def carrito_vaciar(request):
    if 'carrito' in request.session:
        request.session['carrito'] = []
        request.session.modified = True
    return redirect('regioweb:carrito')

# Vista para generar cotizaciones
@login_required_cliente
def generar_cotizacion(request):
    cliente = obtener_cliente_desde_sesion(request)
    carrito = request.session.get('carrito', [])

    if not carrito:
        messages.error(request, "Tu carrito está vacío.")
        return redirect('regioweb:carrito')

    # Tomar los valores directamente desde el POST
    tipo_entrega = request.POST.get('tipo_entrega', 'domicilio')
    direccion_id = request.POST.get('direccion_envio')
    comentarios = request.POST.get('comentarios', '')

    errores = []
    direccion_envio = None
    if tipo_entrega == 'domicilio':
        # Verificar si el cliente tiene direcciones registradas
        if not cliente.direcciones.exists():
            errores.append("Debes registrar al menos una dirección para envío a domicilio.")
        else:
            # Tomar la dirección seleccionada
            direccion_envio = DIRECCION.objects.filter(idDireccion=direccion_id, cliente=cliente).first()
            if not direccion_envio:
                errores.append("La dirección seleccionada no es válida.")
    # Si hay errores, renderizamos una sola vez
    if errores:
        return render(request, 'carrito.html', {
            'carrito': carrito,
            'cliente': cliente,
            'tipo_entrega': tipo_entrega,
            'selected_domicilio': 'selected' if tipo_entrega == 'domicilio' else '',
            'selected_recogida': 'selected' if tipo_entrega == 'recogida' else '',
            'total': sum(item['precio_total'] for item in carrito),
            'errores': errores,
        })

    total = sum(item['precio_total'] for item in carrito)

    # Crear cotización con los datos de la dirección copiados
    if tipo_entrega == 'domicilio' and direccion_envio:
        cotizacion = COTIZACION.objects.create(
            cliente=cliente,
            tipo_entrega=tipo_entrega,
            calle=direccion_envio.calle,
            numero=direccion_envio.numero,
            colonia=direccion_envio.colonia,
            ciudad=direccion_envio.ciudad,
            estado_domicilio=direccion_envio.estado,
            codigo_postal=direccion_envio.codigo_postal,
            total_estimado=total,
            comentarios=comentarios
        )
    else: 
        cotizacion = COTIZACION.objects.create(
            cliente=cliente,
            tipo_entrega=tipo_entrega,
            total_estimado=total,
            comentarios=comentarios
        )

    # Crear detalles
    for item in carrito:
        DETALLE_COTIZACION.objects.create(
            cotizacion=cotizacion,
            producto=PRODUCTO.objects.get(pk=item['producto']['idProducto']),
            cantidad=item['cantidad'],
            precio_estimado=item['precio_total'],
        )

    # Limpiar carrito
    request.session['carrito'] = []
    messages.success(request, "Cotización generada correctamente.")
    return render(request, 'carrito.html', {
        'carrito': [],
        'cliente': cliente,
        'cotizacion': cotizacion,
        'modal_cotizacion': True,
        'cotizacion_generada': cotizacion,
    })

# Vista para descargar las cotizaciones
@login_required_cliente
def descargar_cotizacion_pdf(request, cotizacion_id):
    cliente = obtener_cliente_desde_sesion(request)
    cot = COTIZACION.objects.filter(idCotizacion=cotizacion_id, cliente=cliente).first()
    if not cot:
        return redirect('regioweb:usuario')

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
    cot_paragraph = Paragraph(f"<b>Cotización:</b> #{cot.idCotizacion}<br/><b>Fecha:</b> {fecha_local.strftime('%d/%m/%Y %H:%M')}", cot_style)

    # Tabla de encabezado (logo a la izquierda, datos totalmente a la derecha)
    header_table = Table([[logo, cot_paragraph]], colWidths=[70*mm, 110*mm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (1,0), (1,0), 'RIGHT'), ('LEFTPADDING', (1,0), (1,0), 0), ('RIGHTPADDING', (1,0), (1,0), 0), ('TOPPADDING', (0,0), (-1,-1), 0)]))
    data.append(header_table)
    data.append(Spacer(1, 12))

    # Datos del solicitante
    data.append(Paragraph('<b>Datos del Solicitante</b>', titulos_style))
    data.append(Paragraph(f"<b>Nombre:</b> {cliente.nombre} {cliente.apellido}", texto_style))
    data.append(Paragraph(f"<b>Correo:</b> {cliente.correo}", texto_style))
    if cliente.telefono:
        data.append(Paragraph(f"<b>Teléfono:</b> {cliente.telefono}", texto_style))
    data.append(Spacer(1, 10))

    # Productos
    data.append(Paragraph('<b>Productos para la Cotización</b>', titulos_style))
    for d in detalles:
        if d.producto.imagen:
            # ruta absoluta del archivo
            img_path = d.producto.imagen.path
            if os.path.exists(img_path):
                img = Image(img_path, width=30*mm, height=30*mm)
            else:
                img = Paragraph('(Sin imagen)', styles['Normal'])
        else:
            img = Paragraph('(Sin imagen)', styles['Normal'])

        producto_info = f"""
        <b>{d.producto.nombre}</b><br/>
        {d.producto.descripcion}<br/><br/>
        <b>Precio unitario:</b> ${ (d.producto.precio or 0):,.2f} MXN<br/>
        <b>Cantidad:</b> {d.cantidad}<br/>
        <b>Total estimado:</b> ${ (d.precio_estimado or 0):,.2f} MXN
        """
        table_producto = Table([[img, Paragraph(producto_info, texto_style)]], colWidths=[45*mm, 135*mm])
        table_producto.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 50), ('RIGHTPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))

        data.append(table_producto)
        data.append(Spacer(1, 10))

    # Total
    data.append(Paragraph(f"<b>TOTAL ESTIMADO:</b> ${ (cot.total_estimado or 0):,.2f} MXN", total_style))
    data.append(Spacer(1, 10))

    # Datos de entrega
    data.append(Paragraph('<b>Datos de Entrega</b>', titulos_style))
    data.append(Paragraph(f"<b>Tipo:</b> {cot.get_tipo_entrega_display()}.", texto_style))
    if cot.tipo_entrega == 'domicilio' and cot.calle:
        data.append(Paragraph(f"<b>Dirección:</b> {cot.calle} {cot.numero}, {cot.colonia}, {cot.codigo_postal} {cot.ciudad}, {cot.estado_domicilio.title()}.", texto_style))
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
    data.append(Paragraph("NOTA: Se dará respuesta en máximo 5 días hábiles.", nota_footer_style))
    data.append(Paragraph("Contáctanos:<br /> Correo: regiobox@gmail.com | WhatsApp: 81-1234-5678 | Dirección: José López Collado 2233, Ferrocarrilera, Monterrey, N.L.", texto_footer_style))

    doc.build(data)
    return response

# Vista para recuperar contraseña
def usuario_recuperar_contraseña(request):
    mensaje_exito = None
    mensaje_error = None
    
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        
        # Validar formato de correo
        validator = EmailValidator()
        try:
            validator(email)
        except ValidationError:
            mensaje_error = "Ingresa un correo válido."
            return render(request, "recuperar_contraseña.html", {
                "mensaje_exito": None,
                "mensaje_error": mensaje_error
            })

        try:
            cliente = CLIENTE.objects.get(correo__iexact=email)
            
            # Generar uid y token
            uid = urlsafe_base64_encode(force_bytes(cliente.idCliente))
            token = generar_token(cliente)  # función para generar token

            # Generar enlace de recuperación dinámico
            reset_link = request.build_absolute_uri(f"/usuario/recuperar-contraseña/{uid}/{token}/")

            # Preparar correo
            subject = "Recuperación de contraseña"
            html_message = render_to_string("texto_correo.html", {
                "cliente": cliente,
                "reset_link": reset_link
            })

            email_message = EmailMultiAlternatives(subject, html_message, settings.EMAIL_HOST_USER, [email])
            email_message.attach_alternative(html_message, "text/html")
            email_message.send()
            mensaje_exito = "Se ha enviado un correo con el enlace para restablecer tu contraseña."
        except CLIENTE.DoesNotExist:
            mensaje_error = "El correo no está registrado."

    return render(request, "recuperar_contraseña.html", {
        "mensaje_exito": mensaje_exito,
        "mensaje_error": mensaje_error
    })

# Vista para restablecer contraseña
def usuario_restablecer_contraseña(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        cliente = CLIENTE.objects.get(idCliente=uid)

        if not validar_token(cliente, token):
            return render(request, "recuperar_contraseña.html", {"error": "El enlace ha expirado o es inválido."})

        errores = []
        cambio_exitoso = False

        if request.method == "POST":
            nueva = request.POST.get("nueva_contraseña1", "")
            repetir = request.POST.get("nueva_contraseña2", "")

            # Validar que las contraseñas coincidan
            if nueva != repetir:
                errores.append("Las contraseñas no coinciden.")
            else:
                # Validar la fortaleza de la contraseña
                try:
                    validate_password(nueva, user=cliente)
                except ValidationError as e:
                    errores.extend(e.messages)

            # Si no hay errores, guardar la nueva contraseña
            if not errores:
                cliente.set_password(nueva)
                cliente.save()
                cambio_exitoso = True

        return render(request, "restablecer_contraseña.html", {
            "cliente": cliente,
            "errores": errores,
            "cambio_exitoso": cambio_exitoso
        })

    except CLIENTE.DoesNotExist:
        return render(request, "recuperar_contraseña.html", {"error": "Enlace inválido."})
    
# Vista para el contacto
def contacto_web(request):
    return render(request, "contacto.html")

# Vista para procesar el envío de formulario del contacto
@require_POST
def contacto_enviar(request):
    nombre = request.POST.get('nombre', '').strip()
    correo = request.POST.get('correo', '').strip()
    telefono = request.POST.get('telefono', '').strip()
    estado = request.POST.get('estado', '').strip()
    ciudad = request.POST.get('ciudad', '').strip()
    mensaje = request.POST.get('mensaje', '').strip()

    errores = []
    # Validar obligatorios
    if not nombre or not correo or not estado or not ciudad or not mensaje:
        errores.append('Faltan campos obligatorios.')

    # Verificar si el correo es válido
    validator = EmailValidator()
    try:
        validator(correo)
    except ValidationError:
        errores.append('El correo no es válido.')
        
    # Validar teléfono
    if telefono:
        permitido = set("0123456789 +-")
        if not all(c in permitido for c in telefono):
            errores.append('El teléfono solo puede contener números, espacios, + o guiones.')
        # Contar solo dígitos
        numeros = ''.join(c for c in telefono if c.isdigit())
        if len(numeros) < 8 or len(numeros) > 15:
            errores.append('El teléfono debe tener entre 8 y 15 dígitos.')

    # Si hay errores de validación, solo devolvemos esos
    if errores:
        return JsonResponse({'status': 'validation_error', 'errors': errores})
    
    contexto = {
        "nombre": nombre,
        "correo": correo,
        "telefono": telefono,
        "estado": estado,
        "ciudad": ciudad,
        "mensaje": mensaje,
    }
    cuerpo_html = render_to_string("texto_correo_contacto.html", contexto)

    try:
        email = EmailMessage(
            subject=f"Nuevo mensaje de contacto de {nombre}",
            body=cuerpo_html,
            from_email=settings.EMAIL_HOST_USER,
            to=[getattr(settings, 'CONTACT_RECIPIENT', settings.EMAIL_HOST_USER)],
            reply_to=[correo]
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        return JsonResponse({'status': 'ok', 'message': 'Nos pondremos en contacto contigo pronto.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': 'Ocurrió un problema al enviar el mensaje. Intenta más tarde.'})

# Vista para el inicio
def inicio_web(request):
    # Contar en cuántas cotizaciones aparece cada producto
    top5 = (
        DETALLE_COTIZACION.objects
        .filter(cotizacion__activo=True, producto__activo=True)
        .values('producto')
        .annotate(total_cotizaciones=Count('cotizacion', distinct=True))
        .order_by('-total_cotizaciones')[:5]  # top 5
    )
    # Obtener los IDs y cantidades en un dict
    producto_ids = [item['producto'] for item in top5]
    cotizaciones_por_id = {item['producto']: item['total_cotizaciones'] for item in top5}

    if not producto_ids:
        mas_cotizados = []
    else:
        productos_qs = PRODUCTO.objects.filter(idProducto__in=producto_ids, activo=True)
        productos_dict = {p.idProducto: p for p in productos_qs}

        mas_cotizados = [
            (productos_dict[p_id], cotizaciones_por_id[p_id])
            for p_id in producto_ids if p_id in productos_dict
        ]

    return render(request, "inicio.html", {'mas_cotizados': mas_cotizados})

# Vista para la sección de nosotros
def nosotros_web(request):
    return render(request, "nosotros.html")

# Vista para el aviso de privacidad
def aviso_privacidad(request):
    return render(request, "aviso_de_privacidad.html")

# Vista para los términos y condiciones
def terminos_condiciones(request):
    return render(request, "terminos_y_condiciones.html")

# Vista para cerrar sesión
@login_required_cliente
def logout_web(request):
    request.session.flush()
    return redirect('regioweb:inicio')
