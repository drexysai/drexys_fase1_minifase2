from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    """Endpoint raiz da API médica Dr. Exys"""
    return JsonResponse({
        'message': 'Bem-vindo à API médica Dr. Exys',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/v1/auth/',
            'docs': '/admin/',
            'health': '/api/v1/auth/health/'
        }
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', api_root, name='api_root'),
    path('api/v1/auth/', include('apps.authentication.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)