# 🚀 Guía de Despliegue en AWS

## 📋 Resumen de Cambios

Esta rama `feature-mejoras` incluye:
- ✅ Validaciones de campos (backend + frontend)
- ✅ Campo RUT en proveedores (con migración)
- ✅ Sistema de gestión de inventario completo
- ✅ Requisitos de contraseñas (RQ-USR-02 a RQ-USR-06)
- ✅ Configuración para SendGrid
- ✅ Fixtures para pruebas de stress (40,100 registros)

---

## 🔧 Paso 1: Actualizar Código en AWS

```bash
# Conectarte a tu instancia EC2
ssh -i tu-clave.pem ubuntu@tu-ip-aws

# Ir al directorio del proyecto
cd /ruta/de/tu/proyecto

# Ver rama actual
git branch

# Fetch cambios del remoto
git fetch origin

# Cambiar a la rama feature-mejoras
git checkout feature-mejoras

# Hacer pull de los últimos cambios
git pull origin feature-mejoras
```

---

## ⚙️ Paso 2: Actualizar Variables de Entorno

Edita tu archivo `.env` en AWS:

```bash
nano .env
```

**Asegúrate de tener estas variables:**

```bash
# GENERAL
DJANGO_SECRET_KEY=tu-secret-key-aqui
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=tu-ip-aws,localhost,tu-dominio.com

# BASE DE DATOS
USE_MYSQL=True
DB_NAME=dulceria_db
DB_USER=root
DB_PASSWORD=tu-password-db
DB_HOST=tu-rds-endpoint.rds.amazonaws.com
DB_PORT=3306

# INTERNACIONALIZACIÓN
DJANGO_LANGUAGE_CODE=es-cl
DJANGO_TIME_ZONE=America/Santiago

# SENDGRID
SENDGRID_API_KEY=SG.tu-api-key-de-sendgrid-aqui
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=tu-email@gmail.com
SITE_URL=http://tu-ip-aws
```

**💡 IMPORTANTE:** El sistema detecta automáticamente `SENDGRID_API_KEY` y configura:
- `EMAIL_HOST_USER = 'apikey'`
- `EMAIL_HOST_PASSWORD = SENDGRID_API_KEY`

---

## 🗄️ Paso 3: Aplicar Migraciones de Base de Datos

```bash
# Activar entorno virtual (si lo usas)
source venv/bin/activate

# Aplicar TODAS las migraciones
python manage.py migrate

# Deberías ver:
# - inventarios.0002: Agrega stock_minimo, stock_maximo, MovimientoInventario, AlertaInventario
# - proveedores.0002: Agrega campo rut
```

---

## 📦 Paso 4: Recolectar Archivos Estáticos

```bash
python manage.py collectstatic --noinput
```

---

## 🔄 Paso 5: Reiniciar Servicios

### Si usas Gunicorn + Nginx:

```bash
# Reiniciar Gunicorn
sudo systemctl restart gunicorn

# Verificar estado
sudo systemctl status gunicorn

# Reiniciar Nginx
sudo systemctl restart nginx

# Verificar estado
sudo systemctl status nginx
```

### Si usas otro servidor (uWSGI, Apache):

```bash
# uWSGI
sudo systemctl restart uwsgi

# Apache
sudo systemctl restart apache2
```

---

## ✅ Paso 6: Verificar Funcionamiento

### 6.1 Verificar que el servidor esté corriendo

```bash
# Ver logs de Gunicorn
sudo journalctl -u gunicorn -f

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log
```

### 6.2 Probar en el navegador

```
http://tu-ip-aws/dashboard/login/
```

### 6.3 Verificar migraciones aplicadas

```bash
python manage.py showmigrations
```

Deberías ver `[X]` en:
- `inventarios 0002_inventario_stock_maximo_inventario_stock_minimo_and_more`
- `proveedores 0002_proveedor_rut`

### 6.4 Probar envío de emails

```bash
python manage.py shell
```

```python
from django.core.mail import send_mail

send_mail(
    'Test desde AWS',
    'Este es un correo de prueba desde la instancia EC2',
    'tu-email@gmail.com',
    ['tu-email@gmail.com'],
    fail_silently=False,
)
```

