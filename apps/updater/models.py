"""
Gestion des versions et mises à jour de l'application desktop.
Stocké dans PostgreSQL (accessible par tous).
"""
from django.db import models


class AppVersion(models.Model):
    """Catalogue des versions publiées par l'administrateur."""

    version = models.CharField('Version', max_length=20)
    release_notes = models.TextField('Notes de version', blank=True)
    download_url = models.URLField(
        'URL de téléchargement',
        help_text='Lien SharePoint vers le nouvel exécutable.'
    )
    min_required_version = models.CharField(
        'Version minimale requise', max_length=20,
        help_text='Les clients dont la version est inférieure seront bloqués.'
    )
    is_forced = models.BooleanField(
        'Mise à jour forcée', default=True,
        help_text='Si activé, les anciens clients ne peuvent plus utiliser l\'app.'
    )
    released_at = models.DateTimeField('Publiée le', auto_now_add=True)
    released_by = models.ForeignKey(
        'accounts.User', null=True, on_delete=models.SET_NULL,
        related_name='app_versions', verbose_name='Publié par'
    )

    class Meta:
        verbose_name = 'Version applicative'
        verbose_name_plural = 'Versions applicatives'
        ordering = ['-released_at']

    def __str__(self):
        return f"v{self.version} ({'forcée' if self.is_forced else 'optionnelle'})"

    @classmethod
    def get_latest(cls):
        return cls.objects.order_by('-released_at').first()

    def requires_update(self, current_version: str) -> bool:
        """True si current_version < min_required_version."""
        return self._parse(current_version) < self._parse(self.min_required_version)

    @staticmethod
    def _parse(version: str) -> tuple:
        try:
            return tuple(int(x) for x in version.split('.'))
        except (ValueError, AttributeError):
            return (0,)
