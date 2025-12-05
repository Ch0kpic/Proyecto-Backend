from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
from django.contrib.auth.hashers import make_password
from django.conf import settings
from productos.models import Producto
from inventarios.models import Inventario
from usuarios.models import Usuario, PasswordResetToken
from .forms import ProductoForm, InventarioForm
import secrets
import string
import re


# ========== FUNCIONES AUXILIARES ==========

def generar_contrasena_robusta():
    """
    RQ-USR-02: Generar contraseña temporal robusta
    Requisitos:
    - Longitud mínima: 8 caracteres
    - Al menos 1 mayúscula, 1 minúscula, 1 dígito, 1 carácter especial
    """
    while True:
        # Generar contraseña de 12 caracteres
        mayusculas = string.ascii_uppercase
        minusculas = string.ascii_lowercase
        digitos = string.digits
        especiales = "!@#$%&*"
        
        # Asegurar que tenga al menos uno de cada tipo
        password = [
            secrets.choice(mayusculas),
            secrets.choice(minusculas),
            secrets.choice(digitos),
            secrets.choice(especiales)
        ]
        
        # Completar hasta 12 caracteres con caracteres aleatorios
        todos_caracteres = mayusculas + minusculas + digitos + especiales
        for _ in range(8):  # 12 - 4 = 8
            password.append(secrets.choice(todos_caracteres))
        
        # Mezclar los caracteres
        secrets.SystemRandom().shuffle(password)
        password_str = ''.join(password)
        
        # Validar que cumple los requisitos
        if (re.search(r'[A-Z]', password_str) and
            re.search(r'[a-z]', password_str) and
            re.search(r'[0-9]', password_str) and
            re.search(r'[!@#$%&*]', password_str) and
            len(password_str) >= 8):
            return password_str


