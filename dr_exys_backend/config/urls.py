# config/urls.py (URLs principais)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API v1 - Authentication (seu include existente - perfeito!)
    path('api/v1/auth/', include('apps.authentication.urls')),
    
    # ========================================
    # FUTURAS APIs (preparadas para expansão)
    # ========================================
    # Descomente conforme for criando os apps:
    
    # path('api/v1/users/', include('apps.users.urls')),
    # path('api/v1/medicos/', include('apps.medicos.urls')),
    # path('api/v1/produtos/', include('apps.produtos.urls')),
    # path('api/v1/financeiro/', include('apps.financeiro.urls')),
    # path('api/v1/ia-medica/', include('apps.ia_medica.urls')),
    # path('api/v1/ia-comercial/', include('apps.ia_comercial.urls')),
    # path('api/v1/whatsapp/', include('apps.whatsapp_integration.urls')),
    # path('api/v1/monitoring/', include('apps.monitoring.urls')),
]

# Servir arquivos estáticos em desenvolvimento (seu código existente - perfeito!)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Opcional: servir arquivos de media também
    if hasattr(settings, 'MEDIA_URL') and hasattr(settings, 'MEDIA_ROOT'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)