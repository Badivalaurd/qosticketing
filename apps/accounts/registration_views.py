"""
Inscription et gestion des employés autorisés (branch develop — version web).

Flux inscription :
  1. GET  /accounts/register/        → Formulaire CUID + email @orange.com + nom + MDP
  2. POST /accounts/register/        → Valider, générer code 8 car., envoyer email
  3. GET  /accounts/verify-email/    → Saisie du code avec chrono 5 min
  4. POST /accounts/verify-email/    → Vérifier code → activer compte
  5. POST /accounts/resend-code/     → Renvoyer un nouveau code

Admin :
  GET/POST /accounts/admin/upload-employees/ → Upload Excel (CUID / Statut / Département)
"""
import io
import logging
import secrets

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.conf import settings
from django.views.decorators.http import require_http_methods

from apps.accounts.models import AuthorizedEmployee, Department

logger = logging.getLogger(__name__)
User = get_user_model()

CODE_EXPIRY_MINUTES = 5
ALLOWED_DOMAIN = '@orange.com'
CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'  # sans 0/O, 1/I/L pour éviter confusion


# ──────────────────────────────────────────────────────────────────────────────
# ADMIN — Upload fichier Excel des employés autorisés
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def upload_employees(request):
    """
    Upload d'un fichier Excel (.xlsx) contenant les CUIDs autorisés.
    Colonnes attendues (ligne 1 = en-têtes) :
      A : CUID
      B : Statut (permanent / interimaire / stagiaire / temporaire)
      C : Département (nom exact ou approximatif)
    """
    if not request.user.is_admin:
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('dashboard:home')

    context = {'results': None}

    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Format non supporté. Utilisez un fichier .xlsx")
            return render(request, 'accounts/upload_employees.html', context)

        try:
            results = _parse_and_import_excel(excel_file, request.user)
            context['results'] = results
            messages.success(
                request,
                f"{results['created']} créé(s), {results['updated']} mis à jour, "
                f"{results['skipped']} ignoré(s)."
            )
        except Exception as exc:
            logger.exception("Erreur import Excel : %s", exc)
            messages.error(request, f"Erreur lors de l'import : {exc}")

    return render(request, 'accounts/upload_employees.html', context)


def _parse_and_import_excel(file_obj, admin_user):
    import openpyxl

    wb = openpyxl.load_workbook(filename=io.BytesIO(file_obj.read()), read_only=True)
    ws = wb.active

    status_map = {
        'permanent': AuthorizedEmployee.STATUS_PERMANENT,
        'permanente': AuthorizedEmployee.STATUS_PERMANENT,
        'interimaire': AuthorizedEmployee.STATUS_INTERIMAIRE,
        'intérimaire': AuthorizedEmployee.STATUS_INTERIMAIRE,
        'interim': AuthorizedEmployee.STATUS_INTERIMAIRE,
        'intérim': AuthorizedEmployee.STATUS_INTERIMAIRE,
        'stagiaire': AuthorizedEmployee.STATUS_STAGIAIRE,
        'temporaire': AuthorizedEmployee.STATUS_TEMPORAIRE,
    }

    results = {'created': 0, 'updated': 0, 'skipped': 0, 'rows': []}

    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not row[0]:
            continue

        cuid_raw = str(row[0]).strip().upper()
        status_raw = str(row[1]).strip().lower() if row[1] else 'permanent'
        dept_raw = str(row[2]).strip() if len(row) > 2 and row[2] else ''

        if not cuid_raw:
            results['skipped'] += 1
            results['rows'].append({'row': row_idx, 'cuid': '—', 'status': 'ignoré', 'detail': 'CUID vide'})
            continue

        # Résoudre le statut
        employee_status = status_map.get(status_raw, AuthorizedEmployee.STATUS_PERMANENT)

        # Résoudre le département (recherche insensible à la casse)
        department = None
        if dept_raw:
            department = (
                Department.objects.filter(name__iexact=dept_raw).first()
                or Department.objects.filter(name__icontains=dept_raw).first()
            )

        # Créer ou mettre à jour
        obj, created = AuthorizedEmployee.objects.update_or_create(
            cuid=cuid_raw,
            defaults={
                'employee_status': employee_status,
                'department': department,
            }
        )

        if created:
            results['created'] += 1
            action = 'créé'
        else:
            results['updated'] += 1
            action = 'mis à jour'

        dept_info = department.name if department else f'"{dept_raw}" non trouvé'
        results['rows'].append({
            'row': row_idx,
            'cuid': cuid_raw,
            'status': action,
            'detail': f"{obj.get_employee_status_display()} · {dept_info}",
        })

    wb.close()
    return results


