"""
Vues d'inscription spécifiques au mode desktop.

Flux complet :
  1. GET  /accounts/register/        → Formulaire (CUID + email @orange.com + MDP)
  2. POST /accounts/register/        → Valider CUID, envoyer email de confirmation
  3. GET  /accounts/confirm/<token>/ → Activer le compte, mettre en cache local
  4. POST /accounts/password-reset/  → Email de réinit (ou ticket secret si email impossible)
  5. POST /accounts/set-temp-password/<uid>/  → Admin fixe un MDP temporaire
  6. POST /accounts/change-temp-password/    → Utilisateur change son MDP temporaire
"""
import logging
import secrets

from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.http import require_http_methods

from apps.accounts.models import ApprovedCUID

logger = logging.getLogger(__name__)
User = get_user_model()

# Durée de validité du token de confirmation email (en heures)
EMAIL_CONFIRM_TOKEN_HOURS = 24


def register(request):
    """
    Étape 1 : inscription avec CUID et email @orange.com.
    """
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    context = {'errors': [], 'form_data': {}}

    if request.method == 'POST':
        data = request.POST
        cuid = data.get('cuid', '').strip().upper()
        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        password = data.get('password', '')
        password2 = data.get('password2', '')

        context['form_data'] = {
            'cuid': cuid, 'email': email,
            'first_name': first_name, 'last_name': last_name,
        }

        errors = _validate_registration(cuid, email, first_name, last_name, password, password2)

        if not errors:
            # Créer le compte (inactif) et envoyer l'email de confirmation
            user, token = _create_pending_user(
                cuid=cuid, email=email,
                first_name=first_name, last_name=last_name,
                password=password,
            )
            _send_confirmation_email(user, token, request)

            # Marquer le CUID comme inscrit
            ApprovedCUID.objects.filter(cuid=cuid).update(
                is_registered=True, registered_user=user
            )

            return render(request, 'accounts/register_pending.html', {
                'email': email,
            })

        context['errors'] = errors

    return render(request, 'accounts/register.html', context)


def confirm_email(request, token: str):
    """
    Étape 2 : activation du compte via le lien reçu par email.
    """
    try:
        user = User.objects.get(
            email_confirm_token=token,
            is_active=False,
        )
    except User.DoesNotExist:
        messages.error(request, "Lien de confirmation invalide ou expiré.")
        return redirect('account_login')

    # Vérifier l'expiration (24h)
    if user.email_confirm_sent_at:
        delta = timezone.now() - user.email_confirm_sent_at
        if delta.total_seconds() > EMAIL_CONFIRM_TOKEN_HOURS * 3600:
            messages.error(request, "Ce lien a expiré. Contactez l'administrateur.")
            return redirect('account_login')

    user.is_active = True
    user.email_confirm_token = ''
    user.save()

    messages.success(request, "Votre compte est activé. Vous pouvez maintenant vous connecter.")
    return redirect('account_login')


