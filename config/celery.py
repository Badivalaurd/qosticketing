import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('qos_ticketing')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Vérification SLA toutes les minutes (alertes 1h/30min/10min avant dépassement)
    'check-sla-warnings-every-minute': {
        'task': 'apps.notifications.tasks.check_sla_warnings',
        'schedule': 60.0,
    },
    # Digest quotidien des SLA dépassés — chaque matin à 8h00
    'send-daily-sla-digest-8am': {
        'task': 'apps.notifications.tasks.send_daily_sla_digest',
        'schedule': crontab(hour=8, minute=0),
    },
}
