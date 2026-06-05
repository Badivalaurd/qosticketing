from django.db import models
from django.conf import settings


class Project(models.Model):
    STATUS_ACTIF = 'ACTIF'
    STATUS_EN_PAUSE = 'EN_PAUSE'
    STATUS_TERMINE = 'TERMINE'
    STATUS_ANNULE = 'ANNULE'

    STATUS_CHOICES = [
        (STATUS_ACTIF, 'Actif'),
        (STATUS_EN_PAUSE, 'En pause'),
        (STATUS_TERMINE, 'Terminé'),
        (STATUS_ANNULE, 'Annulé'),
    ]

    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    code = models.CharField('Code', max_length=20, unique=True)
    status = models.CharField('Statut', max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIF)
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
        related_name='managed_projects', verbose_name='Responsable'
    )
    team = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True,
        related_name='projects', verbose_name='Équipe'
    )
    start_date = models.DateField('Date début', null=True, blank=True)
    end_date = models.DateField('Date fin prévue', null=True, blank=True)
    department = models.ForeignKey(
        'accounts.Department', null=True, blank=True, on_delete=models.SET_NULL,
        verbose_name='Direction'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Projet'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def completion_percent(self):
        total = self.user_stories.count()
        if not total:
            return 0
        done = self.user_stories.filter(status='DONE').count()
        return int(done * 100 / total)


class Sprint(models.Model):
    STATUS_PLANIFIE = 'PLANIFIE'
    STATUS_ACTIF = 'ACTIF'
    STATUS_TERMINE = 'TERMINE'

    STATUS_CHOICES = [
        (STATUS_PLANIFIE, 'Planifié'),
        (STATUS_ACTIF, 'Actif'),
        (STATUS_TERMINE, 'Terminé'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    name = models.CharField('Nom', max_length=100)
    goal = models.TextField('Objectif', blank=True)
    status = models.CharField('Statut', max_length=15, choices=STATUS_CHOICES, default=STATUS_PLANIFIE)
    start_date = models.DateField('Début', null=True, blank=True)
    end_date = models.DateField('Fin', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sprint'
        ordering = ['project', 'start_date']

    def __str__(self):
        return f"{self.project} - {self.name}"


class Epic(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='epics')
    name = models.CharField('Nom', max_length=200)
    description = models.TextField('Description', blank=True)
    color = models.CharField('Couleur', max_length=7, default='#6366f1')
    start_date = models.DateField('Début', null=True, blank=True)
    end_date = models.DateField('Fin', null=True, blank=True)

    class Meta:
        verbose_name = 'Epic'
        ordering = ['project', 'name']

    def __str__(self):
        return f"{self.project} > {self.name}"


class UserStory(models.Model):
    STATUS_BACKLOG = 'BACKLOG'
    STATUS_TODO = 'TODO'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_IN_TEST = 'IN_TEST'
    STATUS_DONE = 'DONE'

    STATUS_CHOICES = [
        (STATUS_BACKLOG, 'Backlog'),
        (STATUS_TODO, 'À faire'),
        (STATUS_IN_PROGRESS, 'En cours'),
        (STATUS_IN_TEST, 'En test'),
        (STATUS_DONE, 'Terminé'),
    ]

    KANBAN_COLUMNS = {
        STATUS_BACKLOG: 'Backlog',
        STATUS_TODO: 'À faire',
        STATUS_IN_PROGRESS: 'En cours',
        STATUS_IN_TEST: 'En test',
        STATUS_DONE: 'Terminé',
    }

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='user_stories')
    epic = models.ForeignKey(Epic, null=True, blank=True, on_delete=models.SET_NULL, related_name='user_stories')
    sprint = models.ForeignKey(Sprint, null=True, blank=True, on_delete=models.SET_NULL, related_name='user_stories')
    title = models.CharField('Titre', max_length=500)
    description = models.TextField('Description', blank=True)
    acceptance_criteria = models.TextField('Critères d\'acceptation', blank=True)
    status = models.CharField('Statut', max_length=15, choices=STATUS_CHOICES, default=STATUS_BACKLOG)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='user_stories', verbose_name='Assigné à'
    )
    story_points = models.PositiveIntegerField('Points', default=0)
    priority = models.PositiveIntegerField('Priorité', default=0)
    order = models.PositiveIntegerField('Ordre', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Story'
        verbose_name_plural = 'User Stories'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Task(models.Model):
    STATUS_TODO = 'TODO'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_DONE = 'DONE'

    STATUS_CHOICES = [
        (STATUS_TODO, 'À faire'),
        (STATUS_IN_PROGRESS, 'En cours'),
        (STATUS_DONE, 'Terminé'),
    ]

    story = models.ForeignKey(UserStory, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField('Titre', max_length=300)
    description = models.TextField('Description', blank=True)
    status = models.CharField('Statut', max_length=15, choices=STATUS_CHOICES, default=STATUS_TODO)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='tasks'
    )
    estimated_hours = models.DecimalField('Heures estimées', max_digits=6, decimal_places=2, default=0)
    actual_hours = models.DecimalField('Heures réelles', max_digits=6, decimal_places=2, default=0)
    due_date = models.DateField('Échéance', null=True, blank=True)
    order = models.PositiveIntegerField('Ordre', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Tâche'
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title
