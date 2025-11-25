# 📊 Instrucciones para Pruebas de Stress/Rendimiento

## Check List de Pruebas de Stress

Basado en el documento proporcionado, se deben realizar las siguientes pruebas:

### 1. ST-PROD-01: Búsqueda y Filtrado con Alto Volumen
- **Volumen**: 10,000 productos
- **Caso de prueba**: Búsqueda y filtrado con alto volumen
- **Datos**: BD con ~10,000 productos
- **Resultado esperado**: Respuesta de filtros dentro de umbral definido, sin timeouts ni errores 500

### 2. ST-PROD-02: Paginación en Listado de Productos
- **Volumen**: 10,000 productos
- **Caso de prueba**: Paginación en listado de productos
- **Datos**: BD con ~10,000 productos, paginador activo
- **Resultado esperado**: Cambio de página fluido, sin registros duplicados/omitidos

### 3. ST-PROV-01: Filtros y Paginación en Proveedores
- **Volumen**: 5,000 proveedores
- **Caso de prueba**: Filtros y paginación en proveedores
- **Datos**: BD con ~5,000 proveedores
- **Resultado esperado**: Paginación y filtros responden dentro del tiempo esperado

### 4. ST-INV-01: Filtros por Fecha, Tipo de Movimiento, Producto
- **Volumen**: ≥10,000 movimientos
- **Caso de prueba**: Filtros por fecha, tipo de movimiento, producto
- **Datos**: BD con alto volumen de movimientos
- **Resultado esperado**: Resultados consistentes, tiempos aceptables, sin errores

### 5. ST-CONC-01: Usuarios Concurrentes
- **Volumen**: N usuarios simultáneos
- **Caso de prueba**: Usuarios concurrentes usando filtros y paginación
- **Datos**: Herramientas de carga (JMeter, etc.)
- **Resultado esperado**: Sistema mantiene estabilidad, errores bajo umbral definido, uso de CPU/memoria aceptable

### 6. ST-CONC-02: Login Concurrentes
- **Volumen**: N usuarios simultáneos
- **Caso de prueba**: Prueba de carga sobre login
- **Datos**: Múltiples logins concurrentes
- **Resultado esperado**: Tiempos de respuesta controlados, sin caída del servicio

---

## 🚀 Pasos para Ejecutar Pruebas en AWS

### Paso 1: Generar Fixtures (En tu máquina local)

```bash
# En el directorio del proyecto
python generate_stress_fixtures.py
```

Esto generará 5 archivos en `fixtures/`:
- `stress_test_productos.json` (10,000 registros)
- `stress_test_proveedores.json` (5,000 registros)
- `stress_test_inventarios.json` (10,000 registros)
- `stress_test_movimientos.json` (10,000 registros)
- `stress_test_usuarios.json` (100 registros)

### Paso 2: Subir Fixtures a AWS

```bash
# Desde tu máquina local, copia los fixtures a AWS
scp -i tu-clave.pem fixtures/stress_test_*.json usuario@tu-ip-aws:/ruta/proyecto/fixtures/
```

O si ya tienes el código actualizado en AWS con git:

```bash
# Conectarte a AWS
ssh -i tu-clave.pem usuario@tu-ip-aws

# Ir al proyecto
cd /ruta/de/tu/proyecto

# Generar fixtures en el servidor
python generate_stress_fixtures.py
```

### Paso 3: Cargar Fixtures en la Base de Datos

```bash
# En AWS, activar entorno virtual
source venv/bin/activate

# Cargar fixtures EN ORDEN (importante para las relaciones)
python manage.py loaddata fixtures/stress_test_productos.json
python manage.py loaddata fixtures/stress_test_proveedores.json
python manage.py loaddata fixtures/stress_test_inventarios.json
python manage.py loaddata fixtures/stress_test_usuarios.json
python manage.py loaddata fixtures/stress_test_movimientos.json

# O cargar todos a la vez
python manage.py loaddata fixtures/stress_test_*.json
```

### Paso 4: Verificar Carga de Datos

