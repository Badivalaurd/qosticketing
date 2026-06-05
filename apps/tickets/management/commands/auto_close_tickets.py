"""
Ferme automatiquement les tickets restés 2 jours en état 'Résolu'.
À exécuter via le planificateur Windows ou Celery beat :
    python manage.py auto_close_tickets
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Clôture automatiquement les tickets résolus depuis plus de 2 jours'

    def handle(self, *args, **options):
        from apps.tickets.models import Ticket, TicketHistory

        threshold = timezone.now() - timedelta(days=2)
        tickets = Ticket.objects.filter(
            status=Ticket.STATUS_RESOLU,
            resolved_at__lte=threshold
        )
        count = 0
        for ticket in tickets:
            ticket.status = Ticket.STATUS_CLOTURE
            ticket.closed_at = timezone.now()
            ticket.save(update_fields=['status', 'closed_at', 'updated_at'])
            TicketHistory.objects.create(
                ticket=ticket,
                user=None,
                action="Clôture automatique — ticket résolu depuis plus de 2 jours",
                field_name='status',
                old_value=Ticket.STATUS_RESOLU,
                new_value=Ticket.STATUS_CLOTURE,
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} ticket(s) clôturé(s) automatiquement.'))
