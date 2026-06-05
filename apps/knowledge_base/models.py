from django.db import models
from django.conf import settings


class KBCategory(models.Model):
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    icon = models.CharField('Icône', max_length=50, default='bi-book')
    color = models.CharField('Couleur', max_length=30, default='primary')
    order = models.PositiveIntegerField('Ordre', default=0)

    class Meta:
        verbose_name = 'Catégorie KB'
        verbose_name_plural = 'Catégories KB'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Article(models.Model):
    TYPE_FAQ = 'FAQ'
    TYPE_PROCEDURE = 'PROCEDURE'
    TYPE_GUIDE = 'GUIDE'
    TYPE_SOLUTION = 'SOLUTION'

    TYPE_CHOICES = [
        (TYPE_FAQ, 'FAQ'),
        (TYPE_PROCEDURE, 'Procédure'),
        (TYPE_GUIDE, 'Guide utilisateur'),
        (TYPE_SOLUTION, 'Solution récurrente'),
    ]

    category = models.ForeignKey(KBCategory, on_delete=models.SET_NULL, null=True, related_name='articles')
    type = models.CharField('Type', max_length=15, choices=TYPE_CHOICES, default=TYPE_FAQ)
    title = models.CharField('Titre', max_length=300)
    content = models.TextField('Contenu')
    summary = models.TextField('Résumé', blank=True, max_length=500)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='kb_articles'
    )
    related_tickets = models.ManyToManyField(
        'tickets.Ticket', blank=True, related_name='kb_articles', verbose_name='Tickets liés'
    )
    tags = models.CharField('Tags', max_length=500, blank=True, help_text='Séparés par des virgules')
    views = models.PositiveIntegerField('Vues', default=0)
    is_published = models.BooleanField('Publié', default=True)

    # Restriction de visibilité par département (admin uniquement)
    visibility_restricted = models.BooleanField(
        'Visibilité restreinte', default=False,
        help_text='Si coché, seuls les départements sélectionnés peuvent voir cet article.'
    )
    visible_to_departments = models.ManyToManyField(
        'accounts.Department', blank=True,
        related_name='kb_articles', verbose_name='Visible par les départements'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()]

    def can_user_see(self, user):
        """Vérifie si un utilisateur peut voir cet article."""
        if not self.is_published:
            return user.role in ['ADMIN'] or self.author == user
        if not self.visibility_restricted:
            return True
        # Restreint : vérifier si le département de l'utilisateur est dans la liste
        if user.role == 'ADMIN':
            return True
        if user.department:
            return self.visible_to_departments.filter(pk=user.department.pk).exists()
        return False

    def can_user_edit(self, user):
        return user.role == 'ADMIN' or self.author == user

    def can_user_delete(self, user):
        return user.role == 'ADMIN' or self.author == user
