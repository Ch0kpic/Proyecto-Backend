from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Usuario
from roles.models import Rol
from django import forms
import os
import re

class UsuarioForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Contraseña'}),
        label='Contraseña'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirmar contraseña'}),
        label='Confirmar contraseña'
    )
    
    class Meta:
        model = Usuario
        fields = ['nombre', 'correo', 'id_rol', 'is_active']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre completo'}),
            'correo': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'correo@ejemplo.com'}),
            'id_rol': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.is_edit = kwargs.pop('is_edit', False)
        super().__init__(*args, **kwargs)
        
        if self.is_edit:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False
            self.fields['password'].help_text = "Deja en blanco para mantener la contraseña actual"
        
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if not self.is_edit or password:
            if password != confirm_password:
                raise forms.ValidationError("Las contraseñas no coinciden")
                
        return cleaned_data

class PerfilForm(forms.ModelForm):
    """Formulario para editar datos del perfil"""
    class Meta:
        model = Usuario
        fields = ['nombre', 'correo', 'telefono', 'avatar']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo'
            }),
            'correo': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+51 999 999 999'
            }),
            'avatar': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/jpeg,image/jpg,image/png,image/gif'
            })
        }
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Validar tamaño (máximo 2MB)
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError('El avatar no puede ser mayor a 2MB')
            
            # Validar formato
            ext = os.path.splitext(avatar.name)[1].lower()
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            if ext not in valid_extensions:
                raise forms.ValidationError('Solo se permiten imágenes (JPG, PNG, GIF)')
        
        return avatar

class CambiarPasswordForm(forms.Form):
    """Formulario para cambio de contraseña"""
    password_actual = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña actual'
        }),
        label='Contraseña actual'
    )
    password_nueva = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nueva contraseña'
        }),
        label='Nueva contraseña',
        help_text='Mínimo 8 caracteres, debe incluir mayúscula y número'
    )
    password_confirmar = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirmar nueva contraseña'
        }),
        label='Confirmar nueva contraseña'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_password_actual(self):
        password_actual = self.cleaned_data.get('password_actual')
        if not check_password(password_actual, self.user.password):
            raise forms.ValidationError('La contraseña actual es incorrecta')
        return password_actual
    
    def clean_password_nueva(self):
        password_nueva = self.cleaned_data.get('password_nueva')
        
        # Validar longitud mínima
        if len(password_nueva) < 8:
            raise forms.ValidationError('La contraseña debe tener al menos 8 caracteres')
        
        # Validar que tenga al menos una mayúscula
        if not re.search(r'[A-Z]', password_nueva):
            raise forms.ValidationError('La contraseña debe contener al menos una letra mayúscula')
        
        # Validar que tenga al menos un número
        if not re.search(r'\d', password_nueva):
            raise forms.ValidationError('La contraseña debe contener al menos un número')
        
        return password_nueva
    
    def clean(self):
        cleaned_data = super().clean()
        password_nueva = cleaned_data.get('password_nueva')
        password_confirmar = cleaned_data.get('password_confirmar')
        
        if password_nueva and password_confirmar:
            if password_nueva != password_confirmar:
                raise forms.ValidationError('Las contraseñas nuevas no coinciden')
        
        return cleaned_data

@login_required
@staff_member_required
def lista_usuarios(request):
    """Vista para listar todos los usuarios"""
    usuarios = Usuario.objects.select_related('id_rol').all().order_by('-date_joined')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        usuarios = usuarios.filter(nombre__icontains=search) | usuarios.filter(correo__icontains=search)
    
    # Paginación
    paginator = Paginator(usuarios, 10)
    page = request.GET.get('page')
    usuarios = paginator.get_page(page)
    
    context = {
        'usuarios': usuarios,
        'search': search,
        'total_usuarios': Usuario.objects.count(),
        'usuarios_activos': Usuario.objects.filter(is_active=True).count(),
    }
    return render(request, 'dashboard/usuarios.html', context)

