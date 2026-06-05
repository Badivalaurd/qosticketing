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
    is_active = models.BooleanField('Actif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['name']

    def __str__(self):
        return self.name


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
    def avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return None


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
