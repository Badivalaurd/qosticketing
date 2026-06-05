"""
Envoie le récapitulatif quotidien des tickets SLA dépassés à chaque agent/technicien.
À planifier chaque matin à 8h via le Planificateur de tâches Windows.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Envoie le digest quotidien des tickets SLA dépassés'

    def handle(self, *args, **options):
        from apps.notifications.tasks import send_daily_digest
        sent = send_daily_digest()
        self.stdout.write(
            self.style.SUCCESS(f'Digest envoyé à {sent} utilisateur(s).')
            if sent else 'Aucun digest à envoyer (pas de tickets SLA dépassés).'
        )