@require_http_methods(['GET', 'POST'])
def password_reset_request(request):
    """
    Réinitialisation de mot de passe :
    - Si email @orange.com → envoi email classique
    - Si email impossible → proposer de créer un ticket secret
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        try:
            user = User.objects.get(email=email, is_active=True)
            success = _send_password_reset_email(user, request)
            if success:
                return render(request, 'accounts/password_reset_sent.html', {'email': email})
            else:
                # Proposer le ticket secret
                return render(request, 'accounts/password_reset_ticket.html', {
                    'email': email,
                    'user_id': user.pk,
                })
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe
            return render(request, 'accounts/password_reset_sent.html', {'email': email})

    return render(request, 'accounts/password_reset_form.html')


@require_http_methods(['POST'])
def password_reset_secret_ticket(request):
    """
    Crée un ticket secret pour demande de réinitialisation de mot de passe.
    """
    user_id = request.POST.get('user_id')
    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur introuvable.")
        return redirect('account_login')

    from apps.tickets.models import Ticket, Category
    # Catégorie système pour les tickets secrets (créée à l'init)
    cat = Category.objects.filter(name='Accès et authentification').first()

    ticket = Ticket(
        title=f"Réinitialisation mot de passe — {user.get_full_name() or user.username}",
        description=(
            f"L'utilisateur {user.username} ({user.email}) n'a pas pu recevoir l'email de "
            f"réinitialisation. Veuillez lui attribuer un mot de passe temporaire."
        ),
        priority=Ticket.PRIORITY_P1,
        created_by=user,
        department=user.department,
        category=cat,
        is_secret=True,
    )
    ticket.save()

    return render(request, 'accounts/password_reset_secret_submitted.html', {
        'ticket_number': ticket.number,
    })


@login_required
@require_http_methods(['POST'])
def admin_set_temp_password(request, user_id: int):
    """
    Admin fixe un mot de passe temporaire pour un utilisateur (via ticket secret).
    """
    if not request.user.is_admin:
        messages.error(request, "Action non autorisée.")
        return redirect('tickets:list')

    target_user = get_object_or_404(User, pk=user_id)
    temp_password = request.POST.get('temp_password', '').strip()
    if len(temp_password) < 8:
        messages.error(request, "Le mot de passe temporaire doit contenir au moins 8 caractères.")
        return redirect(request.META.get('HTTP_REFERER', 'tickets:list'))

    target_user.set_password(temp_password)
    # Marquer le MDP comme temporaire (via le credential local si possible)
    target_user.save()

    # Mettre à jour le flag dans le cache local
    try:
        from apps.local_auth.models import LocalCredential
        cred = LocalCredential.objects.using('auth_local').get(pg_user_id=target_user.pk)
        cred.set_password(temp_password)
        cred.is_temporary_password = True
        cred.save(using='auth_local')
    except Exception:
        pass

    messages.success(request, f"Mot de passe temporaire fixé pour {target_user.username}.")
    return redirect(request.META.get('HTTP_REFERER', 'tickets:list'))


@login_required
@require_http_methods(['GET', 'POST'])
def change_temp_password(request):
    """
    Forçage du changement de mot de passe temporaire dès la connexion.
    """
    # Vérifier si l'utilisateur a un MDP temporaire
    try:
        from apps.local_auth.models import LocalCredential
        cred = LocalCredential.objects.using('auth_local').get(pg_user_id=request.user.pk)
        if not cred.is_temporary_password:
            return redirect('dashboard:home')
    except Exception:
        return redirect('dashboard:home')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        new_password2 = request.POST.get('new_password2', '')

        if len(new_password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
        elif new_password != new_password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            # Mettre à jour le cache local
            cred.set_password(new_password)
            cred.is_temporary_password = False
            cred.save(using='auth_local')
            messages.success(request, "Mot de passe mis à jour avec succès.")
            login(request, request.user, backend='apps.accounts.backends.HybridAuthBackend')
            return redirect('dashboard:home')

    return render(request, 'accounts/change_temp_password.html')


# ──────────────────────────────────────────────────────────────────────────────
# Helpers privés
# ──────────────────────────────────────────────────────────────────────────────

def _validate_registration(cuid, email, first_name, last_name, password, password2):
    errors = []
    allowed_domain = getattr(settings, 'ALLOWED_EMAIL_DOMAIN', '@orange.com')

    if not cuid:
        errors.append("Le CUID est obligatoire.")
    else:
        if not ApprovedCUID.objects.filter(cuid=cuid, is_registered=False).exists():
            if ApprovedCUID.objects.filter(cuid=cuid, is_registered=True).exists():
                errors.append("Ce CUID est déjà associé à un compte. Connectez-vous directement.")
            else:
                errors.append("Ce CUID n'est pas dans la liste des utilisateurs autorisés.")

    if not email:
        errors.append("L'adresse email est obligatoire.")
    elif not email.endswith(allowed_domain):
        errors.append(f"Seules les adresses {allowed_domain} sont acceptées.")
    elif User.objects.filter(email=email).exists():
        errors.append("Cette adresse email est déjà utilisée.")

    if not first_name:
        errors.append("Le prénom est obligatoire.")
    if not last_name:
        errors.append("Le nom est obligatoire.")
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères.")
    if password != password2:
        errors.append("Les mots de passe ne correspondent pas.")

    return errors


def _create_pending_user(cuid, email, first_name, last_name, password):
    token = secrets.token_urlsafe(32)
    user = User(
        username=cuid,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=False,  # Actif uniquement après confirmation email
        role=User.ROLE_DEMANDEUR,
        email_confirm_token=token,
        email_confirm_sent_at=timezone.now(),
    )
    user.set_password(password)
    user.save()
    return user, token


def _send_confirmation_email(user, token, request):
    confirm_url = request.build_absolute_uri(
        reverse('accounts:confirm_email', args=[token])
    )
    try:
        send_mail(
            subject='QoS Ticketing — Confirmez votre adresse email',
            message=(
                f"Bonjour {user.first_name},\n\n"
                f"Cliquez sur ce lien pour activer votre compte QoS Ticketing :\n\n"
                f"{confirm_url}\n\n"
                f"Ce lien est valable {EMAIL_CONFIRM_TOKEN_HOURS} heures.\n\n"
                f"Si vous n'êtes pas à l'origine de cette inscription, ignorez ce message."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.error("Impossible d'envoyer l'email de confirmation à %s : %s", user.email, exc)
        return False


def _send_password_reset_email(user, request):
    token = secrets.token_urlsafe(32)
    reset_url = request.build_absolute_uri(
        reverse('accounts:password_reset_confirm', args=[token])
    )
    # Stocker le token temporairement (on réutilise le champ email_confirm_token)
    user.email_confirm_token = token
    user.email_confirm_sent_at = timezone.now()
    user.save(update_fields=['email_confirm_token', 'email_confirm_sent_at'])

    try:
        send_mail(
            subject='QoS Ticketing — Réinitialisation de mot de passe',
            message=(
                f"Bonjour {user.first_name},\n\n"
                f"Cliquez sur ce lien pour réinitialiser votre mot de passe :\n\n"
                f"{reset_url}\n\n"
                f"Ce lien est valable {EMAIL_CONFIRM_TOKEN_HOURS} heures."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as exc:
        logger.error("Impossible d'envoyer l'email de réinitialisation à %s : %s", user.email, exc)
        return False
