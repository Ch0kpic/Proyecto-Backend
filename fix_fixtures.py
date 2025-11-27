"""
Script para corregir las fixtures de inventarios y movimientos
"""
import json
from datetime import datetime, timedelta
import random

def fix_inventarios():
    """Agrega el campo fecha_ultima_actualizacion a las fixtures de inventarios"""
    print("Corrigiendo stress_test_inventarios.json...")
    
    with open('fixtures/stress_test_inventarios.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Agregar fecha_ultima_actualizacion a cada registro
    base_date = datetime(2025, 1, 1)
    for i, item in enumerate(data):
        # Generar una fecha aleatoria entre enero y noviembre 2025
        days_offset = random.randint(0, 300)
        fecha = (base_date + timedelta(days=days_offset)).strftime('%Y-%m-%dT%H:%M:%SZ')
        item['fields']['fecha_ultima_actualizacion'] = fecha
    
    with open('fixtures/stress_test_inventarios.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Corregidos {len(data)} registros de inventarios")

def fix_movimientos():
    """Corrige los campos de las fixtures de movimientos"""
    print("\nCorrigiendo stress_test_movimientos.json...")
    
    with open('fixtures/stress_test_movimientos.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    for item in data:
        fields = item['fields']
        
        # Cambiar id_inventario por inventario
        if 'id_inventario' in fields:
            fields['inventario'] = fields.pop('id_inventario')
        
        # Cambiar usuario_responsable por usuario
        if 'usuario_responsable' in fields:
            fields['usuario'] = fields.pop('usuario_responsable')
        
        # Agregar cantidad_anterior y cantidad_nueva
        cantidad = fields.get('cantidad', 0)
        if 'cantidad_anterior' not in fields:
            # Generar valores lógicos basados en el tipo de movimiento
            tipo = fields.get('tipo_movimiento', 'entrada').lower()
            
            if tipo in ['entrada', 'ajuste']:
                # Para entradas, la cantidad anterior es menor
                cantidad_anterior = max(0, random.randint(0, 100))
                cantidad_nueva = cantidad_anterior + cantidad
            else:  # salida
                # Para salidas, la cantidad anterior es mayor
                cantidad_anterior = cantidad + random.randint(0, 100)
                cantidad_nueva = cantidad_anterior - cantidad
            
            fields['cantidad_anterior'] = cantidad_anterior
            fields['cantidad_nueva'] = max(0, cantidad_nueva)
    
    with open('fixtures/stress_test_movimientos.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Corregidos {len(data)} registros de movimientos")

if __name__ == '__main__':
    print("Iniciando corrección de fixtures...\n")
    fix_inventarios()
    fix_movimientos()
    print("\n✓ Corrección completada exitosamente!")
    print("\nAhora puedes subir los archivos corregidos a tu servidor AWS.")
