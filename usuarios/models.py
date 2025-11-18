from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
import uuid
import re
from roles.models import Rol

class Usuario(AbstractUser):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, verbose_name="Nombre")
    correo = models.EmailField(max_length=150, unique=True, verbose_name="Correo Electrónico")
    contrasena = models.CharField(max_length=128, verbose_name="Contraseña")
    id_rol = models.ForeignKey(Rol, on_delete=models.CASCADE, verbose_name="Rol")
    
    # Campos de perfil
    telefono = models.CharField(max_length=15, blank=True, null=True, verbose_name="Teléfono")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Avatar")
    forzar_cambio_contrasena = models.BooleanField(default=True, verbose_name="Forzar cambio de contraseña")
    
    # Campos adicionales para AbstractUser
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['correo', 'nombre']
    
    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        db_table = "usuario"
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.id_rol.nombre})"
    
    def clean(self):
        super().clean()
        
        # Validar formato del nombre (solo letras y espacios)
        if self.nombre:
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', self.nombre):
                raise ValidationError({'nombre': 'El nombre solo puede contener letras y espacios'})
            
            if len(self.nombre.strip()) < 3:
                raise ValidationError({'nombre': 'El nombre debe tener al menos 3 caracteres'})
        
        # Validar teléfono si se proporciona
        if self.telefono:
            # Eliminar espacios y guiones para validación
            telefono_limpio = self.telefono.replace(' ', '').replace('-', '').replace('+', '')
            if not telefono_limpio.isdigit():
                raise ValidationError({'telefono': 'El teléfono solo puede contener números, espacios, guiones y +'})
            
            if len(telefono_limpio) < 7 or len(telefono_limpio) > 15:
                raise ValidationError({'telefono': 'El teléfono debe tener entre 7 y 15 dígitos'})
    
    def is_admin(self):
        """Verifica si el usuario es administrador"""
        return self.is_superuser or (self.id_rol and self.id_rol.nombre.lower() == 'administrador')
    
    def can_be_deleted(self):
        """Verifica si el usuario puede ser eliminado"""
        # El superusuario o el primer admin no puede ser eliminado
        if self.is_superuser:
            return False
        if self.username == 'admin':
            return False
        return True
    
    def can_be_deactivated(self):
        """Verifica si el usuario puede ser desactivado"""
        # El superusuario o el primer admin no puede ser desactivado
        if self.is_superuser:
            return False
        if self.username == 'admin':
            return False
        return True
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.correo
        if not self.email:
            self.email = self.correo
        
        # Ejecutar validaciones personalizadas
        self.clean()
        
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    """Modelo para almacenar tokens de recuperación de contraseña"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Token de Recuperación"
        verbose_name_plural = "Tokens de Recuperación"
        db_table = "password_reset_token"
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Token válido por 1 hora
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Verifica si el token es válido"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Token para {self.usuario.correo} - {'Válido' if self.is_valid() else 'Expirado/Usado'}"
