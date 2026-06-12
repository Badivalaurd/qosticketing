from django.urls import path
from . import views
from . import registration_views

app_name = 'accounts'

urlpatterns = [
    # ── Inscription ─────────────────────────────────────────────────────────
    path('register/', registration_views.register, name='register'),
    path('verify-email/', registration_views.verify_email, name='verify_email'),
    path('resend-code/', registration_views.resend_code, name='resend_code'),

    # ── Réinitialisation MDP par code 8 caractères ──────────────────────────
    path('password/reset/verify/', registration_views.password_reset_verify, name='password_reset_verify'),
    path('password/reset/resend/', registration_views.password_reset_resend, name='password_reset_resend'),
    path('password/reset/change/', registration_views.password_reset_change, name='password_reset_change'),

    # ── Admin — upload employés autorisés ────────────────────────────────────
    path('admin/upload-employees/', registration_views.upload_employees, name='upload_employees'),

    # ── Gestion utilisateurs ─────────────────────────────────────────────────
    path('profile/', views.profile_view, name='profile'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/new/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_update'),
    path('departments/', views.DepartmentListView.as_view(), name='department_list'),
    path('departments/new/', views.DepartmentCreateView.as_view(), name='department_create'),
    path('departments/<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='department_update'),
    path('audit/', views.AuditLogListView.as_view(), name='audit_log'),
]
