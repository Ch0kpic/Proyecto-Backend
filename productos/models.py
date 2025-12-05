from django.db import models

class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Producto")
    descripcion = models.CharField(max_length=191, verbose_name="Descripción", blank=True, null=True)
    precio_referencia = models.IntegerField(verbose_name="Precio de Referencia")
    
    # Campos adicionales de identificación
    sku = models.CharField(max_length=50, verbose_name="SKU", blank=True, null=True)
    ean_upc = models.CharField(max_length=50, verbose_name="EAN/UPC", blank=True, null=True)
    categoria = models.CharField(max_length=100, verbose_name="Categoría", blank=True, null=True)
    marca = models.CharField(max_length=100, verbose_name="Marca", blank=True, null=True)
    modelo = models.CharField(max_length=100, verbose_name="Modelo", blank=True, null=True)
    
    # Campos de compra y stock
    unidad_compra = models.CharField(max_length=50, verbose_name="Unidad de Compra", blank=True, null=True)
    factor_conversion = models.IntegerField(verbose_name="Factor de Conversión", default=1)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Costo Unitario", blank=True, null=True)
    impuesto = models.IntegerField(verbose_name="Impuesto (%)", default=19)
    stock_minimo = models.IntegerField(verbose_name="Stock Mínimo", default=0)
    stock_maximo = models.IntegerField(verbose_name="Stock Máximo", blank=True, null=True)
    punto_reorden = models.IntegerField(verbose_name="Punto de Reorden", blank=True, null=True)
    
    # Campos de control
    perecedero = models.BooleanField(verbose_name="Perecedero", default=False)
    control_por_lote = models.BooleanField(verbose_name="Control por Lote", default=False)
    control_por_serie = models.BooleanField(verbose_name="Control por Serie", default=False)
    
    # Campos multimedia
    imagen_url = models.URLField(verbose_name="URL de Imagen", blank=True, null=True)
    ficha_tecnica_url = models.URLField(verbose_name="URL de Ficha Técnica", blank=True, null=True)
    
    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        db_table = "producto"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio_referencia:,}"