def enviar_correo_bienvenida(usuario, temp_password):
    """
    RQ-USR-03: Enviar correo con credenciales de acceso
    Incluye:
    - Username (email)
    - Contraseña temporal
    - Enlace directo al login
    """
    try:
        # URL del sistema (ajustar según tu dominio/puerto)
        login_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        login_url += '/dashboard/login/'
        
        # Asunto del correo
        asunto = f'Bienvenido a Dulcería Lilis - Credenciales de Acceso'
        
        # Mensaje en HTML
        mensaje_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4F81F7, #3B5998); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .credentials {{ background: white; padding: 20px; border-left: 4px solid #4F81F7; margin: 20px 0; }}
                .credential-item {{ margin: 10px 0; }}
                .credential-label {{ font-weight: bold; color: #4F81F7; }}
                .credential-value {{ font-family: monospace; background: #f0f0f0; padding: 5px 10px; border-radius: 4px; }}
                .button {{ display: inline-block; background: #4F81F7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍬 Dulcería Lilis</h1>
                    <p>Sistema de Gestión</p>
                </div>
                <div class="content">
                    <h2>¡Bienvenido/a {usuario.nombre}!</h2>
                    <p>Se ha creado una cuenta de acceso para ti en el Sistema de Gestión de Dulcería Lilis.</p>
                    
                    <div class="credentials">
                        <h3>Tus Credenciales de Acceso:</h3>
                        <div class="credential-item">
                            <span class="credential-label">Usuario:</span><br>
                            <span class="credential-value">{usuario.username}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Contraseña Temporal:</span><br>
                            <span class="credential-value">{temp_password}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Rol:</span><br>
                            <span class="credential-value">{usuario.id_rol.nombre}</span>
                        </div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Importante:</strong>
                        <ul>
                            <li>Esta contraseña es temporal y debe ser cambiada en tu primer inicio de sesión</li>
                            <li>Por seguridad, no compartas estas credenciales con nadie</li>
                            <li>Si no solicitaste esta cuenta, contacta al administrador</li>
                        </ul>
                    </div>
                    
                    <center>
                        <a href="{login_url}" class="button">Iniciar Sesión Ahora</a>
                    </center>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                        <a href="{login_url}">{login_url}</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responder.</p>
                    <p>&copy; {datetime.now().year} Dulcería Lilis - Todos los derechos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Mensaje en texto plano (fallback)
        mensaje_texto = f"""
Bienvenido/a {usuario.nombre}!

Se ha creado una cuenta de acceso para ti en el Sistema de Gestión de Dulcería Lilis.

CREDENCIALES DE ACCESO:
Usuario: {usuario.username}
Contraseña Temporal: {temp_password}
Rol: {usuario.id_rol.nombre}

IMPORTANTE:
- Esta contraseña es temporal y debe ser cambiada en tu primer inicio de sesión
- Por seguridad, no compartas estas credenciales con nadie
- Si no solicitaste esta cuenta, contacta al administrador

Para acceder al sistema, visita:
{login_url}

---
Este es un correo automático, por favor no responder.
© {datetime.now().year} Dulcería Lilis
        """
        
        # Enviar correo
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo],
            html_message=mensaje_html,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error al enviar correo de bienvenida: {e}")
        raise


def enviar_correo_reset_password(usuario, temp_password, admin_nombre):
    """
    RQ-USR-06: Enviar correo cuando admin resetea contraseña
    Similar al correo de bienvenida pero indica que fue un reset administrativo
    """
    try:
        # URL del sistema
        login_url = settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://127.0.0.1:8000'
        login_url += '/dashboard/login/'
        
        # Asunto del correo
        asunto = f'Dulcería Lilis - Tu contraseña ha sido reseteada'
        
        # Mensaje en HTML
        mensaje_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4F81F7, #3B5998); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .credentials {{ background: white; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0; }}
                .credential-item {{ margin: 10px 0; }}
                .credential-label {{ font-weight: bold; color: #4F81F7; }}
                .credential-value {{ font-family: monospace; background: #f0f0f0; padding: 5px 10px; border-radius: 4px; }}
                .button {{ display: inline-block; background: #4F81F7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .warning {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
                .alert {{ background: #f8d7da; border-left: 4px solid #dc3545; padding: 15px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍬 Dulcería Lilis</h1>
                    <p>Sistema de Gestión</p>
                </div>
                <div class="content">
                    <h2>Contraseña Reseteada</h2>
                    <p>Hola {usuario.nombre},</p>
                    <p>El administrador <strong>{admin_nombre}</strong> ha reseteado tu contraseña en el Sistema de Gestión de Dulcería Lilis.</p>
                    
                    <div class="alert">
                        <strong>🔐 Acción de Seguridad:</strong>
                        <p>Si NO solicitaste este cambio, contacta inmediatamente al administrador del sistema.</p>
                    </div>
                    
                    <div class="credentials">
                        <h3>Tus Nuevas Credenciales:</h3>
                        <div class="credential-item">
                            <span class="credential-label">Usuario:</span><br>
                            <span class="credential-value">{usuario.username}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Nueva Contraseña Temporal:</span><br>
                            <span class="credential-value">{temp_password}</span>
                        </div>
                        <div class="credential-item">
                            <span class="credential-label">Rol:</span><br>
                            <span class="credential-value">{usuario.id_rol.nombre}</span>
                        </div>
                    </div>
                    
                    <div class="warning">
                        <strong>⚠️ Importante:</strong>
                        <ul>
                            <li>Esta es una contraseña temporal que debes cambiar en tu próximo inicio de sesión</li>
                            <li>Tu contraseña anterior ya NO es válida</li>
                            <li>Por seguridad, no compartas estas credenciales con nadie</li>
                            <li>Cambia tu contraseña por una que solo tú conozcas</li>
                        </ul>
                    </div>
                    
                    <center>
                        <a href="{login_url}" class="button">Iniciar Sesión Ahora</a>
                    </center>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        Si el botón no funciona, copia y pega este enlace en tu navegador:<br>
                        <a href="{login_url}">{login_url}</a>
                    </p>
                </div>
                <div class="footer">
                    <p>Este es un correo automático, por favor no responder.</p>
                    <p>&copy; {datetime.now().year} Dulcería Lilis - Todos los derechos reservados</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Mensaje en texto plano (fallback)
        mensaje_texto = f"""
Contraseña Reseteada - Dulcería Lilis

Hola {usuario.nombre},

El administrador {admin_nombre} ha reseteado tu contraseña en el Sistema de Gestión de Dulcería Lilis.

🔐 ACCIÓN DE SEGURIDAD:
Si NO solicitaste este cambio, contacta inmediatamente al administrador del sistema.

NUEVAS CREDENCIALES:
Usuario: {usuario.username}
Nueva Contraseña Temporal: {temp_password}
Rol: {usuario.id_rol.nombre}

IMPORTANTE:
- Esta es una contraseña temporal que debes cambiar en tu próximo inicio de sesión
- Tu contraseña anterior ya NO es válida
- Por seguridad, no compartas estas credenciales con nadie
- Cambia tu contraseña por una que solo tú conozcas

Para acceder al sistema, visita:
{login_url}

---
Este es un correo automático, por favor no responder.
© {datetime.now().year} Dulcería Lilis
        """
        
        # Enviar correo
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[usuario.correo],
            html_message=mensaje_html,
            fail_silently=False,
        )
        
        return True
    except Exception as e:
        print(f"Error al enviar correo de reset de contraseña: {e}")
        raise


# ========== VISTAS ==========

def login_view(request):
    """Vista de login personalizada"""
    # Si el usuario ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Verificar si el usuario debe cambiar su contraseña
            if hasattr(user, 'forzar_cambio_contrasena') and user.forzar_cambio_contrasena:
                # Redirigir a la página de cambio de contraseña obligatorio
                return redirect('dashboard:cambiar_contrasena_obligatorio')
            
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'dashboard/new_login.html')

def logout_view(request):
    """Vista de logout"""
    logout(request)
    return redirect('dashboard:login')

@login_required
def home(request):
    """Dashboard principal"""
    user = request.user
    now = timezone.now()
    
    # Datos para el contexto
    context = {
        'user': user,
        'productos_count': Producto.objects.count(),
        'inventarios_count': Inventario.objects.count(),
        'today': now.date(),
        'now': now,
    }
    
    # Datos ficticios para proveedores y ventas (solo para administradores)
    if user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador'):
        context.update({
            'proveedores_count': 12,  # Ficticio
            'ventas_count': 156,      # Ficticio
        })
    
    return render(request, 'dashboard/home.html', context)

@login_required
def productos_view(request):
    """Vista para listar todos los productos con búsqueda, paginación y ordenamiento"""
    user = request.user
    
    # Verificar permisos según rol
    rol_nombre = user.id_rol.nombre if hasattr(user, 'id_rol') and user.id_rol else None
    es_vendedor = rol_nombre == 'Vendedor'
    es_bodeguero = rol_nombre == 'Bodeguero'
    puede_crear_editar = user.is_superuser or rol_nombre in ['Administrador', 'Bodeguero']
    puede_eliminar = user.is_superuser or rol_nombre == 'Administrador'
    
    productos = Producto.objects.all()
    
    # Búsqueda por múltiples campos
    search = request.GET.get('search', '')
    if search:
        productos = productos.filter(
            nombre__icontains=search
        ) | productos.filter(
            descripcion__icontains=search
        ) | productos.filter(
            precio_referencia__icontains=search
        )
    
    # Ordenamiento
    order_by = request.GET.get('order_by', 'id_producto')
    order_direction = request.GET.get('order_direction', 'asc')
    
    # Construir el campo de ordenamiento
    if order_direction == 'desc':
        order_field = f'-{order_by}' if not order_by.startswith('-') else order_by
    else:
        order_field = order_by.replace('-', '')
    
    productos = productos.order_by(order_field)
    
    # Paginación - obtener de sesión o de parámetro GET
    per_page_param = request.GET.get('per_page')
    if per_page_param:
        per_page = int(per_page_param)
        request.session['productos_per_page'] = per_page
    else:
        per_page = request.session.get('productos_per_page', 10)
        # Asegurar que sea entero
        if isinstance(per_page, str):
            per_page = int(per_page)
    
    paginator = Paginator(productos, per_page)
    page = request.GET.get('page', 1)
    productos_paginados = paginator.get_page(page)
    
    context = {
        'productos': productos_paginados,
        'search': search,
        'order_by': order_by.replace('-', ''),
        'order_direction': order_direction,
        'per_page': per_page,
        'total_productos': Producto.objects.count(),
        'productos_activos': Producto.objects.count(),
        'es_vendedor': es_vendedor,
        'es_bodeguero': es_bodeguero,
        'puede_crear_editar': puede_crear_editar,
        'puede_eliminar': puede_eliminar,
    }
    return render(request, 'dashboard/productos.html', context)

@login_required
def inventarios_view(request):
    """Vista de inventarios con búsqueda avanzada y alertas"""
    from inventarios.models import AlertaInventario, MovimientoInventario
    from proveedores.models import Proveedor
    from django.db.models import Q
    
    user = request.user
    
    # Verificar permisos según rol
    rol_nombre = user.id_rol.nombre if hasattr(user, 'id_rol') and user.id_rol else None
    es_vendedor = rol_nombre == 'Vendedor'
    es_bodeguero = rol_nombre == 'Bodeguero'
    puede_editar = user.is_superuser or rol_nombre in ['Administrador', 'Bodeguero']
    
    # Obtener inventarios
    inventarios = Inventario.objects.select_related('id_producto').all()
    
    # Búsqueda avanzada
    search = request.GET.get('search', '')
    if search:
        inventarios = inventarios.filter(
            Q(id_producto__nombre__icontains=search) |
            Q(ubicacion__icontains=search) |
            Q(id_producto__descripcion__icontains=search)
        )
    
    # Filtros
    nivel_stock = request.GET.get('nivel_stock')
    ubicacion = request.GET.get('ubicacion')
    
    # Filtrar por nivel de stock
    if nivel_stock:
        if nivel_stock == 'critico':
            inventarios = [inv for inv in inventarios if inv.cantidad_actual == 0]
        elif nivel_stock == 'bajo':
            inventarios = [inv for inv in inventarios if inv.necesita_reabastecimiento and inv.cantidad_actual > 0]
        elif nivel_stock == 'medio':
            inventarios = [inv for inv in inventarios if inv.nivel_stock == 'medio']
        elif nivel_stock == 'alto':
            inventarios = [inv for inv in inventarios if inv.nivel_stock == 'alto']
    
    # Filtrar por ubicación
    if ubicacion:
        inventarios = inventarios.filter(ubicacion__icontains=ubicacion) if hasattr(inventarios, 'filter') else [inv for inv in inventarios if ubicacion.lower() in inv.ubicacion.lower()]
    
    # Convertir a lista si es queryset
    if hasattr(inventarios, 'all'):
        inventarios = list(inventarios)
    
    # Ordenamiento
    order_by = request.GET.get('order_by', 'id_producto__nombre')
    order_direction = request.GET.get('order_direction', 'asc')
    
    # Obtener alertas activas
    alertas_activas = AlertaInventario.objects.filter(resuelta=False).count()
    alertas_criticas = AlertaInventario.objects.filter(resuelta=False, tipo_alerta='stock_critico').count()
    
    # Calcular estadísticas
    total_productos = len(inventarios)
    stock_critico = sum(1 for inv in inventarios if inv.cantidad_actual == 0)
    stock_bajo = sum(1 for inv in inventarios if inv.necesita_reabastecimiento and inv.cantidad_actual > 0)
    stock_medio = sum(1 for inv in inventarios if inv.nivel_stock == 'medio')
    stock_alto = sum(1 for inv in inventarios if inv.nivel_stock == 'alto')
    
    # Obtener ubicaciones únicas para filtro
    ubicaciones = Inventario.objects.values_list('ubicacion', flat=True).distinct()
    
    # Obtener proveedores para el formulario
    proveedores = Proveedor.objects.all().order_by('nombre')
    
    # Obtener movimientos recientes (últimos 20)
    movimientos_recientes = MovimientoInventario.objects.select_related(
        'inventario__id_producto', 'usuario'
    ).order_by('-fecha_movimiento')[:20]
    
    now = timezone.now()
    
    context = {
        'inventarios': inventarios,
        'total_productos': total_productos,
        'stock_alto': stock_alto,
        'stock_medio': stock_medio,
        'stock_bajo': stock_bajo,
        'stock_critico': stock_critico,
        'alertas_activas': alertas_activas,
        'alertas_criticas': alertas_criticas,
        'ubicaciones': ubicaciones,
        'proveedores': proveedores,
        'movimientos_recientes': movimientos_recientes,
        'search': search,
        'nivel_stock_filtro': nivel_stock,
        'ubicacion_filtro': ubicacion,
        'today': now.date(),
        'user': request.user,
        'es_vendedor': es_vendedor,
        'es_bodeguero': es_bodeguero,
        'puede_editar': puede_editar,
    }
    return render(request, 'dashboard/inventarios.html', context)

@login_required
def proveedores_view(request):
    """Vista de gestión de proveedores"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        raise PermissionDenied("No tienes permisos para acceder a esta sección")
    
    from proveedores.models import Proveedor
    from django.db.models import Q
    
    # Obtener parámetros de búsqueda y filtro
    search = request.GET.get('search', '')
    per_page = request.GET.get('per_page', request.session.get('proveedores_per_page', 10))
    order_by = request.GET.get('order_by', 'id_proveedor')
    order_direction = request.GET.get('order_direction', 'asc')
    
    # Guardar per_page en sesión
    request.session['proveedores_per_page'] = int(per_page)
    
    # Obtener proveedores
    proveedores = Proveedor.objects.all()
    
    # Aplicar búsqueda
    if search:
        proveedores = proveedores.filter(
            Q(nombre__icontains=search) |
            Q(contacto__icontains=search) |
            Q(direccion__icontains=search)
        )
    
    # Aplicar ordenamiento
    order_field = order_by if order_direction == 'asc' else f'-{order_by}'
    proveedores = proveedores.order_by(order_field)
    
    # Aplicar paginación
    paginator = Paginator(proveedores, per_page)
    page_number = request.GET.get('page', 1)
    
    try:
        proveedores_page = paginator.page(page_number)
    except PageNotAnInteger:
        proveedores_page = paginator.page(1)
    except EmptyPage:
        proveedores_page = paginator.page(paginator.num_pages)
    
    # Productos disponibles para asociar con proveedores
    productos_disponibles = Producto.objects.all()
    
    context = {
        'proveedores': proveedores_page,
        'productos_disponibles': productos_disponibles,
        'proveedores_count': paginator.count,
        'proveedores_activos': paginator.count,
        'productos_proveedor': productos_disponibles.count(),
        'ordenes_pendientes': 0,
        'search': search,
        'per_page': int(per_page),
        'order_by': order_by,
        'order_direction': order_direction,
        'user': request.user,
    }
    return render(request, 'dashboard/proveedores.html', context)

@login_required
def obtener_proveedor(request, proveedor_id):
    """API para obtener datos de un proveedor en formato JSON"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    try:
        from proveedores.models import Proveedor
        from producto_proveedor.models import ProductoProveedor
        
        proveedor = Proveedor.objects.get(id_proveedor=proveedor_id)
        
        # Obtener productos asociados con sus nombres
        productos_relaciones = ProductoProveedor.objects.filter(id_proveedor=proveedor).select_related('id_producto')
        productos_ids = [rel.id_producto.id_producto for rel in productos_relaciones]
        productos_nombres = [{'id': rel.id_producto.id_producto, 'nombre': rel.id_producto.nombre} for rel in productos_relaciones]
        
        # Parsear dirección para obtener comuna y región
        direccion_completa = proveedor.direccion or ''
        partes_direccion = direccion_completa.split(', ')
        direccion_calle = partes_direccion[0] if len(partes_direccion) > 0 else ''
        comuna = partes_direccion[1] if len(partes_direccion) > 1 else ''
        region = partes_direccion[2] if len(partes_direccion) > 2 else ''
        
        data = {
            'success': True,
            'proveedor': {
                'id': proveedor.id_proveedor,
                'nombre': proveedor.nombre,
                'contacto': proveedor.contacto,
                'direccion': direccion_calle,
                'direccion_completa': direccion_completa,
                'comuna': comuna,
                'region': region,
                'productos': productos_ids,
                'productos_detalle': productos_nombres
            }
        }
        return JsonResponse(data)
    except Proveedor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Proveedor no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

@login_required
def guardar_proveedor(request):
    """API para crear o actualizar un proveedor"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        from proveedores.models import Proveedor
        from producto_proveedor.models import ProductoProveedor
        import json
        
        proveedor_id = request.POST.get('proveedor_id')
        nombre = request.POST.get('nombre', '').strip()
        contacto = request.POST.get('contacto', '').strip()
        direccion = request.POST.get('direccion', '').strip()
        comuna = request.POST.get('comuna', '').strip()
        region = request.POST.get('region', '').strip()
        tipo_proveedor = request.POST.get('tipo_proveedor', '').strip()
        condiciones_pago = request.POST.get('condiciones_pago', '').strip()
        tiempo_entrega = request.POST.get('tiempo_entrega', '').strip()
        monto_minimo = request.POST.get('monto_minimo', '').strip()
        productos_ids = request.POST.getlist('productos[]')
        
        # Validaciones
        if not nombre:
            return JsonResponse({
                'success': False, 
                'errors': {'nombre': ['El campo Nombre es requerido']}
            }, status=400)
        
        if len(nombre) > 150:
            return JsonResponse({
                'success': False, 
                'errors': {'nombre': ['El nombre no puede exceder 150 caracteres']}
            }, status=400)
        
        if not contacto:
            return JsonResponse({
                'success': False, 
                'errors': {'contacto': ['El campo Contacto es requerido']}
            }, status=400)
        
        if len(contacto) > 200:
            return JsonResponse({
                'success': False, 
                'errors': {'contacto': ['El contacto no puede exceder 200 caracteres']}
            }, status=400)
        
        if not direccion:
            return JsonResponse({
                'success': False, 
                'errors': {'direccion': ['El campo Dirección es requerido']}
            }, status=400)
        
        # Construir dirección completa con información chilena
        direccion_completa = direccion
        if comuna:
            direccion_completa += f", {comuna}"
        if region:
            direccion_completa += f", {region}"
        
        if len(direccion_completa) > 200:
            return JsonResponse({
                'success': False, 
                'errors': {'direccion': ['La dirección completa no puede exceder 200 caracteres']}
            }, status=400)
        
        # Guardar datos adicionales en JSON para recuperarlos después
        datos_adicionales = {
            'direccion_calle': direccion,
            'comuna': comuna,
            'region': region,
            'tipo_proveedor': tipo_proveedor,
            'condiciones_pago': condiciones_pago,
            'tiempo_entrega': tiempo_entrega,
            'monto_minimo': monto_minimo
        }
        
        # Crear o actualizar proveedor
        if proveedor_id:
            # Actualizar existente
            proveedor = Proveedor.objects.get(id_proveedor=proveedor_id)
            proveedor.nombre = nombre
            proveedor.contacto = contacto
            proveedor.direccion = direccion_completa
            proveedor.save()
            mensaje = f'Proveedor "{nombre}" actualizado exitosamente'
            
            # Eliminar asociaciones anteriores
            ProductoProveedor.objects.filter(id_proveedor=proveedor).delete()
        else:
            # Crear nuevo
            proveedor = Proveedor.objects.create(
                nombre=nombre,
                contacto=contacto,
                direccion=direccion_completa
            )
            mensaje = f'Proveedor "{nombre}" creado exitosamente'
        
        # Asociar productos seleccionados
        productos_asociados = 0
        if productos_ids:
            for producto_id in productos_ids:
                try:
                    producto = Producto.objects.get(id_producto=producto_id)
                    ProductoProveedor.objects.create(
                        id_producto=producto,
                        id_proveedor=proveedor,
                        precio_acordado=0  # Valor por defecto, puede editarse después
                    )
                    productos_asociados += 1
                except Producto.DoesNotExist:
                    continue
        
        if productos_asociados > 0:
            mensaje += f' con {productos_asociados} producto(s) asociado(s)'
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'proveedor': {
                'id': proveedor.id_proveedor,
                'nombre': proveedor.nombre,
                'contacto': proveedor.contacto,
                'direccion': proveedor.direccion,
                'datos_adicionales': datos_adicionales,
                'productos_asociados': productos_asociados
            }
        })
        
    except Proveedor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Proveedor no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al guardar: {str(e)}'}, status=500)

@login_required
def eliminar_proveedor(request, proveedor_id):
    """API para eliminar un proveedor"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    user = request.user
    
    # Verificar permisos - solo administradores
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos para eliminar proveedores'}, status=403)
    
    try:
        from proveedores.models import Proveedor
        
        # Obtener proveedor
        proveedor = Proveedor.objects.get(id_proveedor=proveedor_id)
        nombre_proveedor = proveedor.nombre
        
        # Eliminar proveedor
        proveedor.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Proveedor "{nombre_proveedor}" eliminado exitosamente'
        })
        
    except Proveedor.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Proveedor no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al eliminar: {str(e)}'}, status=500)

@login_required
def exportar_proveedores_excel(request):
    """Exportar proveedores a Excel con formato profesional"""
    user = request.user
    
    # Solo administradores pueden exportar
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        from django.http import HttpResponse
        from datetime import datetime
        from proveedores.models import Proveedor
        from producto_proveedor.models import ProductoProveedor
        
        # Crear workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Proveedores"
        
        # Estilos
        header_fill = PatternFill(start_color="4F81F7", end_color="4F81F7", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Título
        ws.merge_cells('A1:F1')
        ws['A1'] = '🏢 LISTADO DE PROVEEDORES - DULCERÍA LILIS'
        ws['A1'].font = Font(bold=True, size=16, color="4F81F7")
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[1].height = 30
        
        # Fecha de exportación
        ws.merge_cells('A2:F2')
        ws['A2'] = f'Exportado el: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
        ws['A2'].alignment = Alignment(horizontal='center')
        ws['A2'].font = Font(italic=True, size=10)
        ws.row_dimensions[2].height = 20
        
        # Encabezados
        headers = ['ID', 'Nombre', 'Contacto', 'Dirección', 'Comuna', 'Región', 'Productos']
        ws.append([])
        ws.append(headers)
        
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=4, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        ws.row_dimensions[4].height = 25
        
        # Datos
        proveedores = Proveedor.objects.all().order_by('id_proveedor')
        
        for proveedor in proveedores:
            # Parsear dirección
            partes_direccion = proveedor.direccion.split(', ') if proveedor.direccion else []
            direccion_calle = partes_direccion[0] if len(partes_direccion) > 0 else ''
            comuna = partes_direccion[1] if len(partes_direccion) > 1 else ''
            region = partes_direccion[2] if len(partes_direccion) > 2 else ''
            
            # Obtener productos asociados
            productos = ProductoProveedor.objects.filter(id_proveedor=proveedor).select_related('id_producto')
            productos_nombres = ', '.join([p.id_producto.nombre for p in productos]) if productos.exists() else 'Sin productos'
            
            row = [
                proveedor.id_proveedor,
                proveedor.nombre,
                proveedor.contacto or 'Sin contacto',
                direccion_calle or 'Sin dirección',
                comuna or '-',
                region or '-',
                productos_nombres
            ]
            ws.append(row)
            
            # Aplicar bordes y alineación a cada celda
            current_row = ws.max_row
            for col_num in range(1, len(headers) + 1):
                cell = ws.cell(row=current_row, column=col_num)
                cell.border = border
                cell.alignment = Alignment(vertical='center', wrap_text=True)
                
                # ID centrado
                if col_num == 1:
                    cell.alignment = Alignment(horizontal='center', vertical='center')
        
        # Ajustar anchos de columna
        column_widths = [8, 30, 25, 35, 20, 30, 40]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Agregar totales
        total_row = ws.max_row + 2
        ws.merge_cells(f'A{total_row}:C{total_row}')
        ws[f'A{total_row}'] = f'Total de Proveedores: {proveedores.count()}'
        ws[f'A{total_row}'].font = Font(bold=True, size=11)
        ws[f'A{total_row}'].alignment = Alignment(horizontal='left')
        
        # Preparar respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Proveedores_Lilis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        wb.save(response)
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al exportar: {str(e)}'}, status=500)

@login_required
def ventas_view(request):
    """Vista ficticia de ventas"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        raise PermissionDenied("No tienes permisos para acceder a esta sección")
    
    # Datos ficticios
    ventas = [
        {'id': 1, 'fecha': '2025-01-15', 'cliente': 'Cliente A', 'total': 50000, 'estado': 'Completada'},
        {'id': 2, 'fecha': '2025-01-14', 'cliente': 'Cliente B', 'total': 75000, 'estado': 'Pendiente'},
        {'id': 3, 'fecha': '2025-01-13', 'cliente': 'Cliente C', 'total': 30000, 'estado': 'Completada'},
    ]
    
    context = {
        'ventas': ventas,
        'user': request.user,
    }
    return render(request, 'dashboard/ventas.html', context)

@login_required
def agregar_producto(request):
    """Vista para agregar un nuevo producto"""
    user = request.user
    
    # Verificar permisos
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre in ['Administrador', 'Bodeguero'])):
        messages.error(request, 'No tienes permisos para agregar productos')
        return redirect('dashboard:productos')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" agregado exitosamente')
            return redirect('dashboard:productos')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = ProductoForm()
    
    context = {
        'form': form,
        'user': user,
        'titulo': 'Agregar Nuevo Producto'
    }
    return render(request, 'dashboard/form_producto.html', context)

@login_required
def editar_producto(request, producto_id):
    """Vista para editar un producto existente"""
    user = request.user
    producto = get_object_or_404(Producto, id_producto=producto_id)
    
    # Solo administradores pueden editar
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        messages.error(request, 'No tienes permisos para editar productos')
        return redirect('dashboard:productos')
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('dashboard:productos')
    else:
        form = ProductoForm(instance=producto)
    
    context = {
        'form': form,
        'user': user,
        'titulo': f'Editar Producto: {producto.nombre}',
        'producto': producto
    }
    return render(request, 'dashboard/form_producto.html', context)

@login_required
def agregar_inventario(request):
    """Vista para agregar un nuevo inventario"""
    user = request.user
    
    # Solo administradores pueden agregar inventarios
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        messages.error(request, 'Solo los administradores pueden agregar inventarios')
        return redirect('dashboard:inventarios')
    
    if request.method == 'POST':
        form = InventarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventario agregado exitosamente')
            return redirect('dashboard:inventarios')
    else:
        form = InventarioForm()
    
    context = {
        'form': form,
        'user': user,
        'titulo': 'Agregar Nuevo Inventario'
    }
    return render(request, 'dashboard/form_inventario.html', context)

@login_required
def editar_inventario(request, inventario_id):
    """Vista para editar un inventario existente"""
    user = request.user
    inventario = get_object_or_404(Inventario, id_inventario=inventario_id)
    
    # Solo administradores pueden editar
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        messages.error(request, 'No tienes permisos para editar inventarios')
        return redirect('dashboard:inventarios')
    
    if request.method == 'POST':
        form = InventarioForm(request.POST, instance=inventario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventario actualizado exitosamente')
            return redirect('dashboard:inventarios')
    else:
        form = InventarioForm(instance=inventario)
    
    context = {
        'form': form,
        'user': user,
        'titulo': f'Editar Inventario: {inventario.id_producto.nombre}',
        'inventario': inventario
    }
    return render(request, 'dashboard/form_inventario.html', context)

@login_required
def registrar_movimiento_inventario(request):
    """Vista para registrar movimientos de inventario (entrada/salida)"""
    from inventarios.models import MovimientoInventario, AlertaInventario
    from django.db import transaction
    
    user = request.user
    
    # Solo administradores y bodegueros pueden registrar movimientos
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre in ['Administrador', 'Bodeguero'])):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        inventario_id = request.POST.get('inventario_id')
        tipo_movimiento = request.POST.get('tipo_movimiento')
        cantidad = int(request.POST.get('cantidad', 0))
        proveedor = request.POST.get('proveedor', '')
        motivo = request.POST.get('motivo', '')
        
        if not inventario_id or not tipo_movimiento or cantidad <= 0:
            return JsonResponse({'success': False, 'message': 'Datos incompletos'})
        
        inventario = get_object_or_404(Inventario, id_inventario=inventario_id)
        cantidad_anterior = inventario.cantidad_actual
        
        # Calcular nueva cantidad según tipo de movimiento
        if tipo_movimiento == 'entrada':
            cantidad_nueva = cantidad_anterior + cantidad
        elif tipo_movimiento == 'salida':
            if cantidad > cantidad_anterior:
                return JsonResponse({
                    'success': False,
                    'message': f'Stock insuficiente. Disponible: {cantidad_anterior}'
                })
            cantidad_nueva = cantidad_anterior - cantidad
        elif tipo_movimiento == 'ajuste':
            cantidad_nueva = cantidad
        else:
            return JsonResponse({'success': False, 'message': 'Tipo de movimiento no válido'})
        
        # Usar transacción para asegurar consistencia
        with transaction.atomic():
            # Registrar movimiento
            movimiento = MovimientoInventario.objects.create(
                inventario=inventario,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=cantidad_nueva,
                usuario=user,
                proveedor=proveedor if proveedor else None,
                motivo=motivo if motivo else None
            )
            
            # Actualizar inventario
            inventario.cantidad_actual = cantidad_nueva
            inventario.save()
            
            # Verificar y crear alertas si es necesario
            if inventario.necesita_reabastecimiento:
                # Crear alerta de stock bajo si no existe una sin resolver
                alerta_existente = AlertaInventario.objects.filter(
                    inventario=inventario,
                    tipo_alerta='stock_bajo',
                    resuelta=False
                ).first()
                
                if not alerta_existente:
                    AlertaInventario.objects.create(
                        inventario=inventario,
                        tipo_alerta='stock_bajo' if cantidad_nueva > 0 else 'stock_critico'
                    )
            else:
                # Resolver alertas si el stock vuelve a estar bien
                AlertaInventario.objects.filter(
                    inventario=inventario,
                    resuelta=False
                ).update(resuelta=True, fecha_resolucion=timezone.now())
        
        return JsonResponse({
            'success': True,
            'message': f'Movimiento de {tipo_movimiento} registrado correctamente',
            'data': {
                'cantidad_anterior': cantidad_anterior,
                'cantidad_nueva': cantidad_nueva,
                'nivel_stock': inventario.nivel_stock
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def historial_movimientos(request, inventario_id=None):
    """Vista para obtener historial de movimientos"""
    from inventarios.models import MovimientoInventario
    
    user = request.user
    
    # Verificar permisos
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre in ['Administrador', 'Bodeguero', 'Vendedor'])):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    try:
        # Obtener movimientos
        if inventario_id:
            movimientos = MovimientoInventario.objects.filter(inventario_id=inventario_id)
        else:
            movimientos = MovimientoInventario.objects.all()
        
        # Filtros opcionales
        tipo = request.GET.get('tipo')
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        
        if tipo:
            movimientos = movimientos.filter(tipo_movimiento=tipo)
        if fecha_desde:
            movimientos = movimientos.filter(fecha_movimiento__gte=fecha_desde)
        if fecha_hasta:
            movimientos = movimientos.filter(fecha_movimiento__lte=fecha_hasta)
        
        # Preparar datos
        data = [{
            'id': mov.id_movimiento,
            'producto': mov.inventario.id_producto.nombre,
            'ubicacion': mov.inventario.ubicacion,
            'tipo': mov.get_tipo_movimiento_display(),
            'cantidad': mov.cantidad,
            'cantidad_anterior': mov.cantidad_anterior,
            'cantidad_nueva': mov.cantidad_nueva,
            'fecha': mov.fecha_movimiento.strftime('%d/%m/%Y %H:%M'),
            'usuario': mov.usuario.nombre if mov.usuario else 'Sistema',
            'proveedor': mov.proveedor or '-',
            'motivo': mov.motivo or '-'
        } for mov in movimientos[:100]]  # Limitar a 100 registros
        
        return JsonResponse({'success': True, 'movimientos': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def alertas_inventario(request):
    """Vista para obtener alertas activas de inventario"""
    from inventarios.models import AlertaInventario
    
    user = request.user
    
    try:
        # Obtener alertas no resueltas
        alertas = AlertaInventario.objects.filter(resuelta=False).select_related('inventario__id_producto')
        
        data = [{
            'id': alerta.id_alerta,
            'producto': alerta.inventario.id_producto.nombre,
            'ubicacion': alerta.inventario.ubicacion,
            'tipo': alerta.get_tipo_alerta_display(),
            'stock_actual': alerta.inventario.cantidad_actual,
            'stock_minimo': alerta.inventario.stock_minimo,
            'fecha': alerta.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
        } for alerta in alertas]
        
        return JsonResponse({'success': True, 'alertas': data, 'total': len(data)})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def exportar_inventario_excel(request):
    """Exportar inventario completo a Excel"""
    from openpyxl.utils import get_column_letter
    
    user = request.user
    
    try:
        # Obtener inventarios
        inventarios = Inventario.objects.select_related('id_producto').all()
        
        # Crear workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventario"
        
        # Estilos
        header_fill = PatternFill(start_color="4F81F7", end_color="4F81F7", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Encabezados
        headers = ['ID', 'Producto', 'Ubicación', 'Stock Actual', 'Stock Mínimo', 'Stock Máximo', 'Nivel', 'Última Actualización']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Datos
        for row, inv in enumerate(inventarios, 2):
            ws.cell(row=row, column=1, value=inv.id_inventario).border = border
            ws.cell(row=row, column=2, value=inv.id_producto.nombre).border = border
            ws.cell(row=row, column=3, value=inv.ubicacion).border = border
            ws.cell(row=row, column=4, value=inv.cantidad_actual).border = border
            ws.cell(row=row, column=5, value=inv.stock_minimo).border = border
            ws.cell(row=row, column=6, value=inv.stock_maximo).border = border
            ws.cell(row=row, column=7, value=inv.nivel_stock.upper()).border = border
            ws.cell(row=row, column=8, value=inv.fecha_ultima_actualizacion.strftime('%d/%m/%Y %H:%M')).border = border
            
            # Color según nivel de stock
            nivel_cell = ws.cell(row=row, column=7)
            if inv.nivel_stock == 'critico':
                nivel_cell.fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
                nivel_cell.font = Font(color="FFFFFF", bold=True)
            elif inv.nivel_stock == 'bajo':
                nivel_cell.fill = PatternFill(start_color="FFA500", end_color="FFA500", fill_type="solid")
                nivel_cell.font = Font(color="FFFFFF", bold=True)
            elif inv.nivel_stock == 'alto':
                nivel_cell.fill = PatternFill(start_color="00FF00", end_color="00FF00", fill_type="solid")
        
        # Ajustar anchos
        column_widths = [8, 35, 25, 15, 15, 15, 12, 20]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Respuesta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Inventario_Lilis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        wb.save(response)
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar: {str(e)}')
        return redirect('dashboard:inventarios')

@login_required
def exportar_movimientos_excel(request):
    """Exportar historial de movimientos a Excel"""
    from inventarios.models import MovimientoInventario
    from openpyxl.utils import get_column_letter
    
    user = request.user
    
    try:
        # Obtener movimientos (últimos 1000)
        movimientos = MovimientoInventario.objects.select_related('inventario__id_producto', 'usuario').all()[:1000]
        
        # Crear workbook
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Movimientos"
        
        # Estilos
        header_fill = PatternFill(start_color="4F81F7", end_color="4F81F7", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Encabezados
        headers = ['ID', 'Fecha', 'Producto', 'Ubicación', 'Tipo', 'Cantidad', 'Stock Anterior', 'Stock Nuevo', 'Usuario', 'Proveedor', 'Motivo']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Datos
        for row, mov in enumerate(movimientos, 2):
            ws.cell(row=row, column=1, value=mov.id_movimiento).border = border
            ws.cell(row=row, column=2, value=mov.fecha_movimiento.strftime('%d/%m/%Y %H:%M')).border = border
            ws.cell(row=row, column=3, value=mov.inventario.id_producto.nombre).border = border
            ws.cell(row=row, column=4, value=mov.inventario.ubicacion).border = border
            ws.cell(row=row, column=5, value=mov.get_tipo_movimiento_display()).border = border
            ws.cell(row=row, column=6, value=mov.cantidad).border = border
            ws.cell(row=row, column=7, value=mov.cantidad_anterior).border = border
            ws.cell(row=row, column=8, value=mov.cantidad_nueva).border = border
            ws.cell(row=row, column=9, value=mov.usuario.nombre if mov.usuario else 'Sistema').border = border
            ws.cell(row=row, column=10, value=mov.proveedor or '-').border = border
            ws.cell(row=row, column=11, value=mov.motivo or '-').border = border
            
            # Color según tipo
            tipo_cell = ws.cell(row=row, column=5)
            if mov.tipo_movimiento == 'entrada':
                tipo_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif mov.tipo_movimiento == 'salida':
                tipo_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        
        # Ajustar anchos
        column_widths = [8, 18, 30, 20, 15, 12, 15, 15, 20, 25, 35]
        for i, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = width
        
        # Respuesta
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="Movimientos_Inventario_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        wb.save(response)
        return response
        
    except Exception as e:
        messages.error(request, f'Error al exportar: {str(e)}')
        return redirect('dashboard:inventarios')

def forgot_password_view(request):
    """Vista para recuperación de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            usuario = Usuario.objects.get(correo=email)
            
            # Crear token de recuperación
            token = PasswordResetToken.objects.create(usuario=usuario)
            
            # Construir URL de recuperación
            site_url = settings.SITE_URL.rstrip('/') if hasattr(settings, 'SITE_URL') else request.build_absolute_uri('/').rstrip('/')
            reset_url = f'{site_url}/reset-password/?token={token.token}'
            
            # Renderizar template de email
            html_message = render_to_string('dashboard/password_reset_email.html', {
                'usuario': usuario,
                'reset_url': reset_url,
                'token': token
            })
            plain_message = strip_tags(html_message)
            
            # Enviar email
            send_mail(
                subject='Recuperación de Contraseña - Dulcería Lilis',
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Se ha enviado un email con las instrucciones para recuperar tu contraseña'
                })
            
            messages.success(request, 'Se ha enviado un email con las instrucciones para recuperar tu contraseña')
            return redirect('dashboard:login')
            
        except Usuario.DoesNotExist:
            # Por seguridad, no revelamos que el email no existe
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Si el email existe, recibirás instrucciones para recuperar tu contraseña'
                })
            
            messages.info(request, 'Si el email existe, recibirás instrucciones para recuperar tu contraseña')
            return redirect('dashboard:login')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Error al enviar el email. Por favor intenta nuevamente.'
                })
            
            messages.error(request, 'Error al enviar el email. Por favor intenta nuevamente.')
    
    return render(request, 'dashboard/forgot_password.html')

def reset_password_view(request):
    """Vista para resetear contraseña con token"""
    token_str = request.GET.get('token') or request.POST.get('token')
    
    if not token_str:
        messages.error(request, 'Token de recuperación no válido')
        return redirect('dashboard:login')
    
    try:
        token = PasswordResetToken.objects.get(token=token_str)
        
        if not token.is_valid():
            messages.error(request, 'El token ha expirado o ya fue usado. Solicita uno nuevo.')
            return redirect('dashboard:forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            if password != password_confirm:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Las contraseñas no coinciden'
                    })
                messages.error(request, 'Las contraseñas no coinciden')
            elif len(password) < 8:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'La contraseña debe tener al menos 8 caracteres'
                    })
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            else:
                # Cambiar contraseña
                usuario = token.usuario
                usuario.password = make_password(password)
                usuario.save()
                
                # Marcar token como usado
                token.is_used = True
                token.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Contraseña cambiada exitosamente'
                    })
                
                messages.success(request, 'Contraseña cambiada exitosamente. Ahora puedes iniciar sesión.')
                return redirect('dashboard:login')
        
        context = {
            'token': token_str,
            'usuario': token.usuario
        }
        return render(request, 'dashboard/reset_password.html', context)
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Token de recuperación no válido')
        return redirect('dashboard:login')


