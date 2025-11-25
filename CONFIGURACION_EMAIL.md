# Configuración de Email para Envío de Credenciales

## RQ-USR-03: Envío automático de correo con credenciales

El sistema ahora envía automáticamente un correo electrónico cuando se crea un nuevo usuario, incluyendo:
- Username (email de acceso)
- Contraseña temporal generada
- Enlace directo al login
- Instrucciones de seguridad

## Configuración Requerida

### 1. Archivo .env

Agrega las siguientes variables a tu archivo `.env` en la raíz del proyecto:

```env
# Configuración de Email
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=tu-app-password-de-16-digitos
SITE_URL=http://127.0.0.1:8000
```

### 2. Obtener App Password de Gmail

Para usar Gmail como servidor SMTP:

1. **Habilitar verificación en 2 pasos**:
   - Ve a https://myaccount.google.com/security
   - Busca "Verificación en 2 pasos" y actívala

2. **Generar App Password**:
   - Ve a https://myaccount.google.com/apppasswords
   - Selecciona "Correo" y "Otro (nombre personalizado)"
   - Escribe "Dulcería Lilis"
   - Copia el password de 16 dígitos generado
   - Pégalo en `EMAIL_HOST_PASSWORD` en tu archivo `.env`

### 3. Variables de Entorno

```env
# Ejemplo completo
EMAIL_HOST_USER=dulceria.lilis@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
SITE_URL=http://127.0.0.1:8000
```

**Nota**: El `EMAIL_HOST_PASSWORD` debe ser el App Password de 16 dígitos, NO tu contraseña de Gmail normal.

## Prueba del Sistema

### Modo Desarrollo (Sin enviar correos reales)

Si quieres probar sin enviar correos, agrega en `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Esto imprimirá los correos en la consola en lugar de enviarlos.

### Modo Producción (Envío real)

Usa la configuración normal:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
```

O simplemente no definas `EMAIL_BACKEND` (usará el valor por defecto de settings.py).

## Funcionamiento

Cuando un administrador crea un usuario:

1. ✅ Se genera una contraseña robusta (min 8 chars, 1 mayúscula, 1 minúscula, 1 dígito, 1 especial)
2. ✅ Se crea el usuario con `forzar_cambio_contrasena=True`
3. ✅ Se envía un correo HTML profesional al email del usuario
4. ✅ El usuario recibe username + contraseña temporal + enlace de login
5. ✅ Al iniciar sesión, se fuerza cambio de contraseña antes de acceder al sistema

## Solución de Problemas

### Error: "SMTPAuthenticationError"
- Verifica que hayas creado un App Password (no uses tu contraseña normal de Gmail)
- Confirma que la verificación en 2 pasos esté activada

### Error: "SMTPException: STARTTLS extension not supported"
- Verifica que `EMAIL_PORT=587` y `EMAIL_USE_TLS=True` en settings.py

### Los correos no llegan
- Revisa la carpeta de Spam
- Verifica que el email del usuario esté correcto
- Revisa los logs de Django para ver errores

### Modo consola para desarrollo
Si quieres ver los correos sin enviarlos, agrega en `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

## Requisitos Cumplidos

- ✅ **RQ-USR-02**: Generación automática de clave provisoria robusta
  - Longitud mínima: 8 caracteres (se genera con 12)
  - Al menos 1 mayúscula, 1 minúscula, 1 dígito, 1 carácter especial
  - Asociada como temporal (`forzar_cambio_contrasena=True`)

- ✅ **RQ-USR-03**: Envío de correo con clave provisoria
  - Incluye username (email)
  - Incluye contraseña temporal
  - Incluye enlace directo al login
  - No incluye información sensible adicional
  - Correo HTML profesional y responsivo

- ✅ **RQ-USR-04**: Obligación de cambio de clave en primer ingreso
  - Middleware detecta `forzar_cambio_contrasena=True`
  - Redirige automáticamente a pantalla de cambio
  - Bloquea navegación hasta cambiar contraseña
  - Después de cambiar, permite acceso normal

- ✅ **RQ-USR-06**: Cambio de clave cuando la define el administrador
  - Administrador puede resetear contraseña de cualquier usuario
  - Genera nueva contraseña temporal robusta
  - Marca `forzar_cambio_contrasena=True` automáticamente
  - Envía correo con nueva contraseña temporal
  - Al iniciar sesión, usuario debe cambiar la contraseña
  - Botón "Resetear Contraseña" disponible en gestión de usuarios

