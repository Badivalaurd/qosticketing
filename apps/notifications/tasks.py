"""
Envoi d'emails sans Celery/Redis — utilise des threads Python natifs.
Les tâches périodiques (SLA warnings, digest) sont dans les management commands.
"""
import threading
import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def send_email_task(to_email, subject, template_name, context):
    """Lance l'envoi de l'email dans un thread séparé pour ne pas bloquer la requête."""
    t = threading.Thread(
        target=_send_email_sync,
        args=(to_email, subject, template_name, context),
        daemon=True,
    )
    t.start()


# Compatibilité avec l'ancien code qui appelait .delay()
class _DelayShim:
    def __init__(self, func):
        self._func = func

    def delay(self, **kwargs):
        self._func(**kwargs)

    def __call__(self, **kwargs):
        self._func(**kwargs)


def _send_email_sync(to_email, subject, template_name, context):
    """Envoi synchrone réel — appelé depuis un thread."""
    try:
        html_content = render_to_string(f'email/{template_name}', context)
        # Fallback texte brut
        text_content = context.get('message', subject)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logger.info(f"Email envoyé → {to_email} | {subject}")
    except Exception as exc:
        logger.error(f"Échec email → {to_email} : {exc}")


def send_sla_warnings():
    """
    Vérifie les échéances SLA et envoie les alertes 1h / 30min / 10min.
    Appelé par la commande : python manage.py check_sla_warnings
    """
    from django.utils import timezone
    from apps.tickets.models import Ticket
    from apps.accounts.models import User

    open_statuses = [
        Ticket.STATUS_NOUVEAU, Ticket.STATUS_AFFECTE,
        Ticket.STATUS_EN_COURS, Ticket.STATUS_ATTENTE_INFO,
        Ticket.STATUS_ATTENTE_PRESTATAIRE,
    ]
    now = timezone.now()

    tickets = Ticket.objects.filter(
        status__in=open_statuses,
        sla_resolution_deadline__isnull=False,
        sla_paused_at__isnull=True,
        sla_resolution_exceeded=False,
    ).select_related('assigned_to', 'created_by', 'category')

    updated = 0
    for ticket in tickets:
        deadline = ticket.sla_resolution_deadline
        time_left = (deadline - now).total_seconds() / 60  # minutes

        recipients = _sla_warning_recipients(ticket)
        if not recipients:
            continue

        fields_to_save = []

        if 50 <= time_left <= 70 and not ticket.sla_warning_1h_sent:
            _dispatch_sla_warning(ticket, recipients, '1 heure', int(time_left))
            ticket.sla_warning_1h_sent = True
            fields_to_save.append('sla_warning_1h_sent')

        elif 20 <= time_left <= 35 and not ticket.sla_warning_30m_sent:
            _dispatch_sla_warning(ticket, recipients, '30 minutes', int(time_left))
            ticket.sla_warning_30m_sent = True
            fields_to_save.append('sla_warning_30m_sent')

        elif 5 <= time_left <= 15 and not ticket.sla_warning_10m_sent:
            _dispatch_sla_warning(ticket, recipients, '10 minutes', int(time_left))
            ticket.sla_warning_10m_sent = True
            fields_to_save.append('sla_warning_10m_sent')

        if fields_to_save:
            fields_to_save.append('updated_at')
            ticket.save(update_fields=fields_to_save)
            updated += 1

    return updated


def send_daily_digest():
    """
    Envoie à chaque technicien/agent son récapitulatif de tickets SLA dépassés.
    Appelé par : python manage.py send_daily_digest
    """
    from django.utils import timezone
    from apps.tickets.models import Ticket
    from apps.accounts.models import User

    open_statuses = [
        Ticket.STATUS_AFFECTE, Ticket.STATUS_EN_COURS,
        Ticket.STATUS_ATTENTE_INFO, Ticket.STATUS_ATTENTE_PRESTATAIRE,
    ]

    agents = User.objects.filter(
        role__in=[User.ROLE_TECHNICIEN, User.ROLE_AGENT, User.ROLE_ADMIN],
        is_active=True,
    ).exclude(email='')

    sent = 0
    for agent in agents:
        overdue = Ticket.objects.filter(
            assigned_to=agent,
            status__in=open_statuses,
            sla_resolution_exceeded=True,
        ).select_related('category', 'department', 'created_by').order_by('sla_resolution_deadline')

        if not overdue.exists():
            continue

        context = {
            'user': agent,
            'tickets': list(overdue),
            'count': overdue.count(),
            'site_url': _site_url(),
            'today': timezone.now().date(),
        }
        _send_email_sync(
            to_email=agent.email,
            subject=f"[QoS] Récapitulatif SLA — {overdue.count()} ticket(s) en retard",
            template_name='sla_daily_digest.html',
            context=context,
        )
        sent += 1

    return sent


# ── Helpers ─────────────────────────────────────────────────────────────────

def _sla_warning_recipients(ticket):
    from apps.accounts.models import User
    emails = []
    if ticket.assigned_to and ticket.assigned_to.email:
        emails.append(ticket.assigned_to.email)
    for admin in User.objects.filter(role=User.ROLE_ADMIN, is_active=True).exclude(email=''):
        if admin.email not in emails:
            emails.append(admin.email)
    return emails


def _dispatch_sla_warning(ticket, recipients, time_label, minutes_left):
    context = {
        'ticket': {
            'number': ticket.number,
            'title': ticket.title,
            'priority': ticket.get_priority_display(),
            'status': ticket.get_status_display(),
            'category': ticket.category.name if ticket.category else '',
            'deadline': ticket.sla_resolution_deadline,
            'url': f"{_site_url()}/tickets/{ticket.number}/",
        },
        'time_label': time_label,
        'minutes_left': minutes_left,
        'site_url': _site_url(),
        'recipient_name': '',
    }
    subject = f"[QoS] Alerte SLA — {ticket.number} expire dans {time_label}"
    for email in recipients:
        send_email_task(email, subject, 'sla_warning.html', context)


def _site_url():
    try:
        host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
        return "http://localhost:8000" if host in ('localhost', '127.0.0.1') else f"https://{host}"
    except Exception:
        return "http://localhost:8000"
