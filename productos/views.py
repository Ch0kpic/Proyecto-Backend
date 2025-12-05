from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Producto
from django import forms

class ProductoForm(forms.ModelForm):
    # Campos adicionales que no están en el modelo pero necesitamos en el formulario
    sku = forms.CharField(
        max_length=50, 
        required=False,  # Se validará en __init__
        widget=forms.TextInput(attrs={
            'class': 'form-input', 
            'placeholder': 'SKU-001'
        }),
        error_messages={'required': 'El SKU es obligatorio'}
    )
    ean_upc = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': '7891234567890'}))
    categoria = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Categoría'}))
    marca = forms.CharField(
        max_length=100, 
        required=False,  # Se validará en __init__
        widget=forms.TextInput(attrs={
            'class': 'form-input', 
            'placeholder': 'Marca'
        }),
        error_messages={'required': 'La marca es obligatoria'}
    )
    modelo = forms.CharField(
        max_length=100, 
        required=False,  # Se validará en __init__
        widget=forms.TextInput(attrs={
            'class': 'form-input', 
            'placeholder': 'Modelo'
        }),
        error_messages={'required': 'El modelo es obligatorio'}
    )
    unidad_compra = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Unidad'}))
    factor_conversion = forms.IntegerField(
        initial=1, 
        required=False, 
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '1', 'min': '1'}),
        error_messages={'min_value': 'El factor de conversión debe ser al menos 1'}
    )
    costo_unitario = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
        error_messages={'min_value': 'El costo unitario no puede ser negativo'}
    )
    impuesto = forms.IntegerField(
        initial=19, 
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '19', 'min': '0', 'max': '100'}),
        error_messages={
            'min_value': 'El impuesto no puede ser negativo',
            'max_value': 'El impuesto no puede ser mayor a 100%'
        }
    )
    stock_minimo = forms.IntegerField(
        initial=0, 
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0', 'min': '0'}),
        error_messages={'min_value': 'El stock mínimo no puede ser negativo'}
    )
    stock_maximo = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0', 'min': '0'}),
        error_messages={'min_value': 'El stock máximo no puede ser negativo'}
    )
    punto_reorden = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0', 'min': '0'}),
        error_messages={'min_value': 'El punto de reorden no puede ser negativo'}
    )
    perecedero = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    control_por_lote = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    control_por_serie = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    imagen_url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...imagen.jpg'}))
    ficha_tecnica_url = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://...ficha.pdf'}))
    
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_referencia']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Nombre del producto'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-input', 'placeholder': 'Descripción del producto', 'rows': 3}),
            'precio_referencia': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': '0', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Capturar si es edición (si instance está presente)
        es_edicion = kwargs.get('instance') is not None
        super().__init__(*args, **kwargs)
        
        # Solo hacer obligatorios SKU, marca y modelo al crear (no al editar)
        if not es_edicion:
            self.fields['sku'].required = True
            self.fields['sku'].widget.attrs['required'] = 'required'
            self.fields['marca'].required = True
            self.fields['marca'].widget.attrs['required'] = 'required'
            self.fields['modelo'].required = True
            self.fields['modelo'].widget.attrs['required'] = 'required'
    
    def clean_precio_referencia(self):
        precio = self.cleaned_data.get('precio_referencia')
        if precio is not None and precio < 0:
            raise forms.ValidationError('El precio de referencia no puede ser negativo')
        return precio
    
    def clean(self):
        cleaned_data = super().clean()
        stock_minimo = cleaned_data.get('stock_minimo')
        stock_maximo = cleaned_data.get('stock_maximo')
        punto_reorden = cleaned_data.get('punto_reorden')
        
        # Validar que stock máximo sea mayor o igual a stock mínimo
        if stock_minimo is not None and stock_maximo is not None:
            if stock_maximo > 0 and stock_minimo > stock_maximo:
                raise forms.ValidationError('El stock mínimo no puede ser mayor al stock máximo')
        
        # Validar que punto de reorden esté entre stock mínimo y máximo
        if punto_reorden is not None and stock_minimo is not None and stock_maximo is not None:
            if stock_maximo > 0 and (punto_reorden < stock_minimo or punto_reorden > stock_maximo):
                raise forms.ValidationError('El punto de reorden debe estar entre el stock mínimo y máximo')
        
        return cleaned_data

@login_required
def lista_productos(request):
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
    order_by = request.GET.get('order_by', '-id_producto')
    order_direction = request.GET.get('order_direction', 'desc')
    
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
        'productos_activos': Producto.objects.count(),  # Todos los productos están activos ya que no hay campo activo
    }
    return render(request, 'dashboard/productos.html', context)

@login_required
def form_producto(request):
    """Vista para mostrar el formulario de productos con la lista al lado"""
    productos = Producto.objects.all().order_by('-id_producto')
    
    context = {
        'form': ProductoForm(),
        'productos': productos,
        'title': 'Formulario de Producto'
    }
    return render(request, 'dashboard/form_producto.html', context)

@login_required
def agregar_producto(request):
    """Vista para agregar un nuevo producto con diseño de 3 pasos"""
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            
            # Si es una petición AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'product': {
                        'id': producto.id_producto,
                        'nombre': producto.nombre,
                        'descripcion': producto.descripcion or '',
                        'precio': float(producto.precio_referencia),
                        'categoria': form.cleaned_data.get('categoria', '')
                    }
                })
            
            messages.success(request, f'Producto "{producto.nombre}" creado exitosamente.')
            return redirect('productos:lista_productos')
        else:
            # Si hay errores y es AJAX, responder con JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = ProductoForm()
    
    # Obtener todos los productos para mostrar en la lista
    productos = Producto.objects.all().order_by('-id_producto')
    
    context = {
        'form': form,
        'productos': productos,
        'title': 'Agregar Producto',
        'action': 'agregar'
    }
    return render(request, 'dashboard/form_producto.html', context)

@login_required
def editar_producto(request, producto_id):
    """Vista para editar un producto existente"""
    producto = get_object_or_404(Producto, pk=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f'Producto "{producto.nombre}" actualizado exitosamente.')
            return redirect('productos:lista_productos')
    else:
        form = ProductoForm(instance=producto)
    
    context = {
        'form': form,
        'producto': producto,
        'title': 'Editar Producto',
        'action': 'editar'
    }
    return render(request, 'dashboard/form_producto.html', context)

@login_required
def eliminar_producto(request, producto_id):
    """Vista para eliminar un producto"""
    producto = get_object_or_404(Producto, pk=producto_id)
    
    if request.method == 'POST':
        nombre = producto.nombre
        producto.delete()
        
        # Si es una petición AJAX, responder con JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'Producto "{nombre}" eliminado exitosamente.'
            })
        
        messages.success(request, f'Producto "{nombre}" eliminado exitosamente.')
        return redirect('productos:lista_productos')
    
    return redirect('productos:lista_productos')