@login_required
def usuarios_view(request):
    """Vista de gestión de usuarios con búsqueda, paginación y ordenamiento"""
    user = request.user
    
    # Solo administradores pueden gestionar usuarios
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        raise PermissionDenied("No tienes permisos para gestionar usuarios")
    
    # Usar el modelo de Usuario personalizado
    from usuarios.models import Usuario
    from roles.models import Rol
    usuarios = Usuario.objects.select_related('id_rol').all()
    roles = Rol.objects.all()
    
    # Búsqueda por múltiples campos
    search = request.GET.get('search', '')
    if search:
        usuarios = usuarios.filter(
            nombre__icontains=search
        ) | usuarios.filter(
            username__icontains=search
        ) | usuarios.filter(
            email__icontains=search
        ) | usuarios.filter(
            correo__icontains=search
        )
    
    # Ordenamiento
    order_by = request.GET.get('order_by', 'id_usuario')
    order_direction = request.GET.get('order_direction', 'asc')
    
    # Construir el campo de ordenamiento
    if order_direction == 'desc':
        order_field = f'-{order_by}' if not order_by.startswith('-') else order_by
    else:
        order_field = order_by.replace('-', '')
    
    usuarios = usuarios.order_by(order_field)
    
    # Paginación - obtener de sesión o de parámetro GET
    per_page_param = request.GET.get('per_page')
    if per_page_param:
        per_page = int(per_page_param)
        request.session['usuarios_per_page'] = per_page
    else:
        per_page = request.session.get('usuarios_per_page', 10)
        # Asegurar que sea entero
        if isinstance(per_page, str):
            per_page = int(per_page)
    
    paginator = Paginator(usuarios, per_page)
    page = request.GET.get('page', 1)
    usuarios_paginados = paginator.get_page(page)
    
    context = {
        'usuarios': usuarios_paginados,
        'roles': roles,
        'search': search,
        'order_by': order_by.replace('-', ''),
        'order_direction': order_direction,
        'per_page': per_page,
        'usuarios_count': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(is_active=True).count(),
        'usuarios_inactivos': Usuario.objects.filter(is_active=False).count(),
        'nuevos_usuarios': 0,  # Mock data
        'user': request.user,
    }
    return render(request, 'dashboard/usuarios.html', context)

