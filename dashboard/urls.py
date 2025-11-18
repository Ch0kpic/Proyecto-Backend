from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('', login_required(views.home), name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('cambiar-contrasena-obligatorio/', login_required(views.cambiar_contrasena_obligatorio), name='cambiar_contrasena_obligatorio'),
    path('usuarios/', login_required(views.usuarios_view), name='usuarios'),
    path('usuarios/obtener/<int:usuario_id>/', login_required(views.obtener_usuario), name='obtener_usuario'),
    path('usuarios/guardar/', login_required(views.guardar_usuario), name='guardar_usuario'),
    path('usuarios/eliminar/<int:usuario_id>/', login_required(views.eliminar_usuario), name='eliminar_usuario'),
    path('usuarios/cambiar-estado/<int:usuario_id>/', login_required(views.cambiar_estado_usuario), name='cambiar_estado_usuario'),
    path('usuarios/exportar-excel/', login_required(views.exportar_usuarios_excel), name='exportar_usuarios_excel'),
    path('productos/', login_required(views.productos_view), name='productos'),
    path('productos/obtener/<int:producto_id>/', login_required(views.obtener_producto), name='obtener_producto'),
    path('productos/actualizar/', login_required(views.actualizar_producto), name='actualizar_producto'),
    path('productos/agregar/', login_required(views.agregar_producto), name='agregar_producto'),
    path('productos/editar/<int:producto_id>/', login_required(views.editar_producto), name='editar_producto'),
    path('productos/exportar-excel/', login_required(views.exportar_productos_excel), name='exportar_productos_excel'),
    path('inventarios/', login_required(views.inventarios_view), name='inventarios'),
    path('inventarios/agregar/', login_required(views.agregar_inventario), name='agregar_inventario'),
    path('inventarios/editar/<int:inventario_id>/', login_required(views.editar_inventario), name='editar_inventario'),
    path('proveedores/', login_required(views.proveedores_view), name='proveedores'),
    path('proveedores/obtener/<int:proveedor_id>/', login_required(views.obtener_proveedor), name='obtener_proveedor'),
    path('proveedores/guardar/', login_required(views.guardar_proveedor), name='guardar_proveedor'),
    path('proveedores/eliminar/<int:proveedor_id>/', login_required(views.eliminar_proveedor), name='eliminar_proveedor'),
    path('proveedores/exportar-excel/', login_required(views.exportar_proveedores_excel), name='exportar_proveedores_excel'),
    path('ventas/', login_required(views.ventas_view), name='ventas'),
    
    # Rutas de prueba para páginas de error (solo en desarrollo)
    path('test-404/', views.error_404, name='test_404'),
    path('test-500/', views.error_500, name='test_500'),
    path('test-403/', views.error_403, name='test_403'),
]
