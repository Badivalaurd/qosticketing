from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class SLAConfig(models.Model):
    """Configuration SLA par priorité — modifiable par l'admin."""
    P0 = 'P0'
    P1 = 'P1'
    P2 = 'P2'
    P3 = 'P3'

    PRIORITY_CHOICES = [
        (P0, 'P0 - Critique'),
        (P1, 'P1 - Haute'),
        (P2, 'P2 - Moyenne'),
        (P3, 'P3 - Faible'),
    ]

    DEFAULTS = {
        P0: {'response': 10,  'resolution': 120},
        P1: {'response': 30,  'resolution': 240},
        P2: {'response': 120, 'resolution': 1440},
        P3: {'response': 240, 'resolution': 2880},
    }

    priority = models.CharField('Priorité', max_length=5, choices=PRIORITY_CHOICES, unique=True)
    response_time_minutes = models.PositiveIntegerField(
        'Délai prise en charge (min)',
        default=30,
        help_text='Temps maximal avant la première prise en charge.'
    )
    resolution_time_minutes = models.PositiveIntegerField(
        'Délai de traitement (min)',
        default=480,
        help_text='Temps maximal avant résolution.'
    )

    class Meta:
        verbose_name = 'Configuration SLA'
        verbose_name_plural = 'Configurations SLA'
        ordering = ['priority']

    def __str__(self):
        return f"{self.get_priority_display()} — Prise en charge: {self.response_time_minutes}min, Traitement: {self.resolution_time_minutes}min"

    @classmethod
    def get_for_priority(cls, priority):
        try:
            return cls.objects.get(priority=priority)
        except cls.DoesNotExist:
            defaults = cls.DEFAULTS.get(priority, {'response': 60, 'resolution': 480})
            return type('SLADefault', (), {
                'response_time_minutes': defaults['response'],
                'resolution_time_minutes': defaults['resolution'],
            })()


class Application(models.Model):
    name = models.CharField('Nom', max_length=200)
    code = models.CharField('Code', max_length=30, unique=True)
    description = models.TextField('Description', blank=True)
    department = models.ForeignKey(
        'accounts.Department', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='applications', verbose_name='Département propriétaire'
    )
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Application'
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    INCIDENT = 'INCIDENT'
    EVOLUTION = 'EVOLUTION'
    SUPPORT = 'SUPPORT'
    PONCTUEL = 'PONCTUEL'
    TACHE_PROJET = 'TACHE_PROJET'

    TYPE_CHOICES = [
        (INCIDENT, 'Incident'),
        (EVOLUTION, "Demande d'Évolution"),
        (SUPPORT, 'Support Fonctionnel'),
        (PONCTUEL, 'Demande Ponctuelle'),
        (TACHE_PROJET, 'Tâche Projet'),
    ]

    type = models.CharField('Type', max_length=20, choices=TYPE_CHOICES, unique=True)
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    icon = models.CharField('Icône Bootstrap', max_length=50, default='bi-ticket')
    color = models.CharField('Couleur CSS', max_length=30, default='primary')
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'

    def __str__(self):
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    is_active = models.BooleanField('Actif', default=True)

    class Meta:
        verbose_name = 'Sous-catégorie'
        verbose_name_plural = 'Sous-catégories'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category} > {self.name}"