@login_required
def obtener_usuario(request, usuario_id):
    """API para obtener datos de un usuario en formato JSON"""
    import traceback
    
    # Verificar autenticación
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'No autenticado'}, status=401)
    
    user = request.user
    
    # Solo administradores pueden acceder
    try:
        if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
            return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error verificando permisos: {str(e)}'}, status=500)
    
    try:
        from usuarios.models import Usuario
        usuario = Usuario.objects.select_related('id_rol').get(id_usuario=usuario_id)
        
        data = {
            'success': True,
            'usuario': {
                'id': usuario.id_usuario,
                'usuario': usuario.username,
                'email': usuario.email,
                'nombre': usuario.nombre,
                'telefono': usuario.telefono or '',
                'id_rol': usuario.id_rol.id_rol if usuario.id_rol else '',
                'is_active': usuario.is_active,
                'cambiar_password': False  # Por defecto no forzar cambio
            }
        }
        return JsonResponse(data)
    except Usuario.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Usuario no encontrado'}, status=404)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error en obtener_usuario: {error_trace}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

@login_required
def guardar_usuario(request):
    """API para crear o actualizar un usuario"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        from usuarios.models import Usuario
        from roles.models import Rol
        import secrets
        import string
        
        usuario_id = request.POST.get('user_id')
        email = request.POST.get('email', '').strip()
        nombre = request.POST.get('nombre', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        id_rol = request.POST.get('id_rol')
        # El checkbox puede venir como 'on', 'true', o no venir
        activo = request.POST.get('activo', 'off') in ['on', 'true', True]
        forzar_cambio = request.POST.get('forzar_cambio_contrasena', 'on') in ['on', 'true', True]
        
        # Validaciones básicas
        print(f"DEBUG - Datos recibidos: email={email}, nombre={nombre}, id_rol={id_rol}")
        
        if not email:
            return JsonResponse({
                'success': False, 
                'errors': {'email': ['El campo Email es requerido']}
            })
        
        if not nombre:
            return JsonResponse({
                'success': False, 
                'errors': {'nombre': ['El campo Nombre es requerido']}
            })
        
        if not id_rol:
            return JsonResponse({
                'success': False, 
                'errors': {'id_rol': ['El campo Rol es requerido']}
            })
        
        # Obtener el rol
        try:
            rol = Rol.objects.get(pk=id_rol)
        except Rol.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': {'id_rol': ['El rol seleccionado no existe']}
            })
        
        # Modo edición o creación
        if usuario_id:
            # Editar usuario existente
            usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
            
            # Verificar que el email no esté siendo usado por otro usuario
            if Usuario.objects.filter(correo=email).exclude(id_usuario=usuario_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'email': ['Este correo electrónico ya está registrado']}
                })
            
            # Actualizar datos
            usuario.username = email
            usuario.email = email
            usuario.correo = email
            usuario.nombre = nombre
            usuario.telefono = telefono if telefono else None
            usuario.id_rol = rol
            usuario.is_active = activo
            
            usuario.save()
            action = 'actualizado'
            temp_password = None  # No se genera contraseña en edición
        else:
            # Crear nuevo usuario
            # Verificar que el email no exista
            if Usuario.objects.filter(correo=email).exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'email': ['Este correo electrónico ya está registrado']}
                })
            
            # RQ-USR-02: Generar contraseña temporal robusta
            # Requisitos: min 8 caracteres, 1 mayúscula, 1 minúscula, 1 dígito, 1 especial
            temp_password = generar_contrasena_robusta()
            
            # Crear usuario
            usuario = Usuario(
                username=email,
                email=email,
                correo=email,
                nombre=nombre,
                telefono=telefono if telefono else None,
                id_rol=rol,
                is_active=activo,
                forzar_cambio_contrasena=forzar_cambio
            )
            usuario.set_password(temp_password)
            usuario.save()
            action = 'creado'
            
            # RQ-USR-03: Enviar correo con credenciales
            try:
                enviar_correo_bienvenida(usuario, temp_password)
            except Exception as email_error:
                print(f"Error al enviar correo: {email_error}")
                # No fallar la creación si el correo falla
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'message': f'Usuario {action} correctamente',
            'usuario': {
                'id': usuario.id_usuario,
                'usuario': usuario.username,
                'nombre': usuario.nombre,
                'email': usuario.email
            }
        }
        
        # Si es un nuevo usuario, incluir la contraseña temporal
        if temp_password:
            response_data['temp_password'] = temp_password
            response_data['message'] = f'Usuario creado correctamente. Contraseña temporal: {temp_password}'
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'general': [str(e)]}
        }, status=500)

@login_required
def eliminar_usuario(request, usuario_id):
    """API para eliminar un usuario"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        from usuarios.models import Usuario
        usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
        
        # Verificar si el usuario puede ser eliminado
        if not usuario.can_be_deleted():
            return JsonResponse({
                'success': False,
                'message': 'No se puede eliminar este usuario porque es un administrador del sistema'
            })
        
        # No permitir eliminar el usuario actual
        if usuario.id_usuario == user.id_usuario:
            return JsonResponse({
                'success': False,
                'message': 'No puedes eliminar tu propia cuenta'
            })
        
        nombre = usuario.nombre
        usuario.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario "{nombre}" eliminado correctamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar el usuario: {str(e)}'
        }, status=500)

