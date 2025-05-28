from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.base_user import BaseUserManager


class CustomUserManager(BaseUserManager):
    """
    Manager customizado que permite criar usuários sem username obrigatório
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Cria e salva um usuário com email e senha
        """
        if not email:
            raise ValueError('O email é obrigatório')
        
        email = self.normalize_email(email)
        
        # Se não tiver username, usa a parte do email antes do @
        if not extra_fields.get('username'):
            username_base = email.split('@')[0]
            username = username_base
            counter = 1
            
            # Garante que o username seja único
            while User.objects.filter(username=username).exists():
                username = f"{username_base}{counter}"
                counter += 1
            
            extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Cria e salva um superusuário
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Modelo de usuário customizado para plataforma médica Dr. Exys
    
    CAMPOS OBRIGATÓRIOS:
    - email (único) - usado para login
    - password
    
    CAMPOS AUTOMÁTICOS:
    - username (gerado automaticamente a partir do email)
    
    CAMPOS OPCIONAIS:
    - first_name, last_name (podem ser preenchidos depois)
    - phone, crm, especialidade (campos médicos opcionais)
    """
    
    # CAMPOS ESSENCIAIS (obrigatórios)
    email = models.EmailField(
        unique=True, 
        verbose_name='Email',
        help_text='Email único para login na plataforma'
    )
    
    # Username será gerado automaticamente (não obrigatório no cadastro)
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Username',
        help_text='Gerado automaticamente a partir do email'
    )
    
    # CAMPOS PESSOAIS (opcionais - podem ser preenchidos posteriormente)
    first_name = models.CharField(
        max_length=30, 
        blank=True,
        null=True,
        verbose_name='Nome'
    )
    last_name = models.CharField(
        max_length=30, 
        blank=True,
        null=True,
        verbose_name='Sobrenome'
    )
    phone = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        verbose_name='Telefone'
    )
    
    # CAMPOS ESPECÍFICOS PARA ÁREA MÉDICA (todos opcionais)
    crm = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        verbose_name='CRM'
    )
    especialidade = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name='Especialidade'
    )
    is_medical_professional = models.BooleanField(
        default=False, 
        verbose_name='É Profissional de Saúde'
    )
    
    # Timestamps automáticos
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    # Manager customizado
    objects = CustomUserManager()
    
    # Configurações de autenticação - LOGIN COM EMAIL
    USERNAME_FIELD = 'email'  # ← Login será feito com email
    REQUIRED_FIELDS = []      # ← MUDANÇA: removido username dos campos obrigatórios
    
    def save(self, *args, **kwargs):
        """
        Override do save para garantir que username seja gerado automaticamente
        """
        if not self.username and self.email:
            username_base = self.email.split('@')[0]
            username = username_base
            counter = 1
            
            # Garante que o username seja único (excluindo o próprio objeto se estiver editando)
            while User.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{username_base}{counter}"
                counter += 1
            
            self.username = username
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        """
        Representação string do usuário
        Se tiver nome completo, mostra nome + CRM (se houver)
        Senão, mostra email
        """
        if self.first_name and self.last_name:
            if self.crm:
                return f"Dr(a). {self.first_name} {self.last_name} - CRM: {self.crm}"
            return f"{self.first_name} {self.last_name} ({self.email})"
        return self.email  # ← MUDANÇA: mostra email ao invés de username
    
    def get_full_name(self):
        """
        Retorna nome completo do usuário médico
        Se não tiver nome, retorna email
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.email  # ← MUDANÇA: retorna email ao invés de username
    
    def get_short_name(self):
        """
        Retorna nome curto para exibição
        """
        return self.first_name or self.email.split('@')[0]  # ← MUDANÇA: usa parte do email se não tiver nome
    
    def get_display_name(self):
        """
        Método para exibição amigável do nome
        """
        if self.first_name:
            return self.first_name
        return self.email.split('@')[0]
    
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
    
    def get_professional_title(self):
        """
        Retorna título profissional formatado
        """
        if self.is_medical_professional and self.crm:
            name = self.get_full_name()
            return f"Dr(a). {name} - CRM: {self.crm}"
        return self.get_full_name()
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'users'
        ordering = ['-created_at']