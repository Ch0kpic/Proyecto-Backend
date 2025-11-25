#!/usr/bin/env python
"""
Script para generar fixtures de pruebas de stress/rendimiento
Genera los volúmenes de datos especificados en el Check List de Pruebas
"""

import json
import random
import os

# Configuración de volúmenes según Check List
VOLUMES = {
    'productos': 10000,      # ST-PROD-01, ST-PROD-02
    'proveedores': 5000,     # ST-PROV-01
    'movimientos': 10000,    # ST-INV-01
    'usuarios': 100          # ST-CONC-01, ST-CONC-02
}

def generate_rut():
    """Genera un RUT chileno válido"""
    num = random.randint(10000000, 25000000)
    rut_str = str(num)
    
    # Calcular dígito verificador
    reversed_digits = map(int, reversed(rut_str))
    factors = [2, 3, 4, 5, 6, 7]
    s = sum(d * factors[i % 6] for i, d in enumerate(reversed_digits))
    verificador = 11 - (s % 11)
    
    if verificador == 11:
        verificador = '0'
    elif verificador == 10:
        verificador = 'K'
    else:
        verificador = str(verificador)
    
    # Formatear RUT
    formatted = f"{num:,}".replace(',', '.')
    return f"{formatted}-{verificador}"

def generate_phone():
    """Genera número de teléfono chileno"""
    return f"{random.randint(10000000, 99999999)}"

def generate_productos(count):
    """Genera fixtures de productos"""
    productos = []
    categorias = ['Dulces', 'Chocolates', 'Bebidas', 'Snacks', 'Galletas', 'Caramelos', 'Chicles']
    
    for i in range(1, count + 1):
        producto = {
            "model": "productos.producto",
            "pk": i,
            "fields": {
                "nombre": f"Producto {i} - {random.choice(categorias)}",
                "descripcion": f"Producto de prueba de stress test número {i} para validar rendimiento",
                "precio_referencia": random.randint(500, 50000)
            }
        }
        productos.append(producto)
    
    return productos

def generate_proveedores(count):
    """Genera fixtures de proveedores"""
    proveedores = []
    regiones = ['Metropolitana', 'Valparaíso', 'Biobío', "O'Higgins", 'Maule']
    comunas = ['Santiago', 'Las Condes', 'Providencia', 'Maipú', 'La Florida', 'Puente Alto']
    
    for i in range(1, count + 1):
        proveedor = {
            "model": "proveedores.proveedor",
            "pk": i,
            "fields": {
                "rut": generate_rut(),
                "nombre": f"Proveedor Test {i} S.A.",
                "contacto": f"Contacto {i} - +56 9 {generate_phone()}",
                "direccion": f"Calle Test {i}, {random.choice(comunas)}, {random.choice(regiones)}"
            }
        }
        proveedores.append(proveedor)
    
    return proveedores

def generate_inventarios(producto_count):
    """Genera fixtures de inventarios (uno por producto)"""
    inventarios = []
    ubicaciones = ['Bodega A', 'Bodega B', 'Estante 1', 'Estante 2', 'Zona Refrigerada']
    
    for i in range(1, producto_count + 1):
        inventario = {
            "model": "inventarios.inventario",
            "pk": i,
            "fields": {
                "id_producto": i,
                "cantidad_actual": random.randint(10, 1000),
                "stock_minimo": random.randint(5, 50),
                "stock_maximo": random.randint(500, 2000),
                "ubicacion": f"{random.choice(ubicaciones)} - Posición {i}"
            }
        }
        inventarios.append(inventario)
    
    return inventarios

def generate_movimientos(count, producto_count):
    """Genera fixtures de movimientos de inventario"""
    movimientos = []
    tipos = ['ENTRADA', 'SALIDA', 'AJUSTE', 'DEVOLUCION']
    motivos = [
        'Compra a proveedor',
        'Venta realizada',
        'Ajuste de inventario',
        'Devolución de cliente',
        'Merma detectada',
        'Reposición de stock'
    ]
    
    for i in range(1, count + 1):
        # Usuario aleatorio entre 1-100 (asumiendo que se crearán usuarios)
        usuario_id = random.randint(1, min(100, VOLUMES['usuarios']))
        
        movimiento = {
            "model": "inventarios.movimientoinventario",
            "pk": i,
            "fields": {
                "id_inventario": random.randint(1, producto_count),
                "tipo_movimiento": random.choice(tipos),
                "cantidad": random.randint(1, 100),
                "motivo": random.choice(motivos),
                "usuario_responsable": usuario_id,
                "fecha_movimiento": f"2025-{random.randint(1,11):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:00Z"
            }
        }
        movimientos.append(movimiento)
    
    return movimientos

