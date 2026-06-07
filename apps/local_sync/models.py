"""
Modèles SQLite pour le fonctionnement hors-ligne.

PendingTicket  → base `pending`  : tickets créés sans connexion
CachedTicket   → base `cache`    : dernière snapshot du listing
"""
import uuid
from django.db import models


class PendingTicket(models.Model):
    """Ticket créé hors-ligne, en attente de synchronisation vers PostgreSQL."""

    SYNC_PENDING = 'PENDING'
    SYNC_SYNCED = 'SYNCED'
    SYNC_FAILED = 'FAILED'
    SYNC_CANCELLED = 'CANCELLED'

    SYNC_CHOICES = [
        (SYNC_PENDING, 'En attente'),
        (SYNC_SYNCED, 'Synchronisé'),
        (SYNC_FAILED, 'Échec'),
        (SYNC_CANCELLED, 'Annulé'),
    ]

    local_id = models.CharField(
        'ID local', max_length=36, unique=True,
        default=lambda: str(uuid.uuid4())
    )

    # Données de l'auteur (capturées au moment de la création)
    user_id = models.IntegerField('ID utilisateur (PG)')
    username = models.CharField('Identifiant', max_length=150)
    department_id = models.IntegerField('Département demandeur (ID)', null=True)
    target_department_id = models.IntegerField('Département cible (ID)', null=True)

    # Données du ticket
    title = models.CharField('Titre', max_length=200)
    description = models.TextField('Description')
    priority = models.CharField('Priorité', max_length=5, default='P2')
    category_id = models.IntegerField('Catégorie (ID)', null=True)

    # Cycle de synchronisation
    sync_status = models.CharField(
        'Statut sync', max_length=20,
        choices=SYNC_CHOICES, default=SYNC_PENDING
    )
    created_at_local = models.DateTimeField('Créé localement le', auto_now_add=True)
    synced_at = models.DateTimeField('Synchronisé le', null=True)
    pg_ticket_number = models.CharField('Référence PG', max_length=30, blank=True)
    error_message = models.TextField('Erreur de sync', blank=True)
    retry_count = models.IntegerField('Tentatives', default=0)

    class Meta:
        app_label = 'local_sync'
        verbose_name = 'Ticket en attente'
        verbose_name_plural = 'Tickets en attente'
        ordering = ['created_at_local']

    def __str__(self):
        return f"[{self.sync_status}] {self.title[:50]}"

    def mark_synced(self, pg_ticket_number: str):
        self.sync_status = self.SYNC_SYNCED
        self.pg_ticket_number = pg_ticket_number
        from django.utils import timezone
        self.synced_at = timezone.now()
        self.save(using='pending')

    def mark_failed(self, error: str):
        self.sync_status = self.SYNC_FAILED
        self.error_message = error
        self.retry_count += 1
        # Remettre en PENDING pour réessai si moins de 5 tentatives
        if self.retry_count < 5:
            self.sync_status = self.SYNC_PENDING
        self.save(using='pending')

    def mark_cancelled(self):
        self.sync_status = self.SYNC_CANCELLED
        self.save(using='pending')


class CachedTicket(models.Model):
    """
    Snapshot local d'un ticket pour consultation hors-ligne.
    Mis à jour à chaque accès réussi à PostgreSQL.
    """

    ticket_number = models.CharField('Référence', max_length=30, unique=True)
    user_id = models.IntegerField('Propriétaire du cache')

    # Données sérialisées du ticket (JSON)
    title = models.CharField('Titre', max_length=200)
    status = models.CharField('Statut', max_length=30)
    priority = models.CharField('Priorité', max_length=5)
    created_by_name = models.CharField('Demandeur', max_length=301, blank=True)
    assigned_to_name = models.CharField('Assigné à', max_length=301, blank=True)
    department_name = models.CharField('Département', max_length=200, blank=True)
    created_at = models.DateTimeField('Créé le')
    updated_at = models.DateTimeField('Modifié le')

    # Métadonnées du cache
    cached_at = models.DateTimeField('Mis en cache le', auto_now=True)

    class Meta:
        app_label = 'local_sync'
        verbose_name = 'Ticket en cache'
        verbose_name_plural = 'Tickets en cache'
        ordering = ['-updated_at']

    def __str__(self):
        return f"[Cache] {self.ticket_number} – {self.title[:40]}"

    @classmethod
    def upsert_from_ticket(cls, ticket, user_id: int):
        """Crée ou met à jour le cache depuis un objet Ticket PostgreSQL."""
        obj, _ = cls.objects.using('cache').update_or_create(
            ticket_number=ticket.number,
            defaults={
                'user_id': user_id,
                'title': ticket.title,
                'status': ticket.status,
                'priority': ticket.priority,
                'created_by_name': ticket.created_by.get_full_name() if ticket.created_by else '',
                'assigned_to_name': ticket.assigned_to.get_full_name() if ticket.assigned_to else '',
                'department_name': ticket.department.name if ticket.department else '',
                'created_at': ticket.created_at,
                'updated_at': ticket.updated_at,
            }
        )
        return obj
