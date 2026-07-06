import os
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


ALLOWED_EXTENSIONS = {
    '.pdf', '.png', '.jpg', '.jpeg', '.gif', '.webp',
    '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.csv', '.zip', '.rar', '.7z',
}


def document_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    related_segment = 'general'

    if instance.type_gestion == Document.TypeGestion.APPLICATION and instance.application_id:
        related_segment = f'applications/{instance.application_id}'
    elif instance.type_gestion == Document.TypeGestion.ENVIRONNEMENT and instance.environnement_id:
        related_segment = f'environnements/{instance.environnement_id}'
    elif instance.type_gestion == Document.TypeGestion.SSL and instance.certificat_ssl_id:
        related_segment = f'ssl/{instance.certificat_ssl_id}'
    elif instance.type_gestion == Document.TypeGestion.DOMAINE and instance.domaine_id:
        related_segment = f'domaines/{instance.domaine_id}'

    return f'documents/{instance.type_gestion.lower()}/{related_segment}/{uuid.uuid4()}{ext}'


class Document(models.Model):
    """Document rattaché à un module de gestion ou global."""

    class TypeGestion(models.TextChoices):
        APPLICATION = 'APPLICATION', _('Application')
        ENVIRONNEMENT = 'ENVIRONNEMENT', _('Environnement')
        SSL = 'SSL', _('Certificat SSL')
        DOMAINE = 'DOMAINE', _('Domaine')
        GENERAL = 'GENERAL', _('Général')

    class Categorie(models.TextChoices):
        TECHNIQUE = 'TECHNIQUE', _('Documentation technique')
        PROCEDURE = 'PROCEDURE', _('Procédure')
        MANUEL = 'MANUEL', _('Manuel utilisateur')
        CONTRAT = 'CONTRAT', _('Contrat')
        ARCHITECTURE = 'ARCHITECTURE', _('Architecture')
        AUTRE = 'AUTRE', _('Autre')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name=_('Identifiant'),
    )
    nom = models.CharField(max_length=255, verbose_name=_('Nom'))
    type_fichier = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Type de fichier'),
        help_text=_('Extension du fichier (pdf, png, docx…).'),
    )
    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.TECHNIQUE,
        verbose_name=_('Catégorie'),
    )
    description = models.TextField(blank=True, verbose_name=_('Description'))
    date_upload = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de téléversement'))
    type_gestion = models.CharField(
        max_length=20,
        choices=TypeGestion.choices,
        default=TypeGestion.GENERAL,
        verbose_name=_('Module de gestion'),
    )
    fichier = models.FileField(
        upload_to=document_upload_path,
        verbose_name=_('Fichier'),
    )
    taille_octets = models.PositiveBigIntegerField(
        default=0,
        verbose_name=_('Taille (octets)'),
    )

    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('Application'),
    )
    environnement = models.ForeignKey(
        'environments.Environnement',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('Environnement'),
    )
    certificat_ssl = models.ForeignKey(
        'ssl.CertificatSSL',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('Certificat SSL'),
    )
    domaine = models.ForeignKey(
        'domaines.Domaine',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name=_('Domaine'),
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documents_uploaded',
        verbose_name=_('Téléversé par'),
    )

    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-date_upload']

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if self.fichier:
            ext = os.path.splitext(self.fichier.name)[1].lower().lstrip('.')
            self.type_fichier = ext or self.type_fichier
            if hasattr(self.fichier, 'size') and self.fichier.size:
                self.taille_octets = self.fichier.size
        super().save(*args, **kwargs)

    @property
    def taille_lisible(self):
        size = self.taille_octets
        for unit in ('o', 'Ko', 'Mo', 'Go'):
            if size < 1024:
                return f'{size:.0f} {unit}' if unit == 'o' else f'{size:.1f} {unit}'
            size /= 1024
        return f'{size:.1f} To'

    @property
    def icone_fichier(self):
        icons = {
            'pdf': '📄',
            'png': '🖼️',
            'jpg': '🖼️',
            'jpeg': '🖼️',
            'gif': '🖼️',
            'webp': '🖼️',
            'doc': '📝',
            'docx': '📝',
            'xls': '📊',
            'xlsx': '📊',
            'ppt': '📽️',
            'pptx': '📽️',
            'txt': '📃',
            'csv': '📊',
            'zip': '🗜️',
            'rar': '🗜️',
            '7z': '🗜️',
        }
        return icons.get(self.type_fichier.lower(), '📎')

    @property
    def preview_mode(self):
        image_types = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        text_types = {'txt', 'csv'}
        file_type = self.type_fichier.lower()

        if file_type == 'pdf':
            return 'pdf'
        if file_type in image_types:
            return 'image'
        if file_type in text_types:
            return 'text'
        return 'none'

    def get_related_label(self):
        if self.type_gestion == self.TypeGestion.APPLICATION and self.application:
            return self.application.nom
        if self.type_gestion == self.TypeGestion.ENVIRONNEMENT and self.environnement:
            return self.environnement.nom
        if self.type_gestion == self.TypeGestion.SSL and self.certificat_ssl:
            return self.certificat_ssl.domaine
        if self.type_gestion == self.TypeGestion.DOMAINE and self.domaine:
            return self.domaine.nom
        return '—'

    def get_related_url(self):
        if self.type_gestion == self.TypeGestion.APPLICATION and self.application:
            from django.urls import reverse
            return reverse('application_detail', kwargs={'pk': self.application.pk})
        if self.type_gestion == self.TypeGestion.ENVIRONNEMENT and self.environnement:
            from django.urls import reverse
            return reverse('environment_detail', kwargs={'pk': self.environnement.pk})
        if self.type_gestion == self.TypeGestion.SSL and self.certificat_ssl:
            from django.urls import reverse
            return reverse('ssl_detail', kwargs={'pk': self.certificat_ssl.pk})
        if self.type_gestion == self.TypeGestion.DOMAINE and self.domaine:
            from django.urls import reverse
            return reverse('domaine_detail', kwargs={'pk': self.domaine.pk})
        return None
