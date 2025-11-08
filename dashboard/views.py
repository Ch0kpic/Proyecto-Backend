from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.hashers import make_password
from django.conf import settings
from productos.models import Producto
from inventarios.models import Inventario
from usuarios.models import Usuario, PasswordResetToken
from .forms import ProductoForm, InventarioForm

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
    }
    return render(request, 'dashboard/productos.html', context)

@login_required
def inventarios_view(request):
    """Vista de inventarios"""
    inventarios = Inventario.objects.select_related('id_producto').all()
    now = timezone.now()
    
    # Mock data para proveedores
    class MockProveedor:
        def __init__(self, id_proveedor, nombre):
            self.id_proveedor = id_proveedor
            self.nombre = nombre
    
    proveedores = [
        MockProveedor(1, 'Distribuidora Nacional'),
        MockProveedor(2, 'Dulces Premium SAC'),
        MockProveedor(3, 'Confitería del Norte'),
    ]
    
    context = {
        'inventarios': inventarios,
        'proveedores': proveedores,
        'total_productos': inventarios.count(),
        'stock_alto': 0,  # Calcular basado en lógica de stock
        'stock_medio': 0,
        'stock_bajo': 0,
        'today': now.date(),
        'user': request.user,
    }
    return render(request, 'dashboard/inventarios.html', context)

@login_required
def proveedores_view(request):
    """Vista ficticia de proveedores"""
    user = request.user
    
    # Solo administradores pueden acceder
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        raise PermissionDenied("No tienes permisos para acceder a esta sección")
    
    # Datos ficticios para proveedores
    class MockProveedor:
        def __init__(self, id_proveedor, nombre, contacto, telefono, email):
            self.id_proveedor = id_proveedor
            self.nombre = nombre
            self.contacto = contacto
            self.telefono = telefono
            self.email = email
    
    proveedores = [
        MockProveedor(1, 'Distribuidora Nacional', 'Juan Pérez', '123-456-7890', 'contacto@distrinacional.com'),
        MockProveedor(2, 'Dulces Premium SAC', 'María García', '098-765-4321', 'ventas@dulcespremium.com'),
        MockProveedor(3, 'Confitería del Norte', 'Carlos López', '555-123-4567', 'info@confiterianorte.com'),
    ]
    
    # Productos disponibles para asociar con proveedores
    productos_disponibles = Producto.objects.all()
    
    context = {
        'proveedores': proveedores,
        'productos_disponibles': productos_disponibles,
        'proveedores_count': len(proveedores),
        'proveedores_activos': len(proveedores),
        'productos_proveedor': productos_disponibles.count(),
        'ordenes_pendientes': 0,
        'user': request.user,
    }
    return render(request, 'dashboard/proveedores.html', context)

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

def forgot_password_view(request):
    """Vista para recuperación de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            usuario = Usuario.objects.get(correo=email)
            
            # Crear token de recuperación
            token = PasswordResetToken.objects.create(usuario=usuario)
            
            # Construir URL de recuperación
            reset_url = request.build_absolute_uri(
                f'/reset-password/?token={token.token}'
            )
            
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
    """Vista de gestión de usuarios"""
    user = request.user
    
    # Solo administradores pueden gestionar usuarios
    if not (user.is_superuser or (hasattr(user, 'id_rol') and user.id_rol.nombre == 'Administrador')):
        raise PermissionDenied("No tienes permisos para gestionar usuarios")
    
    # Usar el modelo de Usuario personalizado
    from usuarios.models import Usuario
    from roles.models import Rol
    usuarios = Usuario.objects.select_related('id_rol').all()
    roles = Rol.objects.all()
    
    context = {
        'usuarios': usuarios,
        'roles': roles,
        'usuarios_count': usuarios.count(),
        'usuarios_activos': usuarios.filter(is_active=True).count(),
        'usuarios_inactivos': usuarios.filter(is_active=False).count(),
        'nuevos_usuarios': 0,  # Mock data
        'user': request.user,
    }
    return render(request, 'dashboard/usuarios.html', context)