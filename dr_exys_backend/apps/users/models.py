from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modelo de usuário customizado para plataforma médica Dr. Exys
    
    CAMPOS OBRIGATÓRIOS:
    - email (único)
    - username (único) 
    - password
    
    CAMPOS OPCIONAIS:
    - first_name, last_name (podem ser preenchidos depois)
    - phone, crm, especialidade (campos médicos opcionais)
    """
    
    # CAMPOS ESSENCIAIS (obrigatórios)
    email = models.EmailField(unique=True, verbose_name='Email')
    
    # CAMPOS PESSOAIS (opcionais - podem ser preenchidos posteriormente)
    first_name = models.CharField(
        max_length=30, 
        blank=True,  # ← MUDANÇA: agora opcional
        null=True,   # ← MUDANÇA: permite null no banco
        verbose_name='Nome'
    )
    last_name = models.CharField(
        max_length=30, 
        blank=True,  # ← MUDANÇA: agora opcional
        null=True,   # ← MUDANÇA: permite null no banco
        verbose_name='Sobrenome'
    )
    phone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,   # ← MUDANÇA: permite null no banco
        verbose_name='Telefone'
    )
    
    # CAMPOS ESPECÍFICOS PARA ÁREA MÉDICA (todos opcionais)
    crm = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,   # ← MUDANÇA: permite null no banco
        verbose_name='CRM'
    )
    especialidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,   # ← MUDANÇA: permite null no banco
        verbose_name='Especialidade'
    )
    is_medical_professional = models.BooleanField(
        default=False, 
        verbose_name='É Profissional de Saúde'
    )
    
    # Timestamps automáticos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    # Configurações de autenticação
    USERNAME_FIELD = 'email'  # Login será feito com email
    REQUIRED_FIELDS = ['username']  # ← MUDANÇA: removido first_name e last_name dos campos obrigatórios
    
    def __str__(self):
        """
        Representação string do usuário
        Se tiver nome completo, mostra nome + CRM (se houver)
        Senão, mostra username e email
        """
        if self.first_name and self.last_name:
            if self.crm:
                return f"Dr(a). {self.first_name} {self.last_name} - CRM: {self.crm}"
            return f"{self.first_name} {self.last_name} ({self.email})"
        return f"{self.username} ({self.email})"
    
    def get_full_name(self):
        """
        Retorna nome completo do usuário médico
        Se não tiver nome, retorna username
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username
    
    def get_short_name(self):
        """
        Retorna nome curto para exibição
        """
        return self.first_name or self.username
    
    def is_profile_complete(self):
        """
        Verifica se o perfil está completo
        Útil para sugerir ao usuário completar dados posteriormente
        """
        return bool(
            self.first_name and 
            self.last_name and 
            (self.crm if self.is_medical_professional else True)
        )
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'users'
        ordering = ['-created_at']