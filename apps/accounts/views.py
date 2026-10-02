import base64
import json
import logging
import urllib.parse

import requests as http_requests

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import User, Department, AuditLog
from .forms import UserRegisterForm, UserProfileForm, UserAdminForm, DepartmentForm, ChooseDepartmentForm

logger = logging.getLogger(__name__)


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


def _jwt_payload(token):
    """Décode le payload d'un JWT sans vérifier la signature (usage diagnostic/login direct)."""
    try:
        part = token.split('.')[1]
        part += '=' * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part))
    except Exception:
        return {}


@require_http_methods(['POST'])
def keycloak_direct_login(request):
    """
    Connexion Keycloak sans redirection (Resource Owner Password Credentials).
    L'utilisateur saisit son identifiant/mot de passe Keycloak directement sur ITTIS.
    Django appelle le token endpoint Keycloak côté serveur et crée/met à jour le compte.
    Nécessite que "Direct Access Grants" soit activé sur le client Keycloak.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    username = request.POST.get('kc_username', '').strip()
    password = request.POST.get('kc_password', '').strip()

    if not username or not password:
        messages.error(request, "Identifiant et mot de passe Keycloak requis.")
        return redirect('account_login')

    token_ep = settings.OIDC_OP_TOKEN_ENDPOINT

    try:
        resp = http_requests.post(
            token_ep,
            data={
                'grant_type':    'password',
                'client_id':     settings.OIDC_RP_CLIENT_ID,
                'client_secret': settings.OIDC_RP_CLIENT_SECRET,
                'username':      username,
                'password':      password,
                'scope':         'openid email profile',
            },
            timeout=8,
        )
    except (http_requests.exceptions.ConnectionError, http_requests.exceptions.Timeout):
        messages.error(
            request,
            "Le serveur SSO est inaccessible. "
            "Utilisez la connexion par identifiant/mot de passe ou le code email ci-dessous."
        )
        return redirect('/accounts/login/?fallback=1')

    if resp.status_code == 200:
        token_data = resp.json()
        claims = _jwt_payload(token_data.get('access_token', ''))

        email      = claims.get('email', '')
        kc_username = claims.get('preferred_username', username)
        first_name = claims.get('given_name', '')
        last_name  = claims.get('family_name', '')

        # Trouver ou créer le compte (même logique que KeycloakOIDCBackend)
        user = User.objects.filter(username=kc_username).first()
        if not user and email:
            user = User.objects.filter(email__iexact=email).first()

        if not user:
            from .models import Department as Dept
            try:
                dept = Dept.objects.get(code='NO-DEPT')
            except Dept.DoesNotExist:
                dept = None
            user = User(
                username=kc_username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=User.ROLE_DEMANDEUR,
                department=dept,
            )
            user.set_unusable_password()
            user.save()
            logger.info("[KC DIRECT] Compte créé : %s (%s)", kc_username, email)
        else:
            changed = False
            for attr, val in [('first_name', first_name), ('last_name', last_name), ('email', email)]:
                if val and getattr(user, attr) != val:
                    setattr(user, attr, val)
                    changed = True
            if changed:
                user.save(update_fields=['first_name', 'last_name', 'email'])

        auth_login(request, user, backend='apps.accounts.oidc.KeycloakOIDCBackend')
        logger.info("[KC DIRECT] Connexion OK : %s", user.username)
        return redirect('dashboard:home')

    elif resp.status_code == 401:
        messages.error(request, "Identifiant ou mot de passe incorrect.")
        logger.warning("[KC DIRECT] Échec auth : %s (401)", username)
        return redirect('account_login')

    elif resp.status_code == 400:
        err = resp.json().get('error_description', resp.json().get('error', ''))
        if 'grant' in err.lower() or 'not allowed' in err.lower() or 'disabled' in err.lower():
            messages.error(
                request,
                "La connexion SSO directe n'est pas disponible. "
                "Utilisez la connexion par identifiant/mot de passe ou le code email."
            )
            return redirect('/accounts/login/?fallback=1')
        else:
            messages.error(request, f"Keycloak : {err}")
            logger.warning("[KC DIRECT] HTTP 400 pour %s : %s", username, err)
            return redirect('account_login')

    else:
        messages.error(request, f"Erreur Keycloak inattendue (HTTP {resp.status_code}).")
        logger.error("[KC DIRECT] HTTP %s pour %s", resp.status_code, username)
        return redirect('/accounts/login/?fallback=1')


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
