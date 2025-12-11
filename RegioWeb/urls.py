from django.urls import path
from . import views

app_name = 'regioweb'

urlpatterns = [
    # Básicos
    path('', views.inicio_web, name='inicio'),
    path('login/', views.login_web, name='login'),
    path('registro/', views.registro_web, name='registro'),
    path('logout/', views.logout_web, name='logout'),

    # Usuario
    path('usuario/', views.usuario_web, name='usuario'),
    path('usuario/actualizar-informacion', views.usuario_actualizar_info, name='usuario_actualizar_info'),
    path('usuario/direcciones/agregar/', views.usuario_agregar_direccion, name='usuario_agregar_direccion'),
    path('usuario/direcciones/<int:id_dir>/editar/', views.usuario_editar_direccion, name='usuario_editar_direccion'),
    path('usuario/direcciones/<int:id_dir>/eliminar/', views.usuario_eliminar_direccion, name='usuario_eliminar_direccion'),
    path('usuario/direcciones/<int:id_dir>/principal/', views.usuario_direccion_principal, name='usuario_direccion_principal'),
    path('usuario/recuperar-contraseña/', views.usuario_recuperar_contraseña, name='usuario_recuperar_contraseña'),
    path('usuario/recuperar-contraseña/<uidb64>/<token>/', views.usuario_restablecer_contraseña, name='usuario_restablecer_contraseña'),

    # Carrito
    path('carrito/', views.carrito_web, name='carrito'),
    path('carrito/agregar/<str:producto_id>/', views.carrito_agregar_producto, name='carrito_agregar_producto'),
    path('carrito/actualizar/<str:producto_id>/<int:cantidad>/', views.carrito_actualizar_producto, name='carrito_actualizar_producto'),
    path('carrito/eliminar/<str:producto_id>/', views.carrito_eliminar_producto, name='carrito_eliminar_producto'),
    path('carrito/vaciar/', views.carrito_vaciar, name='carrito_vaciar'),
    path('carrito/cotizacion/generar/', views.generar_cotizacion, name='generar_cotizacion'),
    path('carrito/cotizacion/<int:cotizacion_id>/pdf/', views.descargar_cotizacion_pdf, name='descargar_cotizacion_pdf'),

    # Contacto
    path('contacto/', views.contacto_web, name='contacto'),
    path('contacto/enviar/', views.contacto_enviar, name='contacto_enviar'),

    # Extra
    path('nosotros/', views.nosotros_web, name='nosotros'),
    path('catalogo/', views.catalogo_web, name='catalogo'),
    path('aviso-de-privacidad/', views.aviso_privacidad, name='aviso_privacidad'),
    path('terminos-y-condiciones/', views.terminos_condiciones, name='terminos_condiciones'),
]
