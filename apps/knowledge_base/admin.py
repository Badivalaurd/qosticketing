from django.contrib import admin
from .models import KBCategory, Article


@admin.register(KBCategory)
class KBCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'order']
    ordering = ['order']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'type', 'author', 'views', 'is_published', 'created_at']
    list_filter = ['type', 'category', 'is_published']
    search_fields = ['title', 'content', 'tags']
    filter_horizontal = ['related_tickets']
