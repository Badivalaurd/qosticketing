from django.contrib import admin
from .models import Project, Sprint, Epic, UserStory, Task


class SprintInline(admin.TabularInline):
    model = Sprint
    extra = 0


class EpicInline(admin.TabularInline):
    model = Epic
    extra = 0


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'status', 'manager', 'start_date', 'end_date']
    list_filter = ['status', 'department']
    search_fields = ['name', 'code']
    inlines = [SprintInline, EpicInline]
    filter_horizontal = ['team']


@admin.register(UserStory)
class UserStoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'sprint', 'status', 'assignee', 'story_points']
    list_filter = ['status', 'project', 'sprint']
    search_fields = ['title']
