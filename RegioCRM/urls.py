from django.urls import path
from . import views

app_name = 'regiocrm'

urlpatterns = [
    path('', views.login_crm, name='login_crm'),
    path('logout/', views.logout_crm, name='logout_crm'),

    path('dashboard/', views.dashboard_crm, name='dashboard_crm'),
    path('clientes/', views.clientes_crm, name='clientes_crm'),
    path('catalogo/', views.catalogo_crm, name='catalogo_crm'),
    path('catalogo/categorias/', views.catalogo_categorias_crm, name='catalogo_categorias_crm'),
    path('catalogo/productos/', views.catalogo_productos_crm, name='catalogo_productos_crm'),

    path('cotizaciones/', views.cotizaciones_crm, name='cotizaciones_crm'),
    path('cotizaciones/<int:cotizacion_id>/pdf/', views.descargar_cotizacion_pdf, name='descargar_cotizacion_pdf'),
    path('cotizaciones/<int:cotizacion_id>/productos/', views.obtener_productos_cotizacion, name='obtener_productos_cotizacion'),
    path('productos-disponibles/', views.obtener_productos_disponibles, name='obtener_productos_disponibles'),
]
