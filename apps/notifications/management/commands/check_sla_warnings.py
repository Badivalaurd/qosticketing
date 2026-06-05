"""
Vérifie les SLA et envoie les alertes email 1h / 30min / 10min avant dépassement.
À planifier toutes les minutes via le Planificateur de tâches Windows.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Envoie les alertes email SLA (1h, 30min, 10min avant dépassement)'

    def handle(self, *args, **options):
        from apps.notifications.tasks import send_sla_warnings
        updated = send_sla_warnings()
        if updated:
            self.stdout.write(self.style.WARNING(f'{updated} alerte(s) SLA envoyée(s).'))
        else:
            self.stdout.write('Aucune alerte SLA à envoyer.')
