from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer SIMPLIFICADO para registro de usuários
    
    CAMPOS OBRIGATÓRIOS:
    - email (único)
    - username (único)
    - password (com validação)
    - password_confirm (confirmação)
    
    CAMPOS OPCIONAIS (removidos temporariamente):
    - first_name, last_name
    - crm, especialidade, phone
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = (
            'email', 
            'username', 
            'password', 
            'password_confirm'
        )
        # CAMPOS REMOVIDOS TEMPORARIAMENTE:
        # 'first_name', 'last_name', 'phone', 'crm', 'especialidade'
    
    def validate(self, attrs):
        """Validação geral dos dados"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem")
        return attrs
    
    def validate_email(self, value):
        """
        Validação de email único
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso")
        return value.lower()
    
    def validate_username(self, value):
        """
        Validação de username único
        Permite letras, números, underscore e hífen
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este username já está em uso")
        
        # Validação de formato (opcional)
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise serializers.ValidationError("Username deve conter apenas letras, números, _ ou -")
        
        return value
    
    def validate_password(self, value):
        """
        Validação de senha forte
        - Mínimo 8 caracteres
        - Pelo menos 1 letra maiúscula
        - Pelo menos 1 número
        """
        if len(value) < 8:
            raise serializers.ValidationError("Senha deve ter pelo menos 8 caracteres")
        
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Senha deve conter pelo menos uma letra maiúscula")
        
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Senha deve conter pelo menos um número")
        
        return value
    
    def create(self, validated_data):
        """
        Criação do usuário com dados mínimos
        """
        # Remove password_confirm dos dados
        validated_data.pop('password_confirm')
        
        # Cria usuário com dados básicos
        # Campos opcionais ficarão null/empty até serem preenchidos
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer para login simplificado
    Login feito com email e senha
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email').lower()
        password = attrs.get('password')
        
        if email and password:
            # Autentica usando email como username
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Email ou senha incorretos')
            if not user.is_active:
                raise serializers.ValidationError('Conta desativada. Entre em contato com o suporte.')
            attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para dados do usuário (usado no perfil/dashboard)
    Inclui todos os campos, mesmo os opcionais
    """
    full_name = serializers.SerializerMethodField()
    profile_complete = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 
            'email', 
            'username', 
            'first_name', 
            'last_name', 
            'full_name', 
            'phone', 
            'crm', 
            'especialidade', 
            'is_medical_professional', 
            'profile_complete',
            'created_at'
        )
        read_only_fields = ('id', 'created_at', 'full_name', 'profile_complete')
    
    def get_full_name(self, obj):
        """Retorna nome completo ou username se nome não estiver preenchido"""
        return obj.get_full_name()
    
    def get_profile_complete(self, obj):
        """Indica se o perfil está completo para sugerir preenchimento"""
        return obj.is_profile_complete()

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer OPCIONAL para atualização posterior do perfil
    Permite ao usuário completar dados médicos depois do cadastro
    """
    crm = serializers.CharField(required=False, allow_blank=True)
    especialidade = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = (
            'first_name', 
            'last_name', 
            'phone', 
            'crm', 
            'especialidade'
        )
    
    def validate_crm(self, value):
        """Validação de CRM apenas se fornecido"""
        if value:
            # Remove espaços e caracteres especiais
            crm_clean = re.sub(r'[^0-9A-Z]', '', value.upper())
            if len(crm_clean) < 4 or len(crm_clean) > 10:
                raise serializers.ValidationError("CRM deve ter entre 4 e 10 caracteres")
            
            # Verifica se CRM já existe (exceto o próprio usuário)
            if User.objects.filter(crm=crm_clean).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("Este CRM já está cadastrado")
            return crm_clean
        return value
    
    def update(self, instance, validated_data):
        """
        Atualiza perfil e marca como profissional médico se CRM fornecido
        """
        # Se CRM for fornecido, marca como profissional médico
        if validated_data.get('crm'):
            validated_data['is_medical_professional'] = True
        
        return super().update(instance, validated_data)