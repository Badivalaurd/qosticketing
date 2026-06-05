from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_INFO = 'INFO'
    TYPE_SUCCESS = 'SUCCESS'
    TYPE_WARNING = 'WARNING'
    TYPE_DANGER = 'DANGER'

    TYPE_CHOICES = [
        (TYPE_INFO, 'Information'),
        (TYPE_SUCCESS, 'Succès'),
        (TYPE_WARNING, 'Avertissement'),
        (TYPE_DANGER, 'Alerte'),
    ]

    EVENT_CREATED = 'TICKET_CREATED'
    EVENT_ASSIGNED = 'TICKET_ASSIGNED'
    EVENT_STATUS = 'STATUS_CHANGED'
    EVENT_COMMENT = 'COMMENT_ADDED'
    EVENT_SLA = 'SLA_EXCEEDED'
    EVENT_CLOSED = 'TICKET_CLOSED'
    EVENT_MENTION = 'MENTION'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications'
    )
    title = models.CharField('Titre', max_length=300)
    message = models.TextField('Message')
    type = models.CharField('Type', max_length=10, choices=TYPE_CHOICES, default=TYPE_INFO)
    event = models.CharField('Événement', max_length=30, blank=True)
    is_read = models.BooleanField('Lu', default=False)
    ticket = models.ForeignKey(
        'tickets.Ticket', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='notifications', verbose_name='Ticket'
    )
    url = models.CharField('URL', max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.title}"

    def mark_read(self):
        self.is_read = True
        self.save(update_fields=['is_read'])