@login_required
@staff_member_required
def agregar_usuario(request):
    """Vista para agregar un nuevo usuario"""
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            usuario = form.save(commit=False)
            # Establecer username como correo
            usuario.username = form.cleaned_data['correo']
            usuario.email = form.cleaned_data['correo']
            # Encriptar contraseña
            usuario.password = make_password(form.cleaned_data['password'])
            usuario.save()
            
            # Si es una petición AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'user': {
                        'id': usuario.id_usuario,
                        'nombre': usuario.nombre,
                        'correo': usuario.correo,
                        'rol': usuario.id_rol.nombre,
                        'is_active': usuario.is_active
                    }
                })
            
            messages.success(request, f'Usuario "{usuario.nombre}" creado exitosamente.')
            return redirect('usuarios:lista_usuarios')
        else:
            # Si hay errores y es AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = UsuarioForm()
    
    # Obtener todos los usuarios para mostrar en la lista
    usuarios = Usuario.objects.select_related('id_rol').all().order_by('-date_joined')
    
    context = {
        'form': form,
        'usuarios': usuarios,
        'title': 'Agregar Usuario',
        'action': 'agregar'
    }
    return render(request, 'dashboard/form_usuario.html', context)

@login_required
@staff_member_required
def editar_usuario(request, usuario_id):
    """Vista para editar un usuario existente"""
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario, is_edit=True)
        if form.is_valid():
            usuario = form.save(commit=False)
            # Actualizar contraseña solo si se proporcionó una nueva
            if form.cleaned_data['password']:
                usuario.password = make_password(form.cleaned_data['password'])
            usuario.save()
            
            messages.success(request, f'Usuario "{usuario.nombre}" actualizado exitosamente.')
            return redirect('usuarios:lista_usuarios')
    else:
        form = UsuarioForm(instance=usuario, is_edit=True)
    
    context = {
        'form': form,
        'usuario': usuario,
        'title': 'Editar Usuario',
        'action': 'editar'
    }
    return render(request, 'dashboard/form_usuario.html', context)

@login_required
@staff_member_required
def eliminar_usuario(request, usuario_id):
    """Vista para eliminar un usuario"""
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    
    if request.method == 'POST':
        nombre = usuario.nombre
        usuario.delete()
        messages.success(request, f'Usuario "{nombre}" eliminado exitosamente.')
        return redirect('usuarios:lista_usuarios')
    
    # Si es una petición GET desde el modal, redirigir a la lista
    # ya que el modal se maneja en el frontend
    return redirect('usuarios:lista_usuarios')

@login_required
@staff_member_required
def toggle_usuario_status(request, usuario_id):
    """Vista para activar/desactivar usuario"""
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    status = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f'Usuario "{usuario.nombre}" {status} exitosamente.')
    return redirect('usuarios:lista_usuarios')

@login_required
def perfil_usuario(request):
    """Vista para ver y editar el perfil del usuario"""
    usuario = request.user
    
    if request.method == 'POST':
        # Determinar qué formulario se envió
        if 'cambiar_password' in request.POST:
            # Formulario de cambio de contraseña
            password_form = CambiarPasswordForm(usuario, request.POST)
            perfil_form = PerfilForm(instance=usuario)
            
            if password_form.is_valid():
                # Cambiar la contraseña
                usuario.password = make_password(password_form.cleaned_data['password_nueva'])
                usuario.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Contraseña actualizada exitosamente'
                    })
                
                messages.success(request, 'Contraseña actualizada exitosamente.')
                return redirect('usuarios:perfil')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': password_form.errors
                    })
        else:
            # Formulario de perfil
            perfil_form = PerfilForm(request.POST, request.FILES, instance=usuario)
            password_form = CambiarPasswordForm(usuario)
            
            if perfil_form.is_valid():
                usuario = perfil_form.save(commit=False)
                
                # Actualizar username y email si cambió el correo
                if 'correo' in perfil_form.changed_data:
                    usuario.username = perfil_form.cleaned_data['correo']
                    usuario.email = perfil_form.cleaned_data['correo']
                
                usuario.save()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Perfil actualizado exitosamente',
                        'avatar_url': usuario.avatar.url if usuario.avatar else None
                    })
                
                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('usuarios:perfil')
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': perfil_form.errors
                    })
    else:
        perfil_form = PerfilForm(instance=usuario)
        password_form = CambiarPasswordForm(usuario)
    
    context = {
        'perfil_form': perfil_form,
        'password_form': password_form,
        'usuario': usuario
    }
    return render(request, 'dashboard/perfil.html', context)
