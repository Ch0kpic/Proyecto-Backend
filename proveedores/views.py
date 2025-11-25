from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Proveedor
from django import forms

class ProveedorForm(forms.ModelForm):
    # Campos adicionales que no están en el modelo pero necesitamos en el formulario
    razon_social = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Proveedor S.A.'}))
    nombre_fantasia = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Proveedores'}))
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'contacto@proveedor.cl'}))
    telefono = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+56 9 2345 6789'}))
    sitio_web = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://proveedor.cl'}))
    estado = forms.ChoiceField(
        choices=[('ACTIVO', 'ACTIVO'), ('BLOQUEADO', 'BLOQUEADO')],
        initial='ACTIVO',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Proveedor
        fields = ['rut', 'nombre', 'contacto', 'direccion']
        widgets = {
            'rut': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': '20.213.992-2',
                'maxlength': '20'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Nombre del proveedor',
                'required': 'required',
                'maxlength': '150'
            }),
            'contacto': forms.TextInput(attrs={
                'class': 'form-input', 
                'placeholder': 'Persona de contacto',
                'required': 'required',
                'maxlength': '200'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'form-input', 
                'placeholder': 'Dirección completa', 
                'rows': 3,
                'required': 'required',
                'maxlength': '200'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].required = True
        self.fields['contacto'].required = True
        self.fields['direccion'].required = True

@login_required
def lista_proveedores(request):
    """Vista para listar todos los proveedores"""
    proveedores = Proveedor.objects.all().order_by('-id_proveedor')
    
    # Búsqueda
    search = request.GET.get('search', '')
    if search:
        proveedores = proveedores.filter(nombre__icontains=search)
    
    # Paginación
    paginator = Paginator(proveedores, 10)
    page = request.GET.get('page')
    proveedores = paginator.get_page(page)
    
    context = {
        'proveedores': proveedores,
        'search': search,
        'total_proveedores': Proveedor.objects.count(),
    }
    return render(request, 'dashboard/proveedores.html', context)

@login_required
def form_proveedor(request):
    """Vista para mostrar el formulario de proveedores con la lista al lado"""
    proveedores = Proveedor.objects.all().order_by('-id_proveedor')
    
    context = {
        'form': ProveedorForm(),
        'proveedores': proveedores,
        'title': 'Formulario de Proveedor'
    }
    return render(request, 'dashboard/form_proveedor.html', context)

@login_required
def agregar_proveedor(request):
    """Vista para agregar un nuevo proveedor con diseño de 3 pasos"""
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            
            # Si es una petición AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'proveedor': {
                        'id': proveedor.id_proveedor,
                        'nombre': proveedor.nombre,
                        'contacto': proveedor.contacto or '',
                        'direccion': proveedor.direccion or '',
                        'rut': proveedor.rut or '',
                        'estado': form.cleaned_data.get('estado', 'ACTIVO')
                    }
                })
            
            messages.success(request, f'Proveedor "{proveedor.nombre}" creado exitosamente.')
            return redirect('proveedores:lista_proveedores')
        else:
            # Si hay errores y es AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = ProveedorForm()
    
    # Obtener todos los proveedores para mostrar en la lista
    proveedores = Proveedor.objects.all().order_by('-id_proveedor')
    
    context = {
        'form': form,
        'proveedores': proveedores,
        'title': 'Agregar Proveedor',
        'action': 'agregar'
    }
    return render(request, 'dashboard/form_proveedor.html', context)

@login_required
def editar_proveedor(request, proveedor_id):
    """Vista para editar un proveedor existente"""
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, f'Proveedor "{proveedor.nombre}" actualizado exitosamente.')
            return redirect('proveedores:lista_proveedores')
    else:
        form = ProveedorForm(instance=proveedor)
    
    context = {
        'form': form,
        'proveedor': proveedor,
        'title': 'Editar Proveedor',
        'action': 'editar'
    }
    return render(request, 'dashboard/form_proveedor.html', context)

@login_required
def eliminar_proveedor(request, proveedor_id):
    """Vista para eliminar un proveedor"""
    proveedor = get_object_or_404(Proveedor, pk=proveedor_id)
    
    if request.method == 'POST':
        nombre = proveedor.nombre
        proveedor.delete()
        
        # Si es una petición AJAX, responder con JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Proveedor "{nombre}" eliminado exitosamente.'
            })
        
        messages.success(request, f'Proveedor "{nombre}" eliminado exitosamente.')
        return redirect('proveedores:lista_proveedores')
    
    return redirect('proveedores:lista_proveedores')
