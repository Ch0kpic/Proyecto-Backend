from django import forms
from productos.models import Producto
from inventarios.models import Inventario

class ProductoForm(forms.ModelForm):
    """Formulario para crear/editar productos"""
    
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio_referencia']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Chocolatina Jet',
                'required': 'required',
                'maxlength': '150'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-input',
                'placeholder': 'Descripción del producto',
                'rows': 3,
                'maxlength': '191'
            }),
            'precio_referencia': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Precio en pesos chilenos',
                'min': '1',
                'step': '100',
                'required': 'required'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].label = 'Nombre del Producto'
        self.fields['nombre'].required = True
        self.fields['descripcion'].label = 'Descripción'
        self.fields['descripcion'].required = False
        self.fields['precio_referencia'].label = 'Precio de Referencia (pesos chilenos)'
        self.fields['precio_referencia'].required = True

class InventarioForm(forms.ModelForm):
    """Formulario para crear/editar inventarios"""
    
    class Meta:
        model = Inventario
        fields = ['id_producto', 'cantidad_actual', 'ubicacion']
        widgets = {
            'id_producto': forms.Select(attrs={
                'class': 'form-input',
                'required': 'required'
            }),
            'cantidad_actual': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Cantidad en stock',
                'min': '0',
                'required': 'required'
            }),
            'ubicacion': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ej: Estante A1, Bodega Principal',
                'required': 'required'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id_producto'].label = 'Producto'
        self.fields['id_producto'].required = True
        self.fields['cantidad_actual'].label = 'Cantidad Actual'
        self.fields['cantidad_actual'].required = True
        self.fields['ubicacion'].label = 'Ubicación'
        self.fields['ubicacion'].required = True
        
        # Filtrar productos que ya tienen inventario
        if self.instance.pk is None:  # Solo para nuevos inventarios
            productos_con_inventario = Inventario.objects.values_list('id_producto', flat=True)
            self.fields['id_producto'].queryset = Producto.objects.exclude(
                id_producto__in=productos_con_inventario
            )
