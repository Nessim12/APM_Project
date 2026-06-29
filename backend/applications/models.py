import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ApplicationQuerySet(models.QuerySet):
    """QuerySet personnalisé avec exclusion des applications archivées."""

    def actives(self):
        """Retourne les applications dont le statut n'est pas « Archivé »."""
        return self.exclude(statut=Application.StatutChoices.ARCHIVE)

    def archivees(self):
        """Retourne uniquement les applications archivées."""
        return self.filter(statut=Application.StatutChoices.ARCHIVE)

    def delete(self):
        """Interdit la suppression physique en masse — archivage logique."""
        count = 0
        for application in self:
            application.delete()
            count += 1
        return count, {self.model._meta.label: count}


class ActiveApplicationManager(models.Manager):
    """
    Gestionnaire par défaut : exclut automatiquement les applications archivées
    de toutes les requêtes standards (list, get, filter…).
    """

    def get_queryset(self):
        return ApplicationQuerySet(self.model, using=self._db).actives()


class AllApplicationManager(models.Manager):
    """Gestionnaire incluant les applications archivées (usage interne / admin)."""

    def get_queryset(self):
        return ApplicationQuerySet(self.model, using=self._db)


class Application(models.Model):
    """Entité métier représentant une application du patrimoine APM."""

    class CriticiteChoices(models.TextChoices):
        FAIBLE = 'FAIBLE', _('Faible')
        MOYENNE = 'MOYENNE', _('Moyenne')
        CRITIQUE = 'CRITIQUE', _('Critique')

    class StatutChoices(models.TextChoices):
        ACTIF = 'ACTIF', _('Actif')
        INACTIF = 'INACTIF', _('Inactif')
        ARCHIVE = 'ARCHIVE', _('Archivé')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Identifiant'),
    )
    nom = models.CharField(max_length=255, verbose_name=_('Nom'))
    description = models.TextField(verbose_name=_('Description'))
    criticite = models.CharField(
        max_length=10,
        choices=CriticiteChoices.choices,
        verbose_name=_('Criticité'),
    )
    statut = models.CharField(
        max_length=10,
        choices=StatutChoices.choices,
        default=StatutChoices.ACTIF,
        verbose_name=_('Statut'),
    )
    date_mise_en_production = models.DateField(verbose_name=_('Date de mise en production'))
    date_fin_vie = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Date de fin de vie'),
    )
    direction_metier = models.CharField(max_length=255, verbose_name=_('Direction métier'))
    nombre_utilisateurs = models.PositiveIntegerField(verbose_name=_("Nombre d'utilisateurs"))

    # Gouvernance humaine — 4 rôles pivots obligatoires
    responsable_metier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='applications_metier',
        verbose_name=_('Responsable métier'),
    )
    responsable_technique = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='applications_technique',
        verbose_name=_('Responsable technique'),
    )
    chef_de_projet = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='applications_chef_projet',
        verbose_name=_('Chef de projet'),
    )
    equipe_support = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='applications_support',
        verbose_name=_('Équipe support'),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActiveApplicationManager()
    all_objects = AllApplicationManager()

    class Meta:
        verbose_name = _('Application')
        verbose_name_plural = _('Applications')
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def archive(self):
        """Passe l'application au statut « Archivé » sans supprimer la ligne."""
        self.statut = self.StatutChoices.ARCHIVE
        self.save(update_fields=['statut', 'updated_at'])

    def delete(self, using=None, keep_parents=False):
        """
        Règle d'or : aucune suppression physique.
        Tout appel à .delete() déclenche un archivage logique.
        """
        self.archive()
