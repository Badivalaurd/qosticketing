from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from .models import Project, Sprint


@receiver(m2m_changed, sender=Project.team.through)
def project_team_changed(sender, instance, action, pk_set, **kwargs):
    """Notifie les nouveaux membres ajoutés à l'équipe du projet."""
    if action != 'post_add' or not pk_set:
        return
    from django.contrib.auth import get_user_model
    from apps.notifications.utils import send_project_notification
    User = get_user_model()
    for user_pk in pk_set:
        try:
            user = User.objects.get(pk=user_pk)
            send_project_notification(instance, 'member_added', recipient=user)
        except User.DoesNotExist:
            pass


@receiver(post_save, sender=Project)
def project_status_changed(sender, instance, created, **kwargs):
    """Notifie les membres quand le statut du projet change (hors création)."""
    if created:
        return
    # On vérifie si le statut a changé via update_fields
    if hasattr(instance, '_status_changed') and instance._status_changed:
        from apps.notifications.utils import send_project_notification
        send_project_notification(instance, 'status_changed')


@receiver(post_save, sender=Sprint)
def sprint_status_changed(sender, instance, created, **kwargs):
    """Notifie les membres quand un sprint démarre ou se termine."""
    from apps.notifications.utils import send_project_notification
    if not created and hasattr(instance, '_status_changed') and instance._status_changed:
        if instance.status == Sprint.STATUS_ACTIF:
            send_project_notification(
                instance.project, 'sprint_started',
                extra_context={
                    'sprint_name': instance.name,
                    'sprint_goal': getattr(instance, 'goal', ''),
                    'sprint_start': instance.start_date,
                    'sprint_end': instance.end_date,
                }
            )
        elif instance.status == Sprint.STATUS_TERMINE:
            send_project_notification(
                instance.project, 'sprint_ended',
                extra_context={
                    'sprint_name': instance.name,
                    'sprint_start': instance.start_date,
                    'sprint_end': instance.end_date,
                }
            )
