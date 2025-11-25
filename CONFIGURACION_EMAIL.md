# 📧 Configuración de Email para Django

Este proyecto soporta **SendGrid** (recomendado para producción/AWS) y **Gmail** (para desarrollo local).

---

## 🚀 Opción 1: SendGrid (Recomendado para AWS/Producción)

### Ventajas de SendGrid:
- ✅ Más confiable en producción
- ✅ Mayor límite de envíos (100 correos/día gratis, 40,000-100,000 con planes pagos)
- ✅ No requiere "App Passwords" ni autenticación de 2 factores
- ✅ Mejor deliverability (menos spam)
- ✅ Métricas y estadísticas incluidas

### Paso 1: Crear cuenta en SendGrid

1. Ve a https://signup.sendgrid.com/
2. Crea una cuenta gratuita
3. Verifica tu email

### Paso 2: Crear API Key

1. Ve a **Settings** > **API Keys**
2. Click en **Create API Key**
3. Nombre: `Django-Dulceria-Lilis`
4. Tipo: **Restricted Access**
5. Permisos: Solo marca **Mail Send** > **Full Access**
6. Click **Create & View**
7. **COPIA LA API KEY** (solo se muestra una vez)

### Paso 3: Verificar dominio o email (Sender Authentication)

#### Opción A: Single Sender Verification (Más fácil)
1. Ve a **Settings** > **Sender Authentication**
2. Click **Verify a Single Sender**
3. Completa el formulario:
   - From Name: `Dulcería Lilis`
   - From Email Address: `noreply@tudominio.com` (o un email que controles)
   - Reply To: Tu email real
4. **Verifica el email** que SendGrid te envía
5. Una vez verificado, ya puedes enviar desde ese email

#### Opción B: Domain Authentication (Recomendado para producción)
1. Ve a **Settings** > **Sender Authentication**
2. Click **Authenticate Your Domain**
3. Sigue las instrucciones para agregar registros DNS

### Paso 4: Configurar Variables de Entorno

En tu archivo `.env` en AWS:

```bash
# SendGrid Configuration
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
DEFAULT_FROM_EMAIL=noreply@tudominio.com
SITE_URL=https://tudominio.com
```

**IMPORTANTE:** 
- El `EMAIL_HOST_USER` SIEMPRE debe ser `apikey` (literal)
- El `EMAIL_HOST_PASSWORD` es tu API Key de SendGrid
- El `DEFAULT_FROM_EMAIL` debe ser el email que verificaste en el paso 3

### Paso 5: Probar envío de correo

```bash
# En AWS, ejecuta la shell de Django
python manage.py shell

# Ejecuta este código
from django.core.mail import send_mail
send_mail(
    'Test SendGrid',
    'Esto es una prueba desde Django con SendGrid',
    'noreply@tudominio.com',
    ['tu-email@gmail.com'],
    fail_silently=False,
)
```

---

## 📨 Opción 2: Gmail (Solo para desarrollo local)

### Ventajas de Gmail:
- ✅ Fácil de configurar
- ✅ No requiere cuenta adicional
- ⚠️ Limitado a 500 correos/día
- ⚠️ Puede ser bloqueado por políticas de seguridad

### Paso 1: Habilitar verificación en 2 pasos

1. Ve a tu cuenta de Google: https://myaccount.google.com/
2. Ve a **Seguridad** en el menú lateral
3. Busca **Verificación en dos pasos** y actívala
4. Sigue el proceso (necesitarás tu teléfono)

### Paso 2: Generar App Password

1. Una vez habilitada la verificación en 2 pasos, ve a:
   https://myaccount.google.com/apppasswords
2. Selecciona **App**: Correo
3. Selecciona **Dispositivo**: Otro (personalizado)
4. Escribe: "Django Dulceria Lilis"
5. Click en **Generar**
6. Google te mostrará una contraseña de 16 caracteres (ejemplo: `abcd efgh ijkl mnop`)
7. **COPIA ESTA CONTRASEÑA** (se muestra solo una vez)

### Paso 3: Configurar Variables de Entorno

En tu archivo `.env` local:

```bash
# Gmail Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=abcd efgh ijkl mnop
DEFAULT_FROM_EMAIL=tu-email@gmail.com
SITE_URL=http://127.0.0.1:8000
```

**Nota:** El `EMAIL_HOST_PASSWORD` es el App Password generado, NO tu contraseña de Gmail.

---

## 🧪 Modo Desarrollo (Console Backend)

Para desarrollo sin enviar emails reales:

```bash
# En .env, agrega:
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Los correos se imprimirán en la consola en lugar de enviarse.

---

## 📋 Funcionalidades Implementadas

### RQ-USR-02: Generación de contraseña robusta
- Longitud: 12 caracteres
- Incluye: mayúsculas, minúsculas, números, caracteres especiales
- Validación con expresión regular

### RQ-USR-03: Envío de correo con credenciales
- Se envía automáticamente al crear un usuario
- Incluye username, contraseña temporal y enlace al login
- Template HTML profesional

### RQ-USR-04: Forzar cambio de contraseña
- Middleware que bloquea todas las URLs excepto login/logout/password-change
- Se activa cuando `forzar_cambio_contrasena = True`

### RQ-USR-06: Reseteo de contraseña por administrador
- Botón "Resetear Contraseña" en gestión de usuarios
- Genera nueva contraseña temporal
- Envía correo con las nuevas credenciales
- Fuerza cambio en siguiente login

---

## ⚠️ Consideraciones de Seguridad

1. **Nunca subas el archivo `.env` a git**
2. **Usa variables de entorno en producción** (AWS Systems Manager, Docker secrets, etc.)
3. **Rota las API Keys regularmente** en SendGrid
4. **Monitorea los envíos** en el dashboard de SendGrid
5. **Limita los permisos** de la API Key solo a Mail Send

---

## 🔧 Troubleshooting

### Error: "Authentication failed"
- **SendGrid**: Verifica que `EMAIL_HOST_USER=apikey` (literal)
- **Gmail**: Verifica que hayas generado un App Password, no uses tu contraseña normal

### Error: "Sender address rejected"
- **SendGrid**: Verifica que hayas completado Single Sender Verification
- **Gmail**: Asegúrate de que `DEFAULT_FROM_EMAIL` sea tu email de Gmail

### Correos van a spam
- **SendGrid**: Completa Domain Authentication para mejor reputación
- **Gmail**: Es normal en desarrollo, en producción usa SendGrid

### Error: "SMTPSenderRefused"
- Verifica que todas las variables de entorno estén configuradas correctamente
- Reinicia el servidor Django después de cambiar `.env`

---

## 📊 Comparación SendGrid vs Gmail

| Característica | SendGrid (Free) | Gmail |
|---------------|-----------------|-------|
| Límite diario | 100 correos/día | 500 correos/día |
| Configuración | Media | Fácil |
| Confiabilidad producción | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Deliverability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Métricas | Sí | No |
| Recomendado para | AWS/Producción | Desarrollo local |

---

## 📞 Soporte

- **SendGrid Docs**: https://docs.sendgrid.com/
- **Django Email Docs**: https://docs.djangoproject.com/en/5.2/topics/email/
