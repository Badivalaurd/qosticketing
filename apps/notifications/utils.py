from django.urls import reverse
from .models import Notification


def send_ticket_notification(ticket, event, recipient=None):
    """
    Crée les notifications in-app ET déclenche les emails.

    Routage :
    - created       → admins + agents SI (si dept IT) OU manager du dept cible
    - assigned      → demandeur + technicien assigné
    - status_changed→ demandeur + technicien assigné
    - comment_added → demandeur + technicien assigné
    - sla_exceeded  → technicien assigné + admins
    - mentioned     → utilisateur mentionné
    """
    from apps.accounts.models import User

    recipients = set()

    if event == 'created':
        recipients = _recipients_for_created(ticket)

    elif event == 'assigned':
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to)
        recipients.add(ticket.created_by)

    elif event == 'status_changed':
        recipients.add(ticket.created_by)
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to)

    elif event == 'comment_added':
        recipients.add(ticket.created_by)
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to)

    elif event == 'sla_exceeded':
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to)
        for u in User.objects.filter(role=User.ROLE_ADMIN, is_active=True):
            recipients.add(u)

    elif event == 'mentioned' and recipient:
        recipients.add(recipient)

    elif event == 'info_responded':
        # Notifier le technicien assigné que la réponse est arrivée
        if ticket.assigned_to:
            recipients.add(ticket.assigned_to)

    elif event == 'transferred' and recipient:
        # Notifier le manager du département cible
        recipients.add(recipient)

    url = reverse('tickets:detail', kwargs={'number': ticket.number})

    event_titles = {
        'created':        f"Nouveau ticket {ticket.number}",
        'assigned':       f"Ticket {ticket.number} affecté",
        'status_changed': f"Ticket {ticket.number} — statut modifié",
        'comment_added':  f"Commentaire sur {ticket.number}",
        'sla_exceeded':   f"SLA dépassé — {ticket.number}",
        'mentioned':      f"Mention dans {ticket.number}",
        'info_responded': f"Réponse reçue sur {ticket.number}",
        'transferred':    f"Ticket {ticket.number} transféré",
    }
    event_messages = {
        'created':        f"Le ticket «{ticket.title}» a été créé.",
        'assigned':       f"Le ticket «{ticket.title}» vous a été affecté.",
        'status_changed': f"Statut : «{ticket.get_status_display()}».",
        'comment_added':  f"Nouveau commentaire sur «{ticket.title}».",
        'sla_exceeded':   f"SLA dépassé sur «{ticket.title}».",
        'mentioned':      f"Vous avez été mentionné dans «{ticket.title}».",
        'info_responded': f"La demande d'information sur «{ticket.title}» a reçu une réponse.",
        'transferred':    f"Le ticket «{ticket.title}» a été transféré à votre département.",
    }
    event_types = {
        'created':        Notification.TYPE_INFO,
        'assigned':       Notification.TYPE_INFO,
        'status_changed': Notification.TYPE_SUCCESS,
        'comment_added':  Notification.TYPE_INFO,
        'sla_exceeded':   Notification.TYPE_DANGER,
        'mentioned':      Notification.TYPE_WARNING,
        'info_responded': Notification.TYPE_SUCCESS,
        'transferred':    Notification.TYPE_WARNING,
    }

    for user in recipients:
        Notification.objects.create(
            user=user,
            title=event_titles.get(event, 'Notification'),
            message=event_messages.get(event, ''),
            type=event_types.get(event, Notification.TYPE_INFO),
            event=event.upper(),
            ticket=ticket,
            url=url,
        )

    _send_ticket_emails(ticket, event, recipients, url, event_titles, event_messages)


def send_project_notification(project, event, recipient=None, extra_context=None):
    """
    Notifications de projet in-app + email.

    event : 'member_added' | 'status_changed' | 'sprint_started' | 'sprint_ended'
    """
    recipients = set()

    if event == 'member_added' and recipient:
        recipients.add(recipient)
    elif event in ('status_changed', 'sprint_started', 'sprint_ended'):
        # Notifier tous les membres + manager
        if project.manager:
            recipients.add(project.manager)
        for member in project.team.filter(is_active=True):
            recipients.add(member)

    event_titles = {
        'member_added':   f"Vous avez été ajouté au projet «{project.name}»",
        'status_changed': f"Projet «{project.name}» — statut modifié",
        'sprint_started': f"Sprint démarré sur «{project.name}»",
        'sprint_ended':   f"Sprint terminé sur «{project.name}»",
    }
    event_messages = {
        'member_added':   f"Vous faites maintenant partie de l'équipe du projet «{project.name}».",
        'status_changed': f"Le statut du projet est maintenant «{project.get_status_display()}».",
        'sprint_started': f"Un nouveau sprint vient de démarrer sur «{project.name}».",
        'sprint_ended':   f"Le sprint en cours sur «{project.name}» est maintenant terminé.",
    }

    for user in recipients:
        Notification.objects.create(
            user=user,
            title=event_titles.get(event, 'Notification projet'),
            message=event_messages.get(event, ''),
            type=Notification.TYPE_INFO,
            event=f"PROJECT_{event.upper()}",
        )

    _send_project_emails(project, event, recipients, event_titles, event_messages, extra_context)


