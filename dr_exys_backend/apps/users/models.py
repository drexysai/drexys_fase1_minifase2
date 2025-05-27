from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modelo de usuário customizado para plataforma médica Dr. Exys
    Campos adicionais para profissionais de saúde
    """
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=30, verbose_name='Nome')
    last_name = models.CharField(max_length=30, verbose_name='Sobrenome')
    phone = models.CharField(max_length=15, blank=True, verbose_name='Telefone')
    
    # Campos específicos para área médica
    crm = models.CharField(max_length=20, blank=True, verbose_name='CRM')
    especialidade = models.CharField(max_length=100, blank=True, verbose_name='Especialidade')
    is_medical_professional = models.BooleanField(default=False, verbose_name='É Profissional de Saúde')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    def __str__(self):
        if self.crm:
            return f"Dr(a). {self.first_name} {self.last_name} - CRM: {self.crm}"
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    def get_full_name(self):
        """Retorna nome completo do usuário médico"""
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = 'Usuário Médico'
        verbose_name_plural = 'Usuários Médicos'
        db_table = 'users'  # ← MUDANÇA: removido 'medicos.'