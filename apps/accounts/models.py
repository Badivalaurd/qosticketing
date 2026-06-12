from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    name = models.CharField('Nom', max_length=200)
    code = models.CharField('Code', max_length=20, unique=True)
    description = models.TextField('Description', blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    is_it_department = models.BooleanField(
        'Département Informatique',
        default=False,
        help_text='Les membres de ce département ont une vue globale sur tous les tickets.'
    )
    ticketing_enabled = models.BooleanField(
        'Ticketing activé',
        default=False,
        help_text=(
            'Ce département peut recevoir des tickets depuis d\'autres départements. '
            'Activez uniquement après accord contractuel. '
            'Le département Informatique est toujours actif par défaut.'
        )
    )
    manager = models.ForeignKey(
        'User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='managed_department',
        verbose_name='Manager ticketing',
        help_text='Responsable de la distribution des tickets dans ce département (hors IT).'
    )
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def accepts_tickets(self):
        """Vrai si ce département peut recevoir des tickets (IT toujours, autres si activés)."""
        return self.is_it_department or self.ticketing_enabled


class User(AbstractUser):
    ROLE_ADMIN = 'ADMIN'
    ROLE_MANAGER = 'MANAGER'
    ROLE_AGENT = 'AGENT'
    ROLE_TECHNICIEN = 'TECHNICIEN'
    ROLE_DEMANDEUR = 'DEMANDEUR'
    ROLE_OBSERVATEUR = 'OBSERVATEUR'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrateur'),
        (ROLE_MANAGER, 'Manager'),
        (ROLE_AGENT, 'Agent de Support'),
        (ROLE_TECHNICIEN, 'Technicien'),
        (ROLE_DEMANDEUR, 'Demandeur'),
        (ROLE_OBSERVATEUR, 'Observateur'),
    ]

    role = models.CharField('Rôle', max_length=20, choices=ROLE_CHOICES, default=ROLE_DEMANDEUR)
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='users', verbose_name='Département'
    )
    phone = models.CharField('Téléphone', max_length=30, blank=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', null=True, blank=True)
    bio = models.TextField('Biographie', blank=True)
    is_active = models.BooleanField('Actif', default=True)
    is_project_manager = models.BooleanField(
        'Chef de projet IT', default=False,
        help_text='Permet de créer et piloter des projets (en plus du rôle principal).'
    )

    # ── Confirmation email à l'inscription ──────────────────────────
    email_confirm_code = models.CharField(
        'Code de confirmation', max_length=8, blank=True
    )
    email_confirm_sent_at = models.DateTimeField(
        'Code envoyé le', null=True, blank=True
    )

    # ── Réinitialisation de mot de passe par code ────────────────────
    pwd_reset_code = models.CharField(
        'Code reset MDP', max_length=8, blank=True
    )
    pwd_reset_sent_at = models.DateTimeField(
        'Code reset envoyé le', null=True, blank=True
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Role shortcuts ---
    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def is_manager(self):
        return self.role == self.ROLE_MANAGER

    @property
    def is_agent(self):
        return self.role == self.ROLE_AGENT

    @property
    def is_technicien(self):
        return self.role == self.ROLE_TECHNICIEN

    @property
    def is_demandeur(self):
        return self.role == self.ROLE_DEMANDEUR

    @property
    def is_observateur(self):
        return self.role == self.ROLE_OBSERVATEUR

    @property
    def is_it_member(self):
        """True if user belongs to the IT department (global visibility)."""
        return bool(self.department and self.department.is_it_department)

    @property
    def has_global_view(self):
        """Admin, Agent, Technicien always have global view; Observateur only if in IT dept."""
        if self.role in [self.ROLE_ADMIN, self.ROLE_AGENT, self.ROLE_TECHNICIEN]:
            return True
        if self.role == self.ROLE_OBSERVATEUR:
            return self.is_it_member
        return False

    @property
    def can_process_tickets(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_AGENT, self.ROLE_TECHNICIEN]

    @property
    def can_manage_projects(self):
        """Chef de projet IT ou Manager IT : crée projets, sprints, livrables."""
        return self.is_it_member and (
            self.is_project_manager or
            self.role in [self.ROLE_ADMIN, self.ROLE_MANAGER]
        )

    @property
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


class AuthorizedEmployee(models.Model):
    """
    Base des CUIDs autorisés à s'inscrire, chargée par l'admin via fichier Excel.
    Colonnes Excel : CUID | Statut | Département
    """
    STATUS_PERMANENT   = 'permanent'
    STATUS_INTERIMAIRE = 'interimaire'
    STATUS_STAGIAIRE   = 'stagiaire'
    STATUS_TEMPORAIRE  = 'temporaire'

    STATUS_CHOICES = [
        (STATUS_PERMANENT,   'Permanent'),
        (STATUS_INTERIMAIRE, 'Intérimaire'),
        (STATUS_STAGIAIRE,   'Stagiaire'),
        (STATUS_TEMPORAIRE,  'Temporaire'),
    ]

    cuid = models.CharField('CUID', max_length=50, unique=True)
    employee_status = models.CharField(
        'Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_PERMANENT
    )
    department = models.ForeignKey(
        Department, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='authorized_employees', verbose_name='Département'
    )
    is_registered = models.BooleanField('Inscrit', default=False)
    registered_user = models.OneToOneField(
        'User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='authorized_employee', verbose_name='Utilisateur'
    )
    uploaded_at = models.DateTimeField('Chargé le', auto_now_add=True)

    class Meta:
        verbose_name = 'Employé autorisé'
        verbose_name_plural = 'Employés autorisés'
        ordering = ['cuid']

    def __str__(self):
        status = self.get_employee_status_display()
        dept = self.department.name if self.department else '—'
        flag = 'inscrit' if self.is_registered else 'disponible'
        return f"{self.cuid} · {status} · {dept} ({flag})"


class AuditLog(models.Model):
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    ACTION_VIEW = 'VIEW'

    ACTION_CHOICES = [
        (ACTION_CREATE, 'Création'),
        (ACTION_UPDATE, 'Modification'),
        (ACTION_DELETE, 'Suppression'),
        (ACTION_LOGIN, 'Connexion'),
        (ACTION_LOGOUT, 'Déconnexion'),
        (ACTION_VIEW, 'Consultation'),
    ]

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField('Action', max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField('Modèle', max_length=100, blank=True)
    object_id = models.CharField('ID Objet', max_length=100, blank=True)
    object_repr = models.CharField('Représentation', max_length=500, blank=True)
    details = models.TextField('Détails', blank=True)
    ip_address = models.GenericIPAddressField('Adresse IP', null=True, blank=True)
    user_agent = models.CharField('User Agent', max_length=500, blank=True)
    created_at = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.created_at}"