# ── Helpers privés ──────────────────────────────────────────────────────────

def _recipients_for_created(ticket):
    """
    Routage à la création :
    - Si le ticket est destiné au département IT → admins + agents SI
    - Sinon → manager du département cible
    """
    from apps.accounts.models import User, Department
    recipients = set()

    target_dept = ticket.target_department or ticket.department
    is_it_target = target_dept and target_dept.is_it_department if target_dept else False

    if is_it_target or target_dept is None:
        # Notifier admins et agents SI
        for u in User.objects.filter(
            role__in=[User.ROLE_ADMIN, User.ROLE_AGENT],
            is_active=True,
        ):
            recipients.add(u)
    else:
        # Notifier le manager du département cible
        for u in User.objects.filter(
            role=User.ROLE_MANAGER,
            department=target_dept,
            is_active=True,
        ):
            recipients.add(u)
        # + les admins toujours en copie
        for u in User.objects.filter(role=User.ROLE_ADMIN, is_active=True):
            recipients.add(u)

    return recipients


def _get_site_url():
    from django.conf import settings
    try:
        host = settings.ALLOWED_HOSTS[0] if settings.ALLOWED_HOSTS else 'localhost'
        if host in ('localhost', '127.0.0.1'):
            return "http://localhost:8000"
        return f"https://{host}"
    except Exception:
        return "http://localhost:8000"


def _send_ticket_emails(ticket, event, recipients, url, titles, messages):
    """Déclenche l'envoi d'email (thread) pour chaque destinataire."""
    try:
        from .tasks import send_email_task
        site_url = _get_site_url()

        template_map = {
            'created':        'ticket_created.html',
            'assigned':       'ticket_assigned.html',
            'status_changed': 'ticket_status_changed.html',
            'comment_added':  'ticket_comment.html',
            'sla_exceeded':   'sla_exceeded.html',
            'mentioned':      'ticket_mentioned.html',
        }
        template = template_map.get(event, 'ticket_generic.html')

        context = {
            'ticket_number': ticket.number,
            'ticket_title': ticket.title,
            'ticket_priority': ticket.get_priority_display(),
            'ticket_status': ticket.get_status_display(),
            'ticket_category': ticket.category.name if ticket.category else '',
            'ticket_url': f"{site_url}{url}",
            'message': messages.get(event, ''),
            'site_url': site_url,
        }

        for user in recipients:
            if user.email:
                send_email_task(
                    to_email=user.email,
                    subject=titles.get(event, 'Notification QoS'),
                    template_name=template,
                    context={**context, 'recipient_name': user.get_full_name() or user.username},
                )
    except Exception:
        pass


def _send_project_emails(project, event, recipients, titles, messages, extra_context=None):
    """Déclenche les tâches Celery d'envoi d'email pour les notifications projet."""
    try:
        from .tasks import send_email_task
        site_url = _get_site_url()

        template_map = {
            'member_added':   'project_member_added.html',
            'status_changed': 'project_status_changed.html',
            'sprint_started': 'project_sprint_update.html',
            'sprint_ended':   'project_sprint_update.html',
        }
        template = template_map.get(event, 'project_generic.html')

        context = {
            'project_name': project.name,
            'project_code': project.code,
            'project_status': project.get_status_display(),
            'project_url': f"{site_url}/projects/{project.pk}/",
            'message': messages.get(event, ''),
            'site_url': site_url,
            **(extra_context or {}),
        }

        for user in recipients:
            if user.email:
                send_email_task(
                    to_email=user.email,
                    subject=titles.get(event, 'Notification Projet QoS'),
                    template_name=template,
                    context={**context, 'recipient_name': user.get_full_name() or user.username},
                )
    except Exception:
        pass
