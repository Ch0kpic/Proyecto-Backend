from django.contrib.auth import get_user_model
from django.http import HttpResponseForbidden
from django.urls import reverse
from django.shortcuts import redirect

User = get_user_model()


class ForzarCambioContrasenaMiddleware:
    """
    RQ-USR-04: Middleware para forzar cambio de contraseña en primer ingreso
    Detecta si la contraseña es temporal y redirige a pantalla de cambio
    No permite navegar por el sistema sin haber cambiado la contraseña
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que se permiten incluso con cambio de contraseña pendiente
        rutas_permitidas = [
            '/dashboard/login/',
            '/dashboard/logout/',
            '/dashboard/cambiar-contrasena-obligatorio/',
            '/admin/logout/',
            '/static/',
            '/media/',
        ]
        
        # Si el usuario está autenticado
        if request.user.is_authenticated:
            # Verificar si debe cambiar su contraseña
            if hasattr(request.user, 'forzar_cambio_contrasena') and request.user.forzar_cambio_contrasena:
                # Verificar si está en una ruta permitida
                es_ruta_permitida = any(request.path.startswith(ruta) for ruta in rutas_permitidas)
                
                if not es_ruta_permitida:
                    # Redirigir al cambio de contraseña obligatorio
                    return redirect('dashboard:cambiar_contrasena_obligatorio')
        
        return self.get_response(request)


class RolMiddleware:
    """
    Middleware para controlar el acceso al admin basado en roles
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo aplicar a URLs del admin
        if request.path.startswith('/admin/'):
            # Permitir acceso a login y logout
            if request.path in ['/admin/', '/admin/login/', '/admin/logout/']:
                return self.get_response(request)
            
            # Si el usuario está autenticado
            if request.user.is_authenticated:
                user_role = request.user.id_rol.nombre if hasattr(request.user, 'id_rol') else None
                
                # Bloquear acceso a ciertos modelos según el rol
                if user_role == 'Cliente':
                    # Los clientes no pueden acceder al admin
                    return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
                
                elif user_role == 'Vendedor':
                    # Los vendedores solo pueden ver productos e inventarios
                    allowed_paths = ['/admin/productos/', '/admin/inventarios/', '/admin/']
                    if not any(request.path.startswith(path) for path in allowed_paths):
                        return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")
                
                elif user_role == 'Bodeguero':
                    # Los bodegueros pueden ver productos e inventarios
                    allowed_paths = ['/admin/productos/', '/admin/inventarios/', '/admin/']
                    if not any(request.path.startswith(path) for path in allowed_paths):
                        return HttpResponseForbidden("No tienes permisos para acceder a esta sección.")

        return self.get_response(request)
