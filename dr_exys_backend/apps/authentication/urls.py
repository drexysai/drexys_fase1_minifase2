# apps/authentication/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Autenticação médica básica (seus URLs existentes - perfeitos!)
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    
    # Perfil do usuário médico (seus URLs existentes - perfeitos!)
    path('profile/', views.user_profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    
    # JWT tokens (seu URL existente - perfeito!)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Health check da API médica (seu URL existente - perfeito!)
    path('health/', views.health_check, name='health_check'),
    
    # ========================================
    # URLs EXTRAS (opcionais - recomendadas)
    # ========================================
    
    # Status de completude do perfil (útil para o frontend)
    path('profile/completion/', views.profile_completion_status, name='profile_completion'),
    
    # Marcar como profissional médico (útil para usuários que se registraram como comum)
    path('profile/mark-medical/', views.mark_as_medical_professional, name='mark_medical'),

]