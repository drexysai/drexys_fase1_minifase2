from pathlib import Path
import os
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure--0f0y$n5t*@tt!ly$r07bi%s&lyjv1q_uc9rd&s!%541+3sho_')

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps para plataforma médica
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    
    # Local apps médicos - Dr. Exys
    'apps.users',
    'apps.authentication',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'dr_exys_db'),
        'USER': os.environ.get('POSTGRES_USER', 'dr_exys'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'dr_exys123'),
        'HOST': 'db',
        'PORT': '5432',
        'OPTIONS': {
            'options': '-c search_path=medicos,public'  # ← Mantido do original
        },
    }
}

# ========================================
# VALIDAÇÃO DE SENHAS PARA AUTH EMAIL-ONLY
# ========================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # ← AJUSTADO: Mínimo 8 caracteres
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'pt-br'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = '/app/staticfiles/'
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configurações CSRF para Docker + Nginx
CSRF_TRUSTED_ORIGINS = [
    'http://192.168.1.4:8081',
    'http://localhost:8081',
    'http://127.0.0.1:8081',
]

# Configurações adicionais para desenvolvimento
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = 'Lax'

# ============================================
# CONFIGURAÇÕES MÉDICAS DR. EXYS
# ============================================

# Modelo de usuário customizado para área médica - EMAIL LOGIN
AUTH_USER_MODEL = 'users.User'

# Configurações REST Framework para API médica
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # ← Mantido do original
    ],
    'DEFAULT_PARSER_CLASSES': [  # ← ADICIONADO: Para upload de arquivos médicos
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',  # ← ADICIONADO: Formato brasileiro
}

# Configurações JWT para autenticação médica segura - EMAIL LOGIN
SIMPLE_JWT = {
    # Duração dos tokens
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),     # ← AJUSTADO: 1 hora
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # ← Mantido: 7 dias
    
    # Configurações de segurança para email login
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    # Configurações do algoritmo
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    # Headers HTTP
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    
    # Claims JWT para email login
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    # Tipos de token
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    
    # Sliding tokens (opcional)
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Configurações específicas para área médica
MEDICAL_SETTINGS = {
    'REQUIRE_CRM_FOR_PROFESSIONALS': True,
    'AUTO_APPROVE_MEDICAL_PROFESSIONALS': False,
    'DEFAULT_USER_TYPE': 'regular',  # regular, medical
    # ========================================
    # NOVAS CONFIGURAÇÕES PARA EMAIL LOGIN
    # ========================================
    'EMAIL_ONLY_REGISTRATION': True,           # ← NOVO: Cadastro apenas com email
    'AUTO_GENERATE_USERNAME': True,            # ← NOVO: Username gerado automaticamente
    'ALLOW_PROFILE_COMPLETION': True,          # ← NOVO: Permite completar perfil depois
    'REQUIRE_EMAIL_VERIFICATION': False,       # ← NOVO: Não obriga verificação por email (pode ativar depois)
}

# ========================================
# LOGGING PARA AUTENTICAÇÃO EMAIL
# ========================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{asctime}] {levelname} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.authentication': {  # ← NOVO: Logs específicos da autenticação
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps.users': {  # ← NOVO: Logs específicos dos usuários
            'handlers': ['console', 'file'] if not DEBUG else ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Criar diretório de logs se não existir
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# ========================================
# CONFIGURAÇÕES DE EMAIL (FUTURO)
# ========================================
# Para quando implementar verificação de email ou reset de senha
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # Desenvolvimento
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Produção

# Configurações SMTP (descomente quando necessário)
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
# EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
# DEFAULT_FROM_EMAIL = 'Dr. Exys <noreply@drexys.com>'

# ========================================
# CONFIGURAÇÕES DE SEGURANÇA ADICIONAL
# ========================================
if not DEBUG:
    # Configurações de segurança para produção
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True