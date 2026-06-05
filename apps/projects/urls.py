from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='list'),
    path('new/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='update'),
    path('<int:pk>/kanban/', views.kanban_board, name='kanban'),
    path('<int:pk>/gantt/', views.gantt_view, name='gantt'),
    path('<int:project_pk>/sprints/<int:sprint_pk>/', views.sprint_detail, name='sprint_detail'),
    path('<int:project_pk>/stories/<int:story_pk>/', views.story_detail, name='story_detail'),
    path('stories/<int:pk>/status/', views.update_story_status, name='update_story_status'),
]
