from django.db import models
from productos.models import Producto
from usuarios.models import Usuario

class Inventario(models.Model):
    id_inventario = models.AutoField(primary_key=True)
    id_producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    cantidad_actual = models.IntegerField(verbose_name="Cantidad Actual")
    stock_minimo = models.IntegerField(default=10, verbose_name="Stock Mínimo")
    stock_maximo = models.IntegerField(default=100, verbose_name="Stock Máximo")
    ubicacion = models.CharField(max_length=150, verbose_name="Ubicación")
    fecha_ultima_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    
    class Meta:
        verbose_name = "Inventario"
        verbose_name_plural = "Inventarios"
        db_table = "inventario"
        ordering = ['-fecha_ultima_actualizacion']
        unique_together = ['id_producto', 'ubicacion']
    
    def __str__(self):
        return f"{self.id_producto.nombre} - {self.ubicacion}: {self.cantidad_actual} unidades"
    
    @property
    def nivel_stock(self):
        """Retorna el nivel de stock: 'bajo', 'medio', 'alto', 'critico'"""
        if self.cantidad_actual == 0:
            return 'critico'
        elif self.cantidad_actual < self.stock_minimo:
            return 'bajo'
        elif self.cantidad_actual > self.stock_maximo:
            return 'alto'
        else:
            return 'medio'
    
    @property
    def necesita_reabastecimiento(self):
        """Retorna True si el stock está por debajo del mínimo"""
        return self.cantidad_actual < self.stock_minimo
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.cantidad_actual < 0:
            raise ValidationError("La cantidad actual no puede ser negativa.")
        if self.stock_minimo < 0:
            raise ValidationError("El stock mínimo no puede ser negativo.")
        if self.stock_maximo < self.stock_minimo:
            raise ValidationError("El stock máximo debe ser mayor o igual al mínimo.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class MovimientoInventario(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('transferencia', 'Transferencia'),
    ]
    
    id_movimiento = models.AutoField(primary_key=True)
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='movimientos', verbose_name="Inventario")
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo de Movimiento")
    cantidad = models.IntegerField(verbose_name="Cantidad")
    cantidad_anterior = models.IntegerField(verbose_name="Cantidad Anterior")
    cantidad_nueva = models.IntegerField(verbose_name="Cantidad Nueva")
    fecha_movimiento = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Movimiento")
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    proveedor = models.CharField(max_length=200, blank=True, null=True, verbose_name="Proveedor")
    motivo = models.TextField(blank=True, null=True, verbose_name="Motivo/Observaciones")
    
    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        db_table = "movimiento_inventario"
        ordering = ['-fecha_movimiento']
    
    def __str__(self):
        return f"{self.get_tipo_movimiento_display()} - {self.inventario.id_producto.nombre} ({self.cantidad})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a cero.")
        
        # Validar que no se pueda sacar más stock del disponible
        if self.tipo_movimiento == 'salida':
            if self.cantidad > self.inventario.cantidad_actual:
                raise ValidationError(f"No hay suficiente stock. Disponible: {self.inventario.cantidad_actual}")


class AlertaInventario(models.Model):
    TIPO_ALERTA_CHOICES = [
        ('stock_bajo', 'Stock Bajo'),
        ('stock_critico', 'Stock Crítico'),
        ('stock_alto', 'Stock Alto'),
    ]
    
    id_alerta = models.AutoField(primary_key=True)
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE, related_name='alertas', verbose_name="Inventario")
    tipo_alerta = models.CharField(max_length=20, choices=TIPO_ALERTA_CHOICES, verbose_name="Tipo de Alerta")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_resolucion = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Resolución")
    resuelta = models.BooleanField(default=False, verbose_name="Resuelta")
    notificado = models.BooleanField(default=False, verbose_name="Notificado")
    
    class Meta:
        verbose_name = "Alerta de Inventario"
        verbose_name_plural = "Alertas de Inventario"
        db_table = "alerta_inventario"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"{self.get_tipo_alerta_display()} - {self.inventario.id_producto.nombre}"
