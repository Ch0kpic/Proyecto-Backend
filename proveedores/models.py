from django.db import models

class Proveedor(models.Model):
    id_proveedor = models.AutoField(primary_key=True)
    rut = models.CharField(max_length=20, null=True, blank=True, verbose_name='RUT/NIF')
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(max_length=200)
    direccion = models.CharField(max_length=200)

    class Meta:
        db_table = 'proveedor'
