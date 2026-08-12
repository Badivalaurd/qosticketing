import urllib.parse

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import User, Department, AuditLog
from .forms import UserRegisterForm, UserProfileForm, UserAdminForm, DepartmentForm, ChooseDepartmentForm


@require_http_methods(['GET', 'POST'])
def sso_logout(request):
    """
    Déconnexion unifiée :
    - SSO (Keycloak) : redirige vers l'endpoint logout Keycloak pour invalider la session SSO
    - Comptes locaux : déconnexion Django classique
    """
    id_token = request.session.get('oidc_id_token')
    logout(request)  # vide la session Django dans tous les cas

    if id_token:
        redirect_uri = request.build_absolute_uri(settings.LOGOUT_REDIRECT_URL or '/accounts/login/')
        params = urllib.parse.urlencode({
            'id_token_hint': id_token,
            'post_logout_redirect_uri': redirect_uri,
            'redirect_uri': redirect_uri,  # compat Keycloak < 18
        })
        return redirect(f"{settings.OIDC_OP_LOGOUT_ENDPOINT}?{params}")

    return redirect(settings.LOGOUT_REDIRECT_URL or '/accounts/login/')


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == User.ROLE_ADMIN


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in [User.ROLE_ADMIN, User.ROLE_MANAGER]


@login_required
def choose_department(request):
    """
    Permet à l'utilisateur de choisir son département à la première connexion.
    - Accessible seulement si `user.department` est None.
    - Une fois le département défini (par l'utilisateur ou un admin/agent),
      la page redirige immédiatement vers le dashboard → l'utilisateur ne peut plus modifier.
    - Seuls les départements non-informatiques sont proposés.
    """
    user = request.user

    # Déjà affecté à un département → redirection immédiate
    if user.department_id is not None:
        return redirect(request.GET.get('next') or 'dashboard:home')

    if request.method == 'POST':
        form = ChooseDepartmentForm(request.POST)
        if form.is_valid():
            user.department = form.cleaned_data['department']
            user.save(update_fields=['department'])
            messages.success(
                request,
                f"Bienvenue ! Votre département « {user.department.name} » a été enregistré."
            )
            return redirect(request.GET.get('next') or 'dashboard:home')
    else:
        form = ChooseDepartmentForm()

    return render(request, 'accounts/choose_department.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil mis à jour avec succès.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.select_related('department').order_by('last_name', 'first_name')
        role = self.request.GET.get('role')
        dept = self.request.GET.get('department')
        search = self.request.GET.get('search')
        if role:
            qs = qs.filter(role=role)
        if dept:
            qs = qs.filter(department_id=dept)
        if search:
            qs = qs.filter(username__icontains=search) | qs.filter(email__icontains=search) | \
                 qs.filter(first_name__icontains=search) | qs.filter(last_name__icontains=search)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['departments'] = Department.objects.filter(is_active=True)
        ctx['roles'] = User.ROLE_CHOICES
        return ctx


class UserCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = UserAdminForm
    template_name = 'accounts/user_form.html'
    context_object_name = 'edited_user'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur créé avec succès.')
        return super().form_valid(form)


class UserUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserAdminForm
    template_name = 'accounts/user_form.html'
    context_object_name = 'edited_user'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur mis à jour.')
        return super().form_valid(form)


class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'profile_user'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tickets_created'] = self.object.created_tickets.count()
        ctx['tickets_assigned'] = self.object.assigned_tickets.count()
        return ctx


class DepartmentListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = Department
    template_name = 'accounts/department_list.html'
    context_object_name = 'departments'
    paginate_by = 20


class DepartmentCreateView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'accounts/department_form.html'
    success_url = reverse_lazy('accounts:department_list')

    def form_valid(self, form):
        messages.success(self.request, 'Direction créée avec succès.')
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'accounts/department_form.html'
    success_url = reverse_lazy('accounts:department_list')


class AuditLogListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = AuditLog
    template_name = 'accounts/audit_log.html'
    context_object_name = 'logs'
    paginate_by = 50

    def get_queryset(self):
        return AuditLog.objects.select_related('user').order_by('-created_at')
