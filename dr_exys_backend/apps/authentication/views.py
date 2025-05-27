from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import update_session_auth_hash
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserSerializer
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Endpoint para registro de novos usuários na plataforma médica Dr. Exys
    Suporte para profissionais de saúde e usuários comuns
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        
        # Log do registro
        user_type = 'profissional de saúde' if user.is_medical_professional else 'usuário comum'
        logger.info(f"Novo {user_type} registrado: {user.email}")
        
        return Response({
            'success': True,
            'message': f"Bem-vindo(a) à plataforma médica Dr. Exys, {user.first_name}!",
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
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
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        
        # Atualizar last_login
        user.save(update_fields=['last_login'])
        
        # Log do login
        logger.info(f"Login realizado: {user.email}")
        
        return Response({
            'success': True,
            'message': f"Bem-vindo(a) de volta, {user.first_name}!",
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
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
    Endpoint para obter dados do usuário médico logado
    """
    serializer = UserSerializer(request.user)
    return Response({
        'success': True,
        'user': serializer.data
    }, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    Endpoint para atualizar perfil do usuário médico
    """
    user = request.user
    allowed_fields = ['first_name', 'last_name', 'phone', 'especialidade']
    
    for field in allowed_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
    
    user.save()
    
    return Response({
        'success': True,
        'message': 'Perfil médico atualizado com sucesso',
        'user': UserSerializer(user).data
    }, status=status.HTTP_200_OK)

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
            'message': 'Erro no logout médico'
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Endpoint para verificar saúde da API médica
    """
    return Response({
        'status': 'healthy',
        'service': 'Dr. Exys Medical API',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)