def generate_usuarios(count):
    """Genera fixtures de usuarios para pruebas de concurrencia"""
    usuarios = []
    roles = [1, 2, 3]  # Asumiendo IDs de roles existentes
    nombres = ['Juan', 'María', 'Carlos', 'Ana', 'Pedro', 'Laura', 'Diego', 'Sofia']
    apellidos = ['González', 'Rodríguez', 'Pérez', 'López', 'Martínez', 'Fernández']
    
    for i in range(1, count + 1):
        nombre = f"{random.choice(nombres)} {random.choice(apellidos)}"
        email = f"usuario.test{i}@dulcerialilis.cl"
        
        usuario = {
            "model": "usuarios.usuario",
            "pk": i + 10,  # Offset para no sobrescribir usuarios existentes
            "fields": {
                "username": email,
                "email": email,
                "correo": email,
                "nombre": nombre,
                "telefono": f"+56 9 {generate_phone()}",
                "id_rol": random.choice(roles),
                "is_active": True,
                "is_staff": False,
                "is_superuser": False,
                "forzar_cambio_contrasena": False,
                "password": "pbkdf2_sha256$600000$test$hashedpassword"  # Password hasheado de "test123"
            }
        }
        usuarios.append(usuario)
    
    return usuarios

def save_fixture(data, filename):
    """Guarda los datos en un archivo JSON"""
    filepath = os.path.join('fixtures', filename)
    os.makedirs('fixtures', exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Creado: {filepath} ({len(data)} registros)")

def main():
    """Función principal"""
    print("=" * 60)
    print("GENERADOR DE FIXTURES PARA PRUEBAS DE STRESS")
    print("=" * 60)
    print()
    print("Generando fixtures según Check List de Pruebas:")
    print(f"  - Productos: {VOLUMES['productos']:,}")
    print(f"  - Proveedores: {VOLUMES['proveedores']:,}")
    print(f"  - Movimientos: {VOLUMES['movimientos']:,}")
    print(f"  - Usuarios: {VOLUMES['usuarios']:,}")
    print()
    
    # Generar y guardar fixtures
    print("Generando fixtures...")
    print()
    
    # Productos (10,000)
    productos = generate_productos(VOLUMES['productos'])
    save_fixture(productos, 'stress_test_productos.json')
    
    # Proveedores (5,000)
    proveedores = generate_proveedores(VOLUMES['proveedores'])
    save_fixture(proveedores, 'stress_test_proveedores.json')
    
    # Inventarios (uno por producto)
    inventarios = generate_inventarios(VOLUMES['productos'])
    save_fixture(inventarios, 'stress_test_inventarios.json')
    
    # Movimientos (10,000)
    movimientos = generate_movimientos(VOLUMES['movimientos'], VOLUMES['productos'])
    save_fixture(movimientos, 'stress_test_movimientos.json')
    
    # Usuarios (100)
    usuarios = generate_usuarios(VOLUMES['usuarios'])
    save_fixture(usuarios, 'stress_test_usuarios.json')
    
    print()
    print("=" * 60)
    print("✓ FIXTURES GENERADOS EXITOSAMENTE")
    print("=" * 60)
    print()
    print("Para cargar en AWS, ejecuta:")
    print("  python manage.py loaddata fixtures/stress_test_productos.json")
    print("  python manage.py loaddata fixtures/stress_test_proveedores.json")
    print("  python manage.py loaddata fixtures/stress_test_inventarios.json")
    print("  python manage.py loaddata fixtures/stress_test_movimientos.json")
    print("  python manage.py loaddata fixtures/stress_test_usuarios.json")
    print()
    print("O carga todo a la vez:")
    print("  python manage.py loaddata fixtures/stress_test_*.json")
    print()

if __name__ == '__main__':
    main()