@login_required
def cambiar_contrasena_obligatorio(request):
    """Vista para cambio de contraseña obligatorio en el primer login"""
    user = request.user
    
    # Si el usuario no necesita cambiar la contraseña, redirigir al dashboard
    if not hasattr(user, 'forzar_cambio_contrasena') or not user.forzar_cambio_contrasena:
        return redirect('dashboard:home')
    
    if request.method == 'POST':
        nueva_contrasena = request.POST.get('nueva_contrasena', '')
        confirmar_contrasena = request.POST.get('confirmar_contrasena', '')
        
        # Validaciones
        if not nueva_contrasena:
            messages.error(request, 'La nueva contraseña es requerida')
        elif len(nueva_contrasena) < 8:
            messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
        elif nueva_contrasena != confirmar_contrasena:
            messages.error(request, 'Las contraseñas no coinciden')
        else:
            # Cambiar la contraseña
            user.set_password(nueva_contrasena)
            user.forzar_cambio_contrasena = False
            user.save()
            
            # Re-autenticar al usuario con la nueva contraseña
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, 'Contraseña cambiada exitosamente')
            return redirect('dashboard:home')
    
    return render(request, 'dashboard/cambiar_contrasena_obligatorio.html', {
        'user': user
    })

@login_required
def resetear_contrasena_usuario(request, usuario_id):
    """
    RQ-USR-06: Reset de contraseña por administrador
    Genera nueva clave temporal robusta, marca flag de cambio obligatorio,
    y envía correo al usuario con las nuevas credenciales.
    """
    user = request.user
    
    # Solo administradores pueden resetear contraseñas
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        from usuarios.models import Usuario
        
        # Obtener el usuario
        usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
        
        # No permitir resetear la propia contraseña con esta función
        if usuario.id_usuario == user.id_usuario:
            return JsonResponse({
                'success': False,
                'message': 'No puedes resetear tu propia contraseña. Usa la opción de cambio de contraseña.'
            })
        
        # RQ-USR-06: Generar nueva contraseña temporal robusta
        nueva_temp_password = generar_contrasena_robusta()
        
        # Actualizar usuario
        usuario.set_password(nueva_temp_password)
        usuario.forzar_cambio_contrasena = True  # Marcar flag de cambio obligatorio
        usuario.save()
        
        # RQ-USR-06: Enviar correo con nueva contraseña temporal
        try:
            enviar_correo_reset_password(usuario, nueva_temp_password, user.nombre)
        except Exception as email_error:
            print(f"Error al enviar correo de reset: {email_error}")
            # Continuar aunque falle el correo (la contraseña ya fue reseteada)
        
        return JsonResponse({
            'success': True,
            'message': f'Contraseña reseteada correctamente para {usuario.nombre}. Se ha enviado un correo con la nueva contraseña temporal.',
            'temp_password': nueva_temp_password,  # Mostrar al admin por si falla el correo
            'usuario': {
                'id': usuario.id_usuario,
                'nombre': usuario.nombre,
                'email': usuario.correo
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al resetear contraseña: {str(e)}'
        }, status=500)


@login_required
def cambiar_estado_usuario(request, usuario_id):
    """API para activar/desactivar un usuario"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    try:
        from usuarios.models import Usuario
        usuario = get_object_or_404(Usuario, id_usuario=usuario_id)
        
        # No permitir cambiar el estado del usuario actual
        if usuario.id_usuario == user.id_usuario:
            return JsonResponse({
                'success': False,
                'message': 'No puedes cambiar el estado de tu propia cuenta'
            })
        
        # Obtener el nuevo estado
        nuevo_estado = request.POST.get('activo', 'false') == 'true'
        
        # Si se intenta desactivar, verificar si puede ser desactivado
        if not nuevo_estado and not usuario.can_be_deactivated():
            return JsonResponse({
                'success': False,
                'message': 'No se puede desactivar este usuario porque es un administrador del sistema'
            })
        
        # Cambiar estado
        usuario.is_active = nuevo_estado
        usuario.save()
        
        estado_texto = 'activado' if nuevo_estado else 'desactivado'
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario "{usuario.nombre}" {estado_texto} correctamente',
            'nuevo_estado': nuevo_estado
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        }, status=500)

@login_required
def exportar_usuarios_excel(request):
    """Exportar lista de usuarios a Excel"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    try:
        from usuarios.models import Usuario
        
        # Crear libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Usuarios"
        
        # Estilos
        header_fill = PatternFill(start_color="DC2626", end_color="DC2626", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Encabezados
        headers = ['ID', 'Usuario', 'Email', 'Nombre', 'Teléfono', 'Rol', 'Estado', 'Último Acceso', 'Fecha Creación']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Obtener usuarios
        usuarios = Usuario.objects.select_related('id_rol').all().order_by('-date_joined')
        
        # Llenar datos
        for row_num, usuario in enumerate(usuarios, 2):
            ws.cell(row=row_num, column=1).value = usuario.id_usuario
            ws.cell(row=row_num, column=2).value = usuario.username
            ws.cell(row=row_num, column=3).value = usuario.email
            ws.cell(row=row_num, column=4).value = usuario.nombre
            ws.cell(row=row_num, column=5).value = usuario.telefono or ''
            ws.cell(row=row_num, column=6).value = usuario.id_rol.nombre if usuario.id_rol else 'Sin rol'
            ws.cell(row=row_num, column=7).value = 'Activo' if usuario.is_active else 'Inactivo'
            ws.cell(row=row_num, column=8).value = usuario.last_login.strftime('%Y-%m-%d %H:%M') if usuario.last_login else 'Nunca'
            ws.cell(row=row_num, column=9).value = usuario.date_joined.strftime('%Y-%m-%d %H:%M') if usuario.date_joined else ''
            
            # Aplicar bordes
            for col_num in range(1, len(headers) + 1):
                ws.cell(row=row_num, column=col_num).border = border
                ws.cell(row=row_num, column=col_num).alignment = Alignment(vertical='center')
        
        # Ajustar ancho de columnas
        column_widths = [8, 20, 30, 25, 15, 20, 12, 20, 20]
        for col_num, width in enumerate(column_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = width
        
        # Crear respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename=usuarios_{fecha_actual}.xlsx'
        
        # Guardar y devolver
        wb.save(response)
        return response
        
    except Exception as e:
        import traceback
        print(f"Error exportando usuarios: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error al exportar: {str(e)}'
        }, status=500)

@login_required
def exportar_productos_excel(request):
    """Exportar lista de productos a Excel"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        return JsonResponse({'success': False, 'message': 'No tienes permisos'}, status=403)
    
    try:
        from productos.models import Producto
        
        # Crear libro de Excel
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Productos"
        
        # Estilos
        header_fill = PatternFill(start_color="DC2626", end_color="DC2626", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=12)
        border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Encabezados
        headers = ['ID', 'Nombre', 'Descripción', 'Precio Referencia']
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num)
            cell.value = header
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
        
        # Obtener productos
        productos = Producto.objects.all().order_by('nombre')
        
        # Llenar datos
        for row_num, producto in enumerate(productos, 2):
            ws.cell(row=row_num, column=1).value = producto.id_producto
            ws.cell(row=row_num, column=2).value = producto.nombre
            ws.cell(row=row_num, column=3).value = producto.descripcion
            ws.cell(row=row_num, column=4).value = producto.precio_referencia
            
            # Formatear precio como moneda
            ws.cell(row=row_num, column=4).number_format = '$#,##0'
            
            # Aplicar bordes
            for col_num in range(1, len(headers) + 1):
                ws.cell(row=row_num, column=col_num).border = border
                ws.cell(row=row_num, column=col_num).alignment = Alignment(vertical='center')
        
        # Ajustar ancho de columnas
        column_widths = [8, 35, 50, 18]
        for col_num, width in enumerate(column_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(col_num)].width = width
        
        # Crear respuesta HTTP
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        fecha_actual = datetime.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename=productos_{fecha_actual}.xlsx'
        
        # Guardar y devolver
        wb.save(response)
        return response
        
    except Exception as e:
        import traceback
        print(f"Error exportando productos: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'message': f'Error al exportar: {str(e)}'
        }, status=500)

@login_required
def obtener_producto(request, producto_id):
    """API para obtener detalles de un producto en formato JSON"""
    import traceback
    
    # Verificar autenticación
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'No autenticado'}, status=401)
    
    try:
        from productos.models import Producto
        from producto_proveedor.models import ProductoProveedor
        
        producto = Producto.objects.get(id_producto=producto_id)
        
        # Obtener proveedores asociados
        proveedores_asociados = ProductoProveedor.objects.filter(
            id_producto=producto
        ).select_related('id_proveedor')
        
        proveedores_data = []
        for pp in proveedores_asociados:
            proveedores_data.append({
                'id': pp.id_proveedor.id_proveedor,
                'nombre': pp.id_proveedor.nombre,
                'contacto': pp.id_proveedor.contacto if hasattr(pp.id_proveedor, 'contacto') else '',
                'precio_acordado': pp.precio_acordado,
                'fecha_registro': pp.fecha_registro.strftime('%Y-%m-%d') if pp.fecha_registro else ''
            })
        
        data = {
            'success': True,
            'producto': {
                'id': producto.id_producto,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio_referencia': producto.precio_referencia,
                'proveedores': proveedores_data
            }
        }
        return JsonResponse(data)
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Producto no encontrado'}, status=404)
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error en obtener_producto: {error_trace}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)

@login_required
def actualizar_producto(request):
    """API para actualizar un producto"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    
    # Verificar permisos: Administrador y Bodeguero pueden editar
    user = request.user
    rol_nombre = user.id_rol.nombre if hasattr(user, 'id_rol') and user.id_rol else None
    
    if rol_nombre not in ['Administrador', 'Bodeguero'] and not user.is_superuser:
        return JsonResponse({
            'success': False, 
            'message': 'No tienes permisos para editar productos.'
        }, status=403)
    
    try:
        from productos.models import Producto
        
        producto_id = request.POST.get('product_id')
        nombre = request.POST.get('nombre', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        precio_referencia = request.POST.get('precio_referencia', '').strip()
        
        # Validaciones
        if not producto_id:
            return JsonResponse({
                'success': False, 
                'errors': {'product_id': ['ID de producto no proporcionado']}
            }, status=400)
        
        if not nombre:
            return JsonResponse({
                'success': False, 
                'errors': {'nombre': ['El campo Nombre es requerido']}
            }, status=400)
        
        if len(nombre) > 150:
            return JsonResponse({
                'success': False, 
                'errors': {'nombre': ['El nombre no puede exceder 150 caracteres']}
            }, status=400)
        
        if descripcion and len(descripcion) > 191:
            return JsonResponse({
                'success': False, 
                'errors': {'descripcion': ['La descripción no puede exceder 191 caracteres']}
            }, status=400)
        
        if not precio_referencia:
            return JsonResponse({
                'success': False, 
                'errors': {'precio_referencia': ['El campo Precio de Referencia es requerido']}
            }, status=400)
        
        try:
            precio_valor = int(precio_referencia)
            if precio_valor <= 0:
                return JsonResponse({
                    'success': False, 
                    'errors': {'precio_referencia': ['El precio debe ser mayor a 0']}
                }, status=400)
        except ValueError:
            return JsonResponse({
                'success': False, 
                'errors': {'precio_referencia': ['El precio debe ser un número válido']}
            }, status=400)
        
        # Actualizar producto
        producto = Producto.objects.get(id_producto=producto_id)
        producto.nombre = nombre
        producto.descripcion = descripcion
        producto.precio_referencia = precio_valor
        producto.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Producto actualizado correctamente',
            'producto': {
                'id': producto.id_producto,
                'nombre': producto.nombre,
                'descripcion': producto.descripcion,
                'precio_referencia': producto.precio_referencia
            }
        })
        
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Producto no encontrado'}, status=404)
    except Exception as e:
        import traceback
        print(f"Error actualizando producto: {traceback.format_exc()}")
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'}, status=500)


# ==========================================
# Vistas de Error Personalizadas
# ==========================================

def error_404(request, exception=None):
    """Vista personalizada para error 404 - Página no encontrada"""
    return render(request, 'dashboard/error_404.html', status=404)


def error_500(request):
    """Vista personalizada para error 500 - Error del servidor"""
    return render(request, 'dashboard/error_500.html', status=500)


def error_403(request, exception=None):
    """Vista personalizada para error 403 - Acceso denegado"""
    return render(request, 'dashboard/error_403.html', status=403)