# ──────────────────────────────────────────────────────────────────────────────
# INSCRIPTION
# ──────────────────────────────────────────────────────────────────────────────

def register(request):
    """Étape 1 — Formulaire d'inscription."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    context = {'errors': [], 'form_data': {}}

    if request.method == 'POST':
        cuid       = request.POST.get('cuid', '').strip().upper()
        email      = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        password   = request.POST.get('password', '')
        password2  = request.POST.get('password2', '')

        context['form_data'] = {
            'cuid': cuid, 'email': email,
            'first_name': first_name, 'last_name': last_name,
        }

        errors = _validate_registration(cuid, email, first_name, last_name, password, password2)

        if not errors:
            user, code = _create_pending_user(cuid, email, first_name, last_name, password)
            sent = _send_confirmation_code(user, code)

            if not sent:
                user.delete()
                errors = ["Impossible d'envoyer le code de confirmation. Contactez l'administrateur."]
            else:
                AuthorizedEmployee.objects.filter(cuid=cuid).update(
                    is_registered=True, registered_user=user
                )
                request.session['email_verify_pending'] = email
                return redirect('accounts:verify_email')

        context['errors'] = errors

    return render(request, 'accounts/register.html', context)


@require_http_methods(['GET', 'POST'])
def verify_email(request):
    """Étape 2 — Saisie du code à 8 caractères avec chrono 5 min."""
    email = request.session.get('email_verify_pending')
    if not email:
        messages.error(request, "Session expirée. Recommencez l'inscription.")
        return redirect('accounts:register')

    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        messages.error(request, "Compte introuvable ou déjà activé.")
        return redirect('account_login')

    # Calcul du temps restant (en secondes) pour le chrono JS
    seconds_remaining = 0
    if user.email_confirm_sent_at:
        elapsed = (timezone.now() - user.email_confirm_sent_at).total_seconds()
        seconds_remaining = max(0, int(CODE_EXPIRY_MINUTES * 60 - elapsed))

    context = {
        'email': email,
        'seconds_remaining': seconds_remaining,
        'expiry_minutes': CODE_EXPIRY_MINUTES,
        'error': None,
    }

    if request.method == 'POST':
        entered = request.POST.get('code', '').strip().upper()

        if seconds_remaining <= 0:
            context['error'] = "Le code a expiré. Cliquez sur « Renvoyer le code »."
            return render(request, 'accounts/verify_email.html', context)

        if user.email_confirm_code == entered:
            user.is_active = True
            user.email_confirm_code = ''
            user.save(update_fields=['is_active', 'email_confirm_code'])
            request.session.pop('email_verify_pending', None)
            messages.success(request, "Votre compte est activé. Bienvenue sur QoS Ticketing !")
            return redirect('account_login')
        else:
            context['error'] = "Code incorrect. Vérifiez l'email reçu et réessayez."

    return render(request, 'accounts/verify_email.html', context)


@require_http_methods(['POST'])
def resend_code(request):
    """Renvoie un nouveau code et repart le chrono."""
    email = request.session.get('email_verify_pending')
    if not email:
        messages.error(request, "Session expirée. Recommencez l'inscription.")
        return redirect('accounts:register')

    try:
        user = User.objects.get(email=email, is_active=False)
    except User.DoesNotExist:
        messages.error(request, "Compte introuvable.")
        return redirect('accounts:register')

    code = _generate_code()
    user.email_confirm_code = code
    user.email_confirm_sent_at = timezone.now()
    user.save(update_fields=['email_confirm_code', 'email_confirm_sent_at'])

    sent = _send_confirmation_code(user, code)
    if sent:
        messages.success(request, "Un nouveau code vous a été envoyé par email.")
    else:
        messages.error(request, "Échec de l'envoi. Contactez l'administrateur.")

    return redirect('accounts:verify_email')


# ──────────────────────────────────────────────────────────────────────────────
# Helpers privés
# ──────────────────────────────────────────────────────────────────────────────

def _generate_code():
    return ''.join(secrets.choice(CODE_ALPHABET) for _ in range(8))


def _validate_registration(cuid, email, first_name, last_name, password, password2):
    errors = []
    allowed = getattr(settings, 'ALLOWED_EMAIL_DOMAIN', ALLOWED_DOMAIN)

    if not cuid:
        errors.append("Le CUID est obligatoire.")
    else:
        emp = AuthorizedEmployee.objects.filter(cuid=cuid).first()
        if emp is None:
            errors.append("Ce CUID n'est pas dans la liste des employés autorisés.")
        elif emp.is_registered:
            errors.append("Ce CUID est déjà associé à un compte. Connectez-vous directement.")

    if not email:
        errors.append("L'adresse email est obligatoire.")
    elif not email.endswith(allowed):
        errors.append(f"Seules les adresses {allowed} sont autorisées.")
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
    emp = AuthorizedEmployee.objects.filter(cuid=cuid).first()
    code = _generate_code()
    user = User(
        username=cuid,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=False,
        role=User.ROLE_DEMANDEUR,
        department=emp.department if emp else None,
        email_confirm_code=code,
        email_confirm_sent_at=timezone.now(),
    )
    user.set_password(password)
    user.save()
    return user, code


def _send_confirmation_code(user, code):
    # Toujours afficher le code en clair dans le terminal (dev + prod)
    logger.info(
        "\033[33m[CODE CONFIRMATION]\033[0m CUID=%-12s  CODE=\033[1;32m%s\033[0m  → %s",
        user.username, code, user.email,
        extra={'user': user.username},
    )
    try:
        text_body = (
            f"Bonjour {user.first_name},\n\n"
            f"Votre code de confirmation QoS Ticketing est :\n\n"
            f"        {code}\n\n"
            f"Saisissez ce code dans les {CODE_EXPIRY_MINUTES} minutes.\n"
            f"Passé ce délai, demandez un nouveau code.\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n\n"
            f"— Équipe QoS Ticketing OMCM"
        )
        html_body = render_to_string('emails/confirm_code.html', {
            'first_name': user.first_name or user.username,
            'code': code,
            'expiry_minutes': CODE_EXPIRY_MINUTES,
        })
        msg = EmailMultiAlternatives(
            subject='QoS Ticketing — Votre code de confirmation',
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info(
            "MAIL OK : code confirmation envoye a %s (CUID: %s)", user.email, user.username,
            extra={'user': user.username},
        )
        return True
    except Exception as exc:
        logger.error(
            "MAIL ECHEC : code confirmation vers %s (CUID: %s) : %s", user.email, user.username, exc,
            extra={'user': user.username},
        )
        return False


# ──────────────────────────────────────────────────────────────────────────────
# RÉINITIALISATION DE MOT DE PASSE PAR CODE 8 CARACTÈRES
# Flux : saisie CUID → envoi code → vérification code (chrono 5 min) → nouveau MDP
# ──────────────────────────────────────────────────────────────────────────────

def custom_password_reset(request):
    """Étape 1 — Saisie du CUID et envoi du code à 8 caractères."""
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    context = {'error': None, 'cuid': ''}

    if request.method == 'POST':
        cuid = request.POST.get('cuid', '').strip().upper()
        context['cuid'] = cuid

        if not cuid:
            context['error'] = "Le CUID est obligatoire."
        else:
            user = User.objects.filter(username=cuid, is_active=True).first()
            if user and user.email:
                code = _generate_code()
                user.pwd_reset_code = code
                user.pwd_reset_sent_at = timezone.now()
                user.save(update_fields=['pwd_reset_code', 'pwd_reset_sent_at'])

                sent = _send_reset_code(user, code)
                if sent:
                    request.session['pwd_reset_cuid'] = cuid
                    return redirect('accounts:password_reset_verify')
                else:
                    context['error'] = "Échec de l'envoi. Contactez l'administrateur."
            else:
                logger.warning(
                    "Reset MDP : CUID inconnu ou inactif : %s", cuid,
                    extra={'user': cuid},
                )
                # Rediriger quand même pour ne pas révéler si le CUID existe
                request.session['pwd_reset_cuid'] = '__unknown__'
                return redirect('accounts:password_reset_verify')

    return render(request, 'account/password_reset.html', context)


@require_http_methods(['GET', 'POST'])
def password_reset_verify(request):
    """Étape 2 — Saisie du code à 8 caractères avec chrono 5 min."""
    cuid = request.session.get('pwd_reset_cuid')
    if not cuid:
        messages.error(request, "Session expirée. Recommencez la réinitialisation.")
        return redirect('account_reset_password')

    # CUID inexistant (on a quand même redirigé pour ne pas révéler)
    user = User.objects.filter(username=cuid, is_active=True).first()

    seconds_remaining = 0
    if user and user.pwd_reset_sent_at:
        elapsed = (timezone.now() - user.pwd_reset_sent_at).total_seconds()
        seconds_remaining = max(0, int(CODE_EXPIRY_MINUTES * 60 - elapsed))

    context = {
        'seconds_remaining': seconds_remaining,
        'expiry_minutes': CODE_EXPIRY_MINUTES,
        'error': None,
    }

    if request.method == 'POST':
        entered = request.POST.get('code', '').strip().upper()

        if not user:
            context['error'] = "Code incorrect."
            return render(request, 'account/password_reset_verify.html', context)

        if seconds_remaining <= 0:
            context['error'] = "Le code a expiré. Cliquez sur « Renvoyer le code »."
            return render(request, 'account/password_reset_verify.html', context)

        if user.pwd_reset_code == entered:
            # Code valide : marquer la session et rediriger vers changement MDP
            user.pwd_reset_code = ''
            user.save(update_fields=['pwd_reset_code'])
            request.session['pwd_reset_verified'] = cuid
            request.session.pop('pwd_reset_cuid', None)
            return redirect('accounts:password_reset_change')
        else:
            context['error'] = "Code incorrect. Vérifiez l'email reçu et réessayez."

    return render(request, 'account/password_reset_verify.html', context)


@require_http_methods(['POST'])
def password_reset_resend(request):
    """Renvoie un nouveau code de reset et repart le chrono."""
    cuid = request.session.get('pwd_reset_cuid')
    if not cuid:
        messages.error(request, "Session expirée. Recommencez la réinitialisation.")
        return redirect('account_reset_password')

    user = User.objects.filter(username=cuid, is_active=True).first()
    if not user:
        return redirect('accounts:password_reset_verify')

    code = _generate_code()
    user.pwd_reset_code = code
    user.pwd_reset_sent_at = timezone.now()
    user.save(update_fields=['pwd_reset_code', 'pwd_reset_sent_at'])

    sent = _send_reset_code(user, code)
    if sent:
        messages.success(request, "Un nouveau code vous a été envoyé par email.")
    else:
        messages.error(request, "Échec de l'envoi. Contactez l'administrateur.")

    return redirect('accounts:password_reset_verify')


@require_http_methods(['GET', 'POST'])
def password_reset_change(request):
    """Étape 3 — Saisie du nouveau mot de passe (après code vérifié)."""
    cuid = request.session.get('pwd_reset_verified')
    if not cuid:
        messages.error(request, "Session invalide. Recommencez la réinitialisation.")
        return redirect('account_reset_password')

    user = User.objects.filter(username=cuid, is_active=True).first()
    if not user:
        messages.error(request, "Compte introuvable.")
        return redirect('account_reset_password')

    context = {'errors': []}

    if request.method == 'POST':
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères.")
        if password != password2:
            errors.append("Les mots de passe ne correspondent pas.")

        if not errors:
            user.set_password(password)
            user.save()
            request.session.pop('pwd_reset_verified', None)
            logger.info(
                "Mot de passe réinitialisé pour CUID: %s", cuid,
                extra={'user': cuid},
            )
            messages.success(request, "Mot de passe modifié avec succès. Connectez-vous.")
            return redirect('account_login')

        context['errors'] = errors

    return render(request, 'account/password_reset_change.html', context)


def _send_reset_code(user, code):
    """Envoie le code de réinitialisation par email (HTML + texte brut)."""
    logger.info(
        "\033[35m[CODE RESET MDP]\033[0m   CUID=%-12s  CODE=\033[1;32m%s\033[0m  → %s",
        user.username, code, user.email,
        extra={'user': user.username},
    )
    try:
        text_body = (
            f"Bonjour {user.first_name or user.username},\n\n"
            f"Votre code de réinitialisation de mot de passe QoS Ticketing est :\n\n"
            f"        {code}\n\n"
            f"Saisissez ce code dans les {CODE_EXPIRY_MINUTES} minutes.\n"
            f"Passé ce délai, demandez un nouveau code.\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.\n\n"
            f"— Équipe QoS Ticketing OMCM"
        )
        html_body = render_to_string('emails/reset_code.html', {
            'first_name': user.first_name or user.username,
            'code': code,
            'expiry_minutes': CODE_EXPIRY_MINUTES,
        })
        msg = EmailMultiAlternatives(
            subject='QoS Ticketing — Code de réinitialisation de mot de passe',
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send(fail_silently=False)
        logger.info(
            "MAIL OK : code reset envoye a %s (CUID: %s)", user.email, user.username,
            extra={'user': user.username},
        )
        return True
    except Exception as exc:
        logger.error(
            "MAIL ECHEC : code reset vers %s (CUID: %s) : %s", user.email, user.username, exc,
            extra={'user': user.username},
        )
        return False