Deberías recibir el email en unos segundos.

---

## 📊 Paso 7: Cargar Datos de Prueba (Opcional)

**⚠️ SOLO para pruebas de stress, NO en producción con datos reales**

```bash
# Cargar todos los fixtures de prueba
python manage.py loaddata fixtures/stress_test_productos.json
python manage.py loaddata fixtures/stress_test_proveedores.json
python manage.py loaddata fixtures/stress_test_inventarios.json
python manage.py loaddata fixtures/stress_test_usuarios.json
python manage.py loaddata fixtures/stress_test_movimientos.json

# O todo de una vez
python manage.py loaddata fixtures/stress_test_*.json
```

**Esto cargará:**
- 10,000 productos
- 5,000 proveedores
- 10,000 inventarios
- 10,000 movimientos
- 100 usuarios de prueba

**Para eliminar después:**

```bash
python manage.py shell
```

```python
from productos.models import Producto
from proveedores.models import Proveedor
from inventarios.models import MovimientoInventario
from usuarios.models import Usuario

# Eliminar datos de prueba
Producto.objects.filter(nombre__startswith='Producto ').delete()
Proveedor.objects.filter(nombre__startswith='Proveedor Test').delete()
Usuario.objects.filter(email__contains='usuario.test').delete()
MovimientoInventario.objects.all().delete()
```

---

## 🔍 Troubleshooting

### Error: "No module named 'decouple'"

```bash
pip install python-decouple
```

### Error: "No such table: inventarios_movimientoinventario"

```bash
# Aplicar migraciones
python manage.py migrate inventarios
```

### Error: "Column 'rut' doesn't exist"

```bash
# Aplicar migración de proveedores
python manage.py migrate proveedores
```

### Error: Email no se envía

1. Verifica que `SENDGRID_API_KEY` esté correcta
2. Verifica que el email en `DEFAULT_FROM_EMAIL` esté verificado en SendGrid
3. Revisa logs: `sudo journalctl -u gunicorn -f`

### Error: "403 Forbidden"

Verifica que tu IP esté en `DJANGO_ALLOWED_HOSTS`

### Error: Static files no se cargan

```bash
# Recolectar estáticos
python manage.py collectstatic --noinput

# Verificar configuración de Nginx
sudo nano /etc/nginx/sites-available/dulceria

# Debe tener:
location /static/ {
    alias /ruta/proyecto/staticfiles/;
}
```

---

## 📝 Checklist Final

- [ ] Código actualizado con `git pull`
- [ ] Variables de entorno configuradas en `.env`
- [ ] Migraciones aplicadas (`migrate`)
- [ ] Archivos estáticos recolectados (`collectstatic`)
- [ ] Servicios reiniciados (Gunicorn + Nginx)
- [ ] Login funciona en el navegador
- [ ] Email de prueba enviado correctamente
- [ ] Nuevos campos (RUT en proveedores) funcionan
- [ ] Inventario muestra nuevos campos (stock_minimo, stock_maximo)

---

## 🔐 Seguridad Post-Despliegue

```bash
# 1. Verificar que DEBUG=False
grep DEBUG .env

# 2. Verificar permisos del .env
chmod 600 .env

# 3. Verificar que .env NO esté en git
cat .gitignore | grep .env

# 4. Actualizar DJANGO_SECRET_KEY si es necesario
# Generar nueva: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## 📞 Soporte

Si tienes problemas:
1. Revisa los logs: `sudo journalctl -u gunicorn -f`
2. Revisa errores de Nginx: `sudo tail -f /var/log/nginx/error.log`
3. Prueba en modo debug temporal (cambia `DJANGO_DEBUG=True` en `.env`)

---

## 🎉 ¡Listo!

Tu aplicación ahora tiene:
- ✅ Validaciones de campos completas
- ✅ Campo RUT en proveedores
- ✅ Sistema de inventario avanzado
- ✅ Gestión de contraseñas segura
- ✅ Envío de emails con SendGrid
- ✅ Fixtures para pruebas de stress
