from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ticket


@receiver(post_save, sender=Ticket)
def check_sla(sender, instance, created, **kwargs):
    if created:
        return  # Les deadlines SLA sont déjà initialisées dans save()

    now = timezone.now()
    updates = {}

    # SLA prise en charge dépassée
    if (instance.sla_response_deadline
            and not instance.sla_response_exceeded
            and not instance.assigned_at
            and not instance.is_sla_paused
            and instance.status not in Ticket.SLA_STOP_STATUSES
            and now > instance.sla_response_deadline):
        updates['sla_response_exceeded'] = True

    # SLA traitement dépassé
    if (instance.sla_resolution_deadline
            and not instance.sla_resolution_exceeded
            and not instance.is_sla_paused
            and instance.status not in Ticket.SLA_STOP_STATUSES
            and now > instance.sla_resolution_deadline):
        updates['sla_resolution_exceeded'] = True
        if instance.status == Ticket.STATUS_RESOLU:
            updates['resolved_out_of_sla'] = True

    if updates:
        Ticket.objects.filter(pk=instance.pk).update(**updates)
