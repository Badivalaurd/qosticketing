from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Department, AuditLog


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent', 'is_it_department', 'ticketing_enabled', 'manager', 'is_active']
    list_filter = ['is_active', 'is_it_department', 'ticketing_enabled']
    search_fields = ['name', 'code']
    fieldsets = [
        (None, {'fields': ['name', 'code', 'description', 'parent', 'is_active']}),
        ('Département Informatique', {'fields': ['is_it_department']}),
        ('Activation Ticketing (autres départements)', {
            'fields': ['ticketing_enabled', 'manager'],
            'description': (
                'Activez uniquement après accord contractuel signé. '
                'Le manager choisi sera responsable de la distribution des tickets dans ce département. '
                'Un seul manager par département. Seul l\'admin peut modifier ces champs.'
            ),
        }),
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'get_full_name', 'role', 'department', 'is_active']
    list_filter = ['role', 'department', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'department', 'phone', 'avatar', 'bio')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {'fields': ('role', 'department', 'phone')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'ip_address', 'created_at']
    list_filter = ['action', 'model_name']
    search_fields = ['user__username', 'object_repr', 'details']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'details', 'ip_address', 'created_at']
    ordering = ['-created_at']
