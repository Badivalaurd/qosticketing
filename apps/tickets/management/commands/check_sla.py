"""
Vérifie et met à jour les dépassements SLA.
    python manage.py check_sla
"""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Vérifie les dépassements SLA et met à jour les tickets'

    def handle(self, *args, **options):
        from apps.tickets.models import Ticket
        from apps.notifications.utils import send_ticket_notification

        open_statuses = [
            Ticket.STATUS_NOUVEAU, Ticket.STATUS_AFFECTE,
            Ticket.STATUS_EN_COURS, Ticket.STATUS_ATTENTE_INFO, Ticket.STATUS_ATTENTE_PRESTATAIRE
        ]
        tickets = Ticket.objects.filter(status__in=open_statuses)
        now = timezone.now()
        updated = 0

        for ticket in tickets:
            changed = False

            # SLA prise en charge
            if (ticket.sla_response_deadline and not ticket.sla_response_exceeded
                    and not ticket.assigned_at and now > ticket.sla_response_deadline):
                ticket.sla_response_exceeded = True
                send_ticket_notification(ticket, 'sla_exceeded')
                changed = True

            # SLA traitement
            if (ticket.sla_resolution_deadline and not ticket.sla_resolution_exceeded
                    and not ticket.is_sla_paused and now > ticket.sla_resolution_deadline):
                ticket.sla_resolution_exceeded = True
                send_ticket_notification(ticket, 'sla_exceeded')
                changed = True

            if changed:
                ticket.save(update_fields=['sla_response_exceeded', 'sla_resolution_exceeded', 'updated_at'])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f'{updated} ticket(s) SLA mis à jour.'))
