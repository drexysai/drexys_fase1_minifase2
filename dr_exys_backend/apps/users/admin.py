from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Configuração do admin para usuários médicos da plataforma Dr. Exys
    """
    list_display = (
        'email', 
        'first_name', 
        'last_name', 
        'crm',
        'especialidade',
        'is_medical_professional',
        'is_staff', 
        'created_at'
    )
    
    list_filter = (
        'is_staff', 
        'is_superuser', 
        'is_medical_professional',
        'especialidade',
        'created_at'
    )
    
    search_fields = (
        'email', 
        'first_name', 
        'last_name', 
        'crm',
        'especialidade'
    )
    
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Médicas', {
            'fields': (
                'crm', 
                'especialidade', 
                'is_medical_professional'
            )
        }),
        ('Informações Adicionais', {
            'fields': (
                'phone', 
                'created_at', 
                'updated_at'
            )
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    # Ações personalizadas para usuários médicos
    actions = ['mark_as_medical_professional', 'mark_as_regular_user']
    
    def mark_as_medical_professional(self, request, queryset):
        queryset.update(is_medical_professional=True)
        self.message_user(request, "Usuários marcados como profissionais de saúde.")
    mark_as_medical_professional.short_description = "Marcar como profissional de saúde"
    
    def mark_as_regular_user(self, request, queryset):
        queryset.update(is_medical_professional=False)
        self.message_user(request, "Usuários marcados como usuários comuns.")
    mark_as_regular_user.short_description = "Marcar como usuário comum"