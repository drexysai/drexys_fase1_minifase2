from rest_framework import serializers
from django.contrib.auth import authenticate
from apps.users.models import User
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de usuários na plataforma médica Dr. Exys
    Inclui validações específicas para profissionais de saúde
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    crm = serializers.CharField(required=False, allow_blank=True)
    especialidade = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 
            'phone', 'crm', 'especialidade', 
            'password', 'password_confirm'
        )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email já está em uso na plataforma médica")
        return value.lower()
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este username já está em uso")
        return value
    
    def validate_crm(self, value):
        """Validação básica de CRM"""
        if value:
            # Remove espaços e caracteres especiais
            crm_clean = re.sub(r'[^0-9A-Z]', '', value.upper())
            if len(crm_clean) < 4 or len(crm_clean) > 10:
                raise serializers.ValidationError("CRM deve ter entre 4 e 10 caracteres")
            # Verificar se CRM já existe
            if User.objects.filter(crm=crm_clean).exists():
                raise serializers.ValidationError("Este CRM já está cadastrado")
            return crm_clean
        return value
    
    def validate_password(self, value):
        """Validação de senha forte para área médica"""
        if len(value) < 8:
            raise serializers.ValidationError("Senha deve ter pelo menos 8 caracteres")
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Senha deve conter pelo menos uma letra maiúscula")
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Senha deve conter pelo menos um número")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        
        # Determinar se é profissional de saúde
        is_medical = bool(validated_data.get('crm'))
        validated_data['is_medical_professional'] = is_medical
        
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer para login na plataforma médica Dr. Exys
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email').lower()
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Email ou senha incorretos para acesso médico')
            if not user.is_active:
                raise serializers.ValidationError('Conta médica desativada. Entre em contato com o suporte.')
            attrs['user'] = user
        return attrs

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para dados do usuário médico
    """
    full_name = serializers.SerializerMethodField()
    user_type = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 
            'full_name', 'phone', 'crm', 'especialidade', 
            'is_medical_professional', 'user_type', 'created_at'
        )
        read_only_fields = ('id', 'created_at', 'full_name', 'user_type')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_user_type(self, obj):
        return 'medical' if obj.is_medical_professional else 'regular'