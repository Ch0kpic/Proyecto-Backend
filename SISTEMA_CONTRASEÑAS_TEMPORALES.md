# 🔐 Sistema de Contraseñas Temporales - Dulcería Lilis

## 📋 Resumen de Cambios

Se ha implementado un sistema de contraseñas temporales para mejorar la seguridad. Ahora cuando un administrador crea un nuevo usuario, **NO** debe ingresar la contraseña manualmente.

---

## ✨ Características Nuevas

### 1. **Creación Automática de Contraseña Temporal**
- Al crear un usuario, el sistema genera automáticamente una contraseña temporal segura
- La contraseña tiene 12 caracteres con letras, números y símbolos especiales
- Se muestra una ÚNICA VEZ al administrador después de crear el usuario

### 2. **Cambio Obligatorio en Primer Login**
- Cuando un nuevo usuario inicia sesión por primera vez, DEBE cambiar su contraseña
- El sistema lo redirige automáticamente a una página de cambio de contraseña
- No puede acceder al sistema hasta que cambie la contraseña temporal

### 3. **Requisitos de Contraseña Segura**
La nueva contraseña del usuario debe cumplir:
- ✅ Mínimo 8 caracteres
- ✅ Al menos una letra mayúscula
- ✅ Al menos una letra minúscula
- ✅ Al menos un número

---

## 🎯 Cómo Crear un Nuevo Usuario (Pasos para Administradores)

### Paso 1: Ir a la sección de Usuarios
Navega a **Dashboard → Usuarios**

### Paso 2: Llenar el formulario
Completa los siguientes campos:
- **Nombre**: Nombre completo del usuario
- **Email**: Correo electrónico (será su nombre de usuario)
- **Teléfono**: Número de contacto (opcional)
- **Rol**: Selecciona el rol apropiado (Administrador, Vendedor, Bodeguero, etc.)
- **Estado y acceso**: Marca si el usuario estará activo
- **Usuario debe cambiar contraseña**: Está marcado por defecto ✅

### Paso 3: Guardar
Haz clic en el botón **"Guardar"**

### Paso 4: ⚠️ IMPORTANTE - Copiar la Contraseña Temporal
Después de crear el usuario, aparecerá un mensaje con la **contraseña temporal**:

```
┌─────────────────────────────────────┐
│  ⚠️ Contraseña Temporal:            │
│  Abc123!@xyz                         │
│                                      │
│  Guarda esta contraseña.            │
│  El usuario deberá cambiarla        │
│  en su primer inicio de sesión.     │
└─────────────────────────────────────┘
```

**IMPORTANTE**: 
- ✉️ Envía esta contraseña al usuario de forma segura (email, mensaje privado, etc.)
- 📋 Copia y guarda la contraseña antes de cerrar el mensaje
- ⚠️ Esta es la ÚNICA VEZ que se mostrará esta contraseña

---

## 👤 Proceso para el Nuevo Usuario

### 1. Recibir credenciales
El administrador le enviará:
- **Usuario**: su correo electrónico
- **Contraseña temporal**: código aleatorio de 12 caracteres

### 2. Primer inicio de sesión
- Ir a la página de login
- Ingresar su email y contraseña temporal
- El sistema lo redirigirá automáticamente a "Cambiar Contraseña"

### 3. Crear contraseña personal
En la pantalla de cambio de contraseña:
- Ingresar nueva contraseña (cumplir requisitos de seguridad)
- Confirmar la nueva contraseña
- Hacer clic en "Cambiar Contraseña"

### 4. Acceso completo
Después de cambiar la contraseña, podrá acceder al sistema normalmente.

---

## 🔄 Usuarios Existentes

**Los usuarios creados ANTES de esta actualización NO necesitan cambiar su contraseña.**

Solo los nuevos usuarios (creados a partir de ahora) tendrán que cambiar la contraseña temporal.

---

## ❓ Preguntas Frecuentes

### ¿Qué pasa si pierdo la contraseña temporal antes de enviarla?
No hay problema. Como administrador, puedes:
1. Editar el usuario
2. Marcar nuevamente "Usuario debe cambiar contraseña"
3. Guardar
4. Esto generará una nueva contraseña temporal

### ¿Puedo deshabilitar el cambio obligatorio de contraseña?
Sí, al crear o editar un usuario, puedes desmarcar la casilla "Usuario debe cambiar contraseña en el primer inicio de sesión". Sin embargo, por seguridad se recomienda mantenerla activada.

### ¿Qué pasa si un usuario olvida su nueva contraseña?
Pueden usar la opción "¿Olvidaste tu contraseña?" en la pantalla de login para recuperarla por email.

---

## 🛡️ Beneficios de Seguridad

1. **Mayor Seguridad**: Los administradores no conocen las contraseñas finales de los usuarios
2. **Contraseñas Únicas**: Cada usuario crea su propia contraseña personal
3. **Trazabilidad**: El sistema registra cuando se crea un usuario y cuando cambia su contraseña
4. **Cumplimiento**: Cumple con mejores prácticas de seguridad informática

---

## 📝 Notas Técnicas

### Archivos Modificados
- `usuarios/models.py` - Agregado campo `forzar_cambio_contrasena`
- `dashboard/views.py` - Modificadas vistas de login y creación de usuarios
- `dashboard/templates/dashboard/form_usuario.html` - Removidos campos de contraseña
- `dashboard/templates/dashboard/cambiar_contrasena_obligatorio.html` - Nueva página de cambio obligatorio

### Base de Datos
Se agregó el campo `forzar_cambio_contrasena` (BOOLEAN) a la tabla `usuarios_usuario`

### Migración Aplicada
```bash
python manage.py makemigrations usuarios
python manage.py migrate usuarios
```

---

## ✅ Checklist de Implementación

- [x] Agregar campo `forzar_cambio_contrasena` al modelo Usuario
- [x] Crear y aplicar migración
- [x] Actualizar usuarios existentes (forzar_cambio_contrasena = False)
- [x] Modificar formulario de creación de usuarios (remover campos de contraseña)
- [x] Implementar generación de contraseña temporal aleatoria
- [x] Modificar vista de login para verificar cambio obligatorio
- [x] Crear vista y template para cambio de contraseña obligatorio
- [x] Agregar validación de contraseña segura en frontend
- [x] Mostrar contraseña temporal al administrador después de crear usuario
- [x] Agregar ruta para cambio de contraseña obligatorio

---

**Fecha de Implementación**: 17 de Noviembre, 2025  
**Versión del Sistema**: 1.5.0  
**Desarrollado por**: GitHub Copilot para Dulcería Lilis