class Ticket(models.Model):
    # ---- Priorités P0→P3 ----
    PRIORITY_P0 = 'P0'
    PRIORITY_P1 = 'P1'
    PRIORITY_P2 = 'P2'
    PRIORITY_P3 = 'P3'

    PRIORITY_CHOICES = [
        (PRIORITY_P0, 'P0 - Critique'),
        (PRIORITY_P1, 'P1 - Haute'),
        (PRIORITY_P2, 'P2 - Moyenne'),
        (PRIORITY_P3, 'P3 - Faible'),
    ]

    PRIORITY_COLORS = {
        PRIORITY_P0: 'danger',
        PRIORITY_P1: 'warning',
        PRIORITY_P2: 'info',
        PRIORITY_P3: 'secondary',
    }

    # ---- Statuts ----
    STATUS_NOUVEAU = 'NOUVEAU'
    STATUS_AFFECTE = 'AFFECTE'
    STATUS_EN_COURS = 'EN_COURS'
    STATUS_ATTENTE_INFO = 'ATTENTE_INFO'
    STATUS_ATTENTE_PRESTATAIRE = 'ATTENTE_PRESTATAIRE'
    STATUS_RESOLU = 'RESOLU'
    STATUS_CLOTURE = 'CLOTURE'
    STATUS_REJETE = 'REJETE'
    STATUS_ANNULE = 'ANNULE'

    STATUS_CHOICES = [
        (STATUS_NOUVEAU, 'Nouveau'),
        (STATUS_AFFECTE, 'Affecté'),
        (STATUS_EN_COURS, 'En cours'),
        (STATUS_ATTENTE_INFO, "En attente d'information"),
        (STATUS_ATTENTE_PRESTATAIRE, 'En attente prestataire'),
        (STATUS_RESOLU, 'Résolu'),
        (STATUS_CLOTURE, 'Clôturé'),
        (STATUS_REJETE, 'Rejeté'),
        (STATUS_ANNULE, 'Annulé'),
    ]

    # Statuts qui mettent le SLA en pause
    SLA_PAUSE_STATUSES = [STATUS_ATTENTE_INFO, STATUS_ATTENTE_PRESTATAIRE]
    # Statuts terminaux (SLA s'arrête)
    SLA_STOP_STATUSES = [STATUS_RESOLU, STATUS_CLOTURE, STATUS_REJETE, STATUS_ANNULE]
    # Statuts qui verrouillent totalement le ticket (aucune modification possible, même pour l'admin)
    LOCKED_STATUSES = [STATUS_ANNULE, STATUS_CLOTURE]

    STATUS_COLORS = {
        STATUS_NOUVEAU: 'secondary',
        STATUS_AFFECTE: 'info',
        STATUS_EN_COURS: 'primary',
        STATUS_ATTENTE_INFO: 'warning',
        STATUS_ATTENTE_PRESTATAIRE: 'warning',
        STATUS_RESOLU: 'success',
        STATUS_CLOTURE: 'dark',
        STATUS_REJETE: 'danger',
        STATUS_ANNULE: 'secondary',
    }

    # ---- Identifiant ----
    number = models.CharField('Numéro', max_length=20, unique=True, editable=False)

    # ---- Informations générales ----
    title = models.CharField('Titre', max_length=500)
    description = models.TextField('Description')
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name='tickets', verbose_name='Catégorie'
    )
    sub_category = models.ForeignKey(
        SubCategory, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tickets', verbose_name='Sous-catégorie'
    )
    application = models.ForeignKey(
        Application, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tickets', verbose_name='Application'
    )
    department = models.ForeignKey(
        'accounts.Department', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tickets', verbose_name='Département'
    )
    # Département cible (si le demandeur envoie vers un dept spécifique)
    target_department = models.ForeignKey(
        'accounts.Department', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='targeted_tickets', verbose_name='Département cible'
    )
    priority = models.CharField('Priorité', max_length=5, choices=PRIORITY_CHOICES, default=PRIORITY_P2)
    status = models.CharField('Statut', max_length=25, choices=STATUS_CHOICES, default=STATUS_NOUVEAU)

    # ---- Acteurs ----
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='created_tickets', verbose_name='Demandeur'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='assigned_tickets', verbose_name='Assigné à'
    )
    # Personne à qui on a demandé une info (visibilité temporaire cross-dept)
    info_requested_from = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='info_requested_tickets', verbose_name='Demande d\'info à'
    )

    # ---- Dates ----
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Mis à jour le', auto_now=True)
    assigned_at = models.DateTimeField('Pris en charge le', null=True, blank=True)
    resolved_at = models.DateTimeField('Résolu le', null=True, blank=True)
    closed_at = models.DateTimeField('Clôturé le', null=True, blank=True)

    # ---- SLA ----
    sla_response_deadline = models.DateTimeField('Échéance prise en charge', null=True, blank=True)
    sla_resolution_deadline = models.DateTimeField('Échéance traitement', null=True, blank=True)
    sla_response_exceeded = models.BooleanField('Prise en charge hors délai', default=False)
    sla_resolution_exceeded = models.BooleanField('Traitement hors délai', default=False)
    resolved_out_of_sla = models.BooleanField('Résolu hors SLA', default=False)
    sla_paused_at = models.DateTimeField('SLA mis en pause le', null=True, blank=True)
    sla_pause_minutes = models.PositiveIntegerField('Minutes de pause SLA accumulées', default=0)

    # ---- Alertes SLA (suivi des envois) ----
    sla_warning_1h_sent = models.BooleanField('Alerte SLA 1h envoyée', default=False)
    sla_warning_30m_sent = models.BooleanField('Alerte SLA 30min envoyée', default=False)
    sla_warning_10m_sent = models.BooleanField('Alerte SLA 10min envoyée', default=False)

    # ---- Rejet / Annulation ----
    rejection_reason = models.TextField('Motif de rejet', blank=True)

    # ---- Lié à un projet ----
    project = models.ForeignKey(
        'projects.Project', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tickets', verbose_name='Projet'
    )

    class Meta:
        verbose_name = 'Ticket'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.number}] {self.title}"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if not self.number:
            self.number = self._generate_number()
        if is_new and self.priority:
            self._init_sla()
        super().save(*args, **kwargs)

    def _generate_number(self):
        from django.db.models import Max
        year = timezone.now().year
        dept_code = 'GEN'
        if self.created_by and self.created_by.department:
            dept_code = self.created_by.department.code
        prefix = f"OMCM-{dept_code}-"
        last = Ticket.objects.filter(number__startswith=prefix).aggregate(Max('number'))['number__max']
        if last:
            try:
                seq = int(last.split('-')[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:05d}"

    def _init_sla(self):
        sla = SLAConfig.get_for_priority(self.priority)
        now = timezone.now()
        self.sla_response_deadline = now + timedelta(minutes=sla.response_time_minutes)
        self.sla_resolution_deadline = now + timedelta(minutes=sla.resolution_time_minutes)

    def reset_sla_for_priority(self, new_priority):
        """Réinitialise les SLA selon la nouvelle priorité (depuis maintenant)."""
        self.priority = new_priority
        sla = SLAConfig.get_for_priority(new_priority)
        now = timezone.now()
        self.sla_response_deadline = now + timedelta(minutes=sla.response_time_minutes)
        self.sla_resolution_deadline = now + timedelta(minutes=sla.resolution_time_minutes)
        self.sla_response_exceeded = False
        self.sla_resolution_exceeded = False
        self.resolved_out_of_sla = False
        self.sla_paused_at = None
        self.sla_pause_minutes = 0
        self.sla_warning_1h_sent = False
        self.sla_warning_30m_sent = False
        self.sla_warning_10m_sent = False

    def reset_sla_on_assign(self):
        """
        Réinitialise le SLA depuis le moment de l'affectation.
        Appelé automatiquement à chaque affectation/réaffectation (logique JIRA).
        """
        self.reset_sla_for_priority(self.priority)
        self.assigned_at = timezone.now()

    # ---- SLA helpers ----
    def pause_sla(self):
        """Appeler quand le ticket entre en ATTENTE_INFO ou ATTENTE_PRESTATAIRE."""
        if not self.sla_paused_at:
            self.sla_paused_at = timezone.now()

    def resume_sla(self):
        """Appeler quand le ticket sort d'un état de pause."""
        if self.sla_paused_at:
            pause_duration = timezone.now() - self.sla_paused_at
            minutes = int(pause_duration.total_seconds() / 60)
            self.sla_pause_minutes += minutes
            if self.sla_response_deadline:
                self.sla_response_deadline += pause_duration
            if self.sla_resolution_deadline:
                self.sla_resolution_deadline += pause_duration
            self.sla_paused_at = None

    def check_and_update_sla(self):
        """Vérifie les dépassements SLA. Retourne True si SLA mis à jour."""
        now = timezone.now()
        changed = False
        if (self.sla_response_deadline and not self.sla_response_exceeded and
                self.status not in [self.STATUS_NOUVEAU] and now > self.sla_response_deadline):
            self.sla_response_exceeded = True
            changed = True
        if (self.sla_resolution_deadline and not self.sla_resolution_exceeded and
                self.status in self.SLA_STOP_STATUSES and now > self.sla_resolution_deadline):
            self.sla_resolution_exceeded = True
            if self.status == self.STATUS_RESOLU:
                self.resolved_out_of_sla = True
            changed = True
        return changed

    @property
    def status_color(self):
        return self.STATUS_COLORS.get(self.status, 'secondary')

    @property
    def priority_color(self):
        return self.PRIORITY_COLORS.get(self.priority, 'secondary')

    @property
    def is_locked(self):
        """True si le ticket est verrouillé — aucune modification permise, même pour l'admin."""
        return self.status in self.LOCKED_STATUSES

    @property
    def is_sla_paused(self):
        return self.sla_paused_at is not None

    @property
    def is_response_overdue(self):
        if self.sla_response_exceeded:
            return True
        if (self.sla_response_deadline and not self.assigned_at and
                self.status not in self.SLA_STOP_STATUSES and not self.is_sla_paused):
            return timezone.now() > self.sla_response_deadline
        return False

    @property
    def is_resolution_overdue(self):
        if self.sla_resolution_exceeded:
            return True
        if (self.sla_resolution_deadline and
                self.status not in self.SLA_STOP_STATUSES and not self.is_sla_paused):
            return timezone.now() > self.sla_resolution_deadline
        return False

    @property
    def is_overdue(self):
        return self.is_response_overdue or self.is_resolution_overdue

    @property
    def response_sla_percent(self):
        """Pourcentage du temps SLA prise en charge écoulé (0-100+)."""
        if not self.sla_response_deadline or self.assigned_at:
            return None
        sla = SLAConfig.get_for_priority(self.priority)
        total = sla.response_time_minutes * 60
        if total == 0:
            return 100
        elapsed = (timezone.now() - self.created_at).total_seconds()
        return min(int(elapsed * 100 / total), 150)

    @property
    def resolution_sla_percent(self):
        """Pourcentage du temps SLA traitement écoulé (0-100+)."""
        if not self.sla_resolution_deadline or self.status in self.SLA_STOP_STATUSES:
            return None
        sla = SLAConfig.get_for_priority(self.priority)
        total = sla.resolution_time_minutes * 60
        if total == 0:
            return 100
        elapsed = (timezone.now() - self.created_at).total_seconds() - (self.sla_pause_minutes * 60)
        return min(int(elapsed * 100 / total), 150)

    @property
    def processing_time(self):
        end = self.resolved_at or self.closed_at or timezone.now()
        return int((end - self.created_at).total_seconds() / 3600)

    def get_allowed_transitions(self, user):
        """Retourne les statuts vers lesquels l'utilisateur peut faire évoluer ce ticket."""
        from apps.accounts.models import User as U

        # Statuts terminaux : personne ne peut rien faire
        if self.status in [self.STATUS_CLOTURE, self.STATUS_REJETE, self.STATUS_ANNULE]:
            return []

        role = user.role

        # OBSERVATEUR : aucune action
        if role == U.ROLE_OBSERVATEUR:
            return []

        # DEMANDEUR : annuler si NOUVEAU et son ticket, réouvrir si RESOLU et son ticket
        if role == U.ROLE_DEMANDEUR:
            if self.status == self.STATUS_NOUVEAU and self.created_by == user:
                return [self.STATUS_ANNULE]
            if self.status == self.STATUS_RESOLU and self.created_by == user:
                return [self.STATUS_NOUVEAU]
            return []

        # AGENT : uniquement rejeter un NOUVEAU et clôturer un RESOLU
        if role == U.ROLE_AGENT:
            if self.status == self.STATUS_NOUVEAU:
                return [self.STATUS_REJETE]
            if self.status == self.STATUS_RESOLU:
                return [self.STATUS_CLOTURE]
            return []

        # TECHNICIEN : actions sur les tickets en cours de traitement
        if role == U.ROLE_TECHNICIEN:
            # Peut prendre en charge (AFFECTE → EN_COURS) si assigné à lui OU même département
            if self.status == self.STATUS_AFFECTE:
                same_dept = (
                    self.assigned_to and
                    user.department and
                    self.assigned_to.department == user.department
                )
                if self.assigned_to == user or same_dept:
                    return [self.STATUS_EN_COURS]
                return []
            # En cours et au-delà : uniquement le technicien assigné
            if self.assigned_to != user:
                return []
            transitions_tech = {
                self.STATUS_EN_COURS: [
                    self.STATUS_ATTENTE_INFO,
                    self.STATUS_ATTENTE_PRESTATAIRE,
                    self.STATUS_RESOLU,
                ],
                self.STATUS_ATTENTE_INFO: [self.STATUS_EN_COURS],
                self.STATUS_ATTENTE_PRESTATAIRE: [self.STATUS_EN_COURS],
            }
            return transitions_tech.get(self.status, [])

        # MANAGER : gestion de son département
        if role == U.ROLE_MANAGER:
            is_my_dept = (
                self.target_department == user.department or
                self.department == user.department
            )
            if not is_my_dept:
                return []
            transitions_mgr = {
                self.STATUS_NOUVEAU: [self.STATUS_AFFECTE, self.STATUS_REJETE],
                self.STATUS_AFFECTE: [self.STATUS_EN_COURS],
                self.STATUS_EN_COURS: [self.STATUS_ATTENTE_INFO, self.STATUS_RESOLU],
                self.STATUS_ATTENTE_INFO: [self.STATUS_EN_COURS],
                self.STATUS_RESOLU: [self.STATUS_CLOTURE],
            }
            return transitions_mgr.get(self.status, [])

        # ADMIN : tout sauf réouvrir (seul le demandeur peut) et rien sur CLOTURE
        if role == U.ROLE_ADMIN:
            transitions_admin = {
                self.STATUS_NOUVEAU: [self.STATUS_AFFECTE, self.STATUS_REJETE, self.STATUS_ANNULE],
                self.STATUS_AFFECTE: [self.STATUS_EN_COURS, self.STATUS_REJETE],
                self.STATUS_EN_COURS: [
                    self.STATUS_ATTENTE_INFO,
                    self.STATUS_ATTENTE_PRESTATAIRE,
                    self.STATUS_RESOLU,
                ],
                self.STATUS_ATTENTE_INFO: [self.STATUS_EN_COURS, self.STATUS_RESOLU],
                self.STATUS_ATTENTE_PRESTATAIRE: [self.STATUS_EN_COURS, self.STATUS_RESOLU],
                # Admin peut clôturer mais PAS réouvrir (seul le demandeur peut)
                self.STATUS_RESOLU: [self.STATUS_CLOTURE],
            }
            return transitions_admin.get(self.status, [])

        return []

    def can_user_reassign(self, user):
        """L'admin peut réaffecter sauf si le ticket est résolu ou clôturé."""
        from apps.accounts.models import User as U
        if user.role == U.ROLE_ADMIN:
            return self.status not in [self.STATUS_RESOLU, self.STATUS_CLOTURE, self.STATUS_REJETE, self.STATUS_ANNULE]
        if user.role == U.ROLE_AGENT:
            return self.status == self.STATUS_NOUVEAU
        if user.role == U.ROLE_MANAGER:
            return self.status in [self.STATUS_NOUVEAU, self.STATUS_AFFECTE]
        return False

    def can_user_see(self, user):
        """Vérifie si un utilisateur a le droit de voir ce ticket."""
        from apps.accounts.models import User as U
        # Admin, Agent, Technicien : vue globale
        if user.role in [U.ROLE_ADMIN, U.ROLE_AGENT, U.ROLE_TECHNICIEN]:
            return True
        # Observateur IT : vue globale ; sinon son dept
        if user.role == U.ROLE_OBSERVATEUR:
            if user.is_it_member:
                return True
            return self.department == user.department
        # Manager : son département
        if user.role == U.ROLE_MANAGER:
            return self.target_department == user.department or self.department == user.department
        # Demandeur : tickets de son département
        if user.role == U.ROLE_DEMANDEUR:
            return self.created_by.department == user.department
        # Visibilité temporaire pour demande d'info
        if self.info_requested_from == user and self.status == self.STATUS_ATTENTE_INFO:
            return True
        return False


class TicketHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='history')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField('Action', max_length=200)
    field_name = models.CharField('Champ', max_length=100, blank=True)
    old_value = models.TextField('Ancienne valeur', blank=True)
    new_value = models.TextField('Nouvelle valeur', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Historique'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket.number} - {self.action}"


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    content = models.TextField('Contenu')
    is_internal = models.BooleanField('Commentaire interne', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Commentaire'
        ordering = ['created_at']

    def __str__(self):
        return f"Commentaire de {self.author} sur {self.ticket.number}"


def ticket_attachment_path(instance, filename):
    return f"attachments/{instance.ticket.number}/{filename}"


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField('Fichier', upload_to=ticket_attachment_path)
    filename = models.CharField('Nom du fichier', max_length=255)
    file_size = models.PositiveBigIntegerField('Taille', default=0)
    content_type = models.CharField('Type MIME', max_length=100, blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Pièce jointe'
        verbose_name_plural = 'Pièces jointes'

    def __str__(self):
        return self.filename

    @property
    def size_display(self):
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        return f"{self.file_size / (1024 * 1024):.1f} MB"
