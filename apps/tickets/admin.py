from django.contrib import admin
from .models import SLAConfig, Ticket, TicketHistory, Comment, Attachment, Category, SubCategory, Application


@admin.register(SLAConfig)
class SLAConfigAdmin(admin.ModelAdmin):
    list_display = ['priority', 'response_time_minutes', 'resolution_time_minutes']
    ordering = ['priority']

    def has_delete_permission(self, request, obj=None):
        return False  # On ne supprime pas les configs SLA


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['type', 'name', 'is_active']
    list_filter = ['is_active']


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['category', 'name', 'is_active']
    list_filter = ['category', 'is_active']


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['name', 'code']


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ['user', 'action', 'field_name', 'old_value', 'new_value', 'created_at']


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'content', 'is_internal', 'created_at']


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['filename', 'file_size', 'uploaded_by', 'created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'number', 'title', 'category', 'priority', 'status',
        'created_by', 'assigned_to', 'sla_response_exceeded', 'resolved_out_of_sla', 'created_at'
    ]
    list_filter = ['status', 'priority', 'category', 'sla_response_exceeded', 'resolved_out_of_sla']
    search_fields = ['number', 'title', 'description']
    readonly_fields = ['number', 'created_at', 'updated_at', 'sla_response_deadline', 'sla_resolution_deadline']
    inlines = [TicketHistoryInline, CommentInline, AttachmentInline]
    date_hierarchy = 'created_at'
