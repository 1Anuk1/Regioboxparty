# regioweb/context_processors.py

def usuario_logueado(request):
    # Devuelve el primer nombre y primer apellido si el usuario está logueado.
    # Esto estará disponible en todos los templates.
    nombre_completo = request.session.get('cliente_nombre', '')
    apellido_completo = request.session.get('cliente_apellido', '')

    nombre_simple = nombre_completo.split()[0] if nombre_completo else ''
    apellido_simple = apellido_completo.split()[0] if apellido_completo else ''

    return {
        'usuario_nombre': nombre_simple,
        'usuario_apellido': apellido_simple,
        'usuario_logueado': bool(request.session.get('cliente_id', False))
    }

def carrito(request):
    carrito = request.session.get('carrito', [])
    total_cantidad = sum(item['cantidad'] for item in carrito)  # suma todas las cantidades
    return {
        'carrito': carrito,
        'total_cantidad_carrito': total_cantidad
    }
