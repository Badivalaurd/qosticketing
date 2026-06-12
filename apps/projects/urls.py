from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Projects
    path('', views.ProjectListView.as_view(), name='list'),
    path('new/', views.ProjectCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='detail'),
    path('<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='update'),
    path('<int:pk>/kanban/', views.kanban_board, name='kanban'),
    path('<int:pk>/gantt/', views.gantt_view, name='gantt'),
    path('<int:pk>/backlog/', views.backlog_view, name='backlog'),

    # Sprints
    path('<int:project_pk>/sprints/new/', views.sprint_create, name='sprint_create'),
    path('<int:project_pk>/sprints/<int:sprint_pk>/', views.sprint_detail, name='sprint_detail'),
    path('<int:project_pk>/sprints/<int:sprint_pk>/edit/', views.sprint_update, name='sprint_update'),
    path('<int:project_pk>/sprints/<int:sprint_pk>/start/', views.sprint_start, name='sprint_start'),
    path('<int:project_pk>/sprints/<int:sprint_pk>/complete/', views.sprint_complete, name='sprint_complete'),
    path('<int:project_pk>/sprints/<int:sprint_pk>/delete/', views.sprint_delete, name='sprint_delete'),

    # Epics
    path('<int:project_pk>/epics/new/', views.epic_create, name='epic_create'),
    path('<int:project_pk>/epics/<int:epic_pk>/edit/', views.epic_update, name='epic_update'),
    path('<int:project_pk>/epics/<int:epic_pk>/delete/', views.epic_delete, name='epic_delete'),

    # User Stories
    path('<int:project_pk>/stories/new/', views.story_create, name='story_create'),
    path('<int:project_pk>/stories/<int:story_pk>/', views.story_detail, name='story_detail'),
    path('<int:project_pk>/stories/<int:story_pk>/edit/', views.story_update, name='story_update'),
    path('<int:project_pk>/stories/<int:story_pk>/delete/', views.story_delete, name='story_delete'),
    path('<int:project_pk>/stories/<int:story_pk>/comment/', views.story_comment_add, name='story_comment_add'),
    path('<int:project_pk>/stories/<int:story_pk>/move/', views.story_move_sprint, name='story_move_sprint'),

    # AJAX story status
    path('stories/<int:pk>/status/', views.update_story_status, name='update_story_status'),

    # Tasks
    path('<int:project_pk>/tasks/<int:task_pk>/edit/', views.task_update, name='task_update'),
    path('<int:project_pk>/tasks/<int:task_pk>/delete/', views.task_delete, name='task_delete'),
    path('tasks/<int:pk>/status/', views.update_task_status, name='update_task_status'),

    # Livrables
    path('<int:project_pk>/deliverables/new/', views.deliverable_create, name='deliverable_create'),
    path('<int:project_pk>/deliverables/<int:deliverable_pk>/edit/', views.deliverable_update, name='deliverable_update'),
]
