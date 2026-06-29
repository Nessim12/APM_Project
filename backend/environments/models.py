import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from applications.models import Application


class Server(models.Model):
    hostname = models.CharField(max_length=255, verbose_name=_('Nom du serveur'))
    adresse_ip = models.GenericIPAddressField(protocol='both', unpack_ipv4=True, blank=True, null=True, verbose_name=_('Adresse IP'))
    systeme_exploitation = models.CharField(max_length=100, blank=True, verbose_name=_('Système'))
    description = models.TextField(blank=True, verbose_name=_('Description'))

    class Meta:
        verbose_name = _('Serveur')
        verbose_name_plural = _('Serveurs')
        ordering = ['hostname']

    def __str__(self):
        return self.hostname


class Environnement(models.Model):
    class TypeHebergement(models.TextChoices):
        ON_PREMISE = 'ON_PREMISE', _('On-premise')
        CLOUD = 'CLOUD', _('Cloud')
        HYBRIDE = 'HYBRIDE', _('Hybride')
        AUTRE = 'AUTRE', _('Autre')

    id_environnement = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Identifiant'),
    )
    nom = models.CharField(max_length=255, verbose_name=_('Nom'))
    url = models.URLField(max_length=500, verbose_name=_('URL'))
    adresse_ip = models.GenericIPAddressField(verbose_name=_('Adresse IP'))
    os = models.CharField(max_length=100, verbose_name=_('OS'))
    cpu = models.CharField(max_length=100, verbose_name=_('CPU'))
    ram = models.CharField(max_length=100, verbose_name=_('RAM'))
    hebergeur = models.CharField(max_length=255, verbose_name=_('Hébergeur'))
    type_hebergement = models.CharField(
        max_length=20,
        choices=TypeHebergement.choices,
        verbose_name=_('Type d’hébergement'),
    )
    docker = models.BooleanField(default=False, verbose_name=_('Docker'))
    kubernetes = models.BooleanField(default=False, verbose_name=_('Kubernetes'))
    application = models.ForeignKey(
        Application,
        on_delete=models.PROTECT,
        related_name='environnements',
        verbose_name=_('Application'),
    )
    serveur = models.ForeignKey(
        Server,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='environnements',
        verbose_name=_('Serveur'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        verbose_name = _('Environnement')
        verbose_name_plural = _('Environnements')
        ordering = ['nom']

    def __str__(self):
        return self.nom
