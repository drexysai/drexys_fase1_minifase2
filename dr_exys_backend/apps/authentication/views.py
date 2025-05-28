from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash
from .serializers import (
    UserRegistrationSerializer, 
    UserLoginSerializer, 
    UserSerializer,
    UserRegistrationResponseSerializer,
    UserProfileUpdateSerializer
)
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Endpoint para registro de novos usuários na plataforma médica Dr. Exys
    
    CAMPOS OBRIGATÓRIOS:
    - email (único)
    - password
    - password_confirm
    
    CAMPOS AUTOMÁTICOS:
    - username (gerado automaticamente a partir do email)
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        # Log do registro com informações básicas
        logger.info(f"Novo usuário registrado: {user.email} (username: {user.username})")
        
        # Mensagem personalizada baseada no que temos disponível
        welcome_name = user.get_display_name()  # Retorna nome ou parte do email
        
        return Response({
            'success': True,
            'message': f"Bem-vindo(a) à plataforma médica Dr. Exys, {welcome_name}!",
            'user': UserRegistrationResponseSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'next_steps': {
                'complete_profile': not user.is_profile_complete(),
                'profile_url': '/api/v1/auth/profile/update/',
                'message': 'Complete seu perfil para ter acesso total aos recursos médicos.'
            }
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'message': 'Erro no cadastro médico',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Endpoint para login na plataforma médica Dr. Exys
    
    CAMPOS OBRIGATÓRIOS:
    - email
    - password
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        # Atualizar last_login automaticamente
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log do login
        logger.info(f"Login realizado: {user.email}")
        
        # Mensagem personalizada baseada no que temos disponível
        welcome_name = user.get_display_name()
        
        return Response({
            'success': True,
            'message': f"Bem-vindo(a) de volta, {welcome_name}!",
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'profile_status': {
                'complete': user.is_profile_complete(),
                'needs_completion': not user.is_profile_complete(),
                'professional': user.is_medical_professional
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Erro no login médico',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Endpoint para obter dados completos do usuário médico logado
    """
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'user': serializer.data,
        'profile_status': {
            'complete': request.user.is_profile_complete(),
            'professional': request.user.is_medical_professional,
            'display_name': request.user.get_display_name(),
            'professional_title': request.user.get_professional_title()
        }
    }, status=status.HTTP_200_OK)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Endpoint para atualizar perfil do usuário médico
    Permite completar dados após o cadastro inicial
    """
    serializer = UserProfileUpdateSerializer(
        request.user, 
        data=request.data, 
        partial=request.method == 'PATCH'
    )
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Log da atualização
        logger.info(f"Perfil atualizado: {user.email}")
        
        return Response({
            'success': True,
            'message': 'Perfil médico atualizado com sucesso',
            'user': UserSerializer(user).data,
            'profile_status': {
                'complete': user.is_profile_complete(),
                'professional': user.is_medical_professional
            }
        }, status=status.HTTP_200_OK)
    
    return Response({
        'success': False,
        'message': 'Erro na atualização do perfil',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Endpoint para logout seguro da plataforma médica
    """
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        logger.info(f"Logout realizado: {request.user.email}")
        
        return Response({
            'success': True,
            'message': 'Logout da plataforma médica realizado com sucesso'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Erro no logout: {str(e)}")
        return Response({
            'success': False,
            'message': 'Erro no logout médico',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint para verificar saúde da API médica
    """
    from django.db import connection
    
    try:
        # Testa conexão com banco
        connection.ensure_connection()
        db_status = 'connected'
    except Exception:
        db_status = 'disconnected'
    
    return Response({
        'status': 'healthy',
        'service': 'Dr. Exys Medical API',
        'version': '1.0.0',
        'database': db_status,
        'authentication': 'email_only',  # Indica que usa apenas email
        'features': {
            'jwt_auth': True,
            'profile_completion': True,
            'medical_professional_support': True
        }
    }, status=status.HTTP_200_OK)

# ==========================================
# VIEWS EXTRAS: Para completar funcionalidades
# ==========================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_completion_status(request):
    """
    Endpoint específico para verificar status de completude do perfil
    Útil para mostrar sugestões no frontend
    """
    user = request.user
    
    missing_fields = []
    if not user.first_name:
        missing_fields.append('first_name')
    if not user.last_name:
        missing_fields.append('last_name')
    if user.is_medical_professional and not user.crm:
        missing_fields.append('crm')
    if user.is_medical_professional and not user.especialidade:
        missing_fields.append('especialidade')
    
    return Response({
        'success': True,
        'profile_complete': user.is_profile_complete(),
        'completion_percentage': max(0, 100 - (len(missing_fields) * 25)),
        'missing_fields': missing_fields,
        'suggestions': {
            'add_name': not user.first_name or not user.last_name,
            'add_medical_info': user.is_medical_professional and (not user.crm or not user.especialidade),
            'add_contact': not user.phone
        }
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_as_medical_professional(request):
    """
    Endpoint para marcar usuário como profissional médico
    """
    user = request.user
    user.is_medical_professional = True
    user.save(update_fields=['is_medical_professional'])
    
    logger.info(f"Usuário marcado como profissional médico: {user.email}")
    
    return Response({
        'success': True,
        'message': 'Usuário marcado como profissional de saúde',
        'user': UserSerializer(user).data
    }, status=status.HTTP_200_OK)
