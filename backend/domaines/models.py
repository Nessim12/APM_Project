from django.db import models
from django.utils.translation import gettext_lazy as _


class Domaine(models.Model):
    nom = models.CharField(max_length=255, verbose_name=_('Nom de domaine'))
    registrar = models.CharField(max_length=255, verbose_name=_('Registrar'))
    dns = models.CharField(max_length=255, verbose_name=_('DNS'))
    responsable = models.CharField(max_length=255, verbose_name=_('Responsable'))
    date_achat = models.DateField(verbose_name=_('Date d’achat'))
    date_expiration = models.DateField(verbose_name=_('Date d’expiration'))
    renouvellement_auto = models.BooleanField(default=False, verbose_name=_('Renouvellement automatique'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        verbose_name = _('Domaine')
        verbose_name_plural = _('Domaines')
        ordering = ['nom']

    def __str__(self):
        return self.nom