```bash
# Entrar a la shell de Django
python manage.py shell

# Verificar cantidad de registros
from productos.models import Producto
from proveedores.models import Proveedor
from inventarios.models import Inventario, MovimientoInventario
from usuarios.models import Usuario

print(f"Productos: {Producto.objects.count()}")
print(f"Proveedores: {Proveedor.objects.count()}")
print(f"Inventarios: {Inventario.objects.count()}")
print(f"Movimientos: {MovimientoInventario.objects.count()}")
print(f"Usuarios: {Usuario.objects.count()}")
```

Deberías ver:
```
Productos: 10000+
Proveedores: 5000+
Inventarios: 10000+
Movimientos: 10000+
Usuarios: 100+
```

---

## 🧪 Ejecutar Pruebas de Stress

### Prueba Manual (ST-PROD-01, ST-PROD-02, ST-PROV-01, ST-INV-01)

1. Accede a la aplicación web
2. Ve a cada módulo y prueba:
   - **Productos**: Buscar, filtrar, paginar entre 10,000 registros
   - **Proveedores**: Buscar, filtrar, paginar entre 5,000 registros
   - **Inventario**: Filtrar movimientos por fecha/tipo/producto
3. Mide tiempos de respuesta (usa Developer Tools > Network)

### Prueba de Concurrencia (ST-CONC-01, ST-CONC-02)

Usa herramientas como Apache JMeter, Locust o Artillery:

#### Opción 1: Locust (Python)

```bash
# Instalar Locust
pip install locust

# Crear archivo locustfile.py
```

```python
from locust import HttpUser, task, between

class DulceriaUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        self.client.post("/dashboard/login/", {
            "username": "usuario.test1@dulcerialilis.cl",
            "password": "test123"
        })
    
    @task(3)
    def view_productos(self):
        self.client.get("/dashboard/productos/")
    
    @task(2)
    def view_proveedores(self):
        self.client.get("/dashboard/proveedores/")
    
    @task(1)
    def view_inventarios(self):
        self.client.get("/dashboard/inventarios/")
```

```bash
# Ejecutar prueba con 50 usuarios concurrentes
locust -f locustfile.py --host=https://tu-dominio.com --users 50 --spawn-rate 10
```

#### Opción 2: Apache Bench (Simple)

```bash
# 1000 requests, 50 concurrentes
ab -n 1000 -c 50 https://tu-dominio.com/dashboard/productos/

# Prueba de login
ab -n 500 -c 25 -p login.txt -T application/x-www-form-urlencoded https://tu-dominio.com/dashboard/login/
```

---

## 📈 Métricas a Monitorear

1. **Tiempo de respuesta**: < 3 segundos para listados con paginación
2. **Errores**: Tasa de error < 1%
3. **CPU**: Uso < 80% en picos
4. **Memoria**: Sin memory leaks
5. **Base de datos**: Query time < 1 segundo

---

## 🧹 Limpiar Datos de Prueba (Después de las pruebas)

```bash
# Entrar a la shell de Django
python manage.py shell

# Ejecutar
from productos.models import Producto
from proveedores.models import Proveedor
from inventarios.models import Inventario, MovimientoInventario
from usuarios.models import Usuario

# Borrar datos de prueba (CUIDADO en producción)
Producto.objects.filter(nombre__startswith='Producto ').delete()
Proveedor.objects.filter(nombre__startswith='Proveedor Test').delete()
Usuario.objects.filter(email__contains='usuario.test').delete()
MovimientoInventario.objects.filter(motivo__contains='prueba').delete()
```

O crear un comando de management:

```bash
python manage.py flush_test_data
```

---

## ⚠️ Recomendaciones

1. **Backup**: Haz un backup de la BD antes de cargar fixtures
2. **Entorno de pruebas**: Usa una instancia separada para stress tests
3. **Monitoreo**: Usa CloudWatch (AWS) para monitorear recursos
4. **Indexación**: Asegúrate de tener índices en campos de búsqueda
5. **Cache**: Considera usar Redis/Memcached para mejorar rendimiento
