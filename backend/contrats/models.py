import uuid
from datetime import date

from django.db import models
from django.utils.translation import gettext_lazy as _

from applications.models import Application


class Fournisseur(models.Model):
    nom = models.CharField(max_length=255, verbose_name=_('Nom du fournisseur'))
    email = models.EmailField(blank=True, verbose_name=_('Email'))
    telephone = models.CharField(max_length=30, blank=True, verbose_name=_('Téléphone'))
    adresse = models.CharField(max_length=255, blank=True, verbose_name=_('Adresse'))
    site_web = models.URLField(blank=True, verbose_name=_('Site web'))
    responsable = models.CharField(max_length=255, blank=True, verbose_name=_('Responsable'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        verbose_name = _('Fournisseur')
        verbose_name_plural = _('Fournisseurs')
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Contract(models.Model):
    class ContractTypeChoices(models.TextChoices):
        MAINTENANCE = 'MAINTENANCE', _('Maintenance')
        SUPPORT = 'SUPPORT', _('Support')
        GARANTIE = 'GARANTIE', _('Garantie')
        RENOUVELLEMENT = 'RENOUVELLEMENT', _('Renouvellement')

    class StatutChoices(models.TextChoices):
        ACTIF = 'ACTIF', _('Actif')
        EN_ATTENTE = 'EN_ATTENTE', _('En attente')
        EXPIRE = 'EXPIRE', _('Expiré')

    # Icônes et couleurs par type — utilisées dans les templates
    TYPE_META = {
        'MAINTENANCE':   {'icon': '🔧', 'color': '#3b82f6', 'bg': 'rgba(59,130,246,0.12)'},
        'SUPPORT':       {'icon': '🎧', 'color': '#8b5cf6', 'bg': 'rgba(139,92,246,0.12)'},
        'GARANTIE':      {'icon': '🛡️', 'color': '#10b981', 'bg': 'rgba(16,185,129,0.12)'},
        'RENOUVELLEMENT':{'icon': '🔄', 'color': '#f59e0b', 'bg': 'rgba(245,158,11,0.12)'},
    }

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        verbose_name=_('Identifiant'),
    )
    numero_contrat = models.CharField(
        max_length=120, unique=True,
        verbose_name=_('Numéro de contrat'),
    )
    contract_type = models.CharField(
        max_length=20, choices=ContractTypeChoices.choices,
        verbose_name=_('Type de contrat'),
    )
    date_debut = models.DateField(verbose_name=_('Date de début'))
    date_fin = models.DateField(verbose_name=_('Date de fin'))
    cout_annuel = models.DecimalField(
        max_digits=14, decimal_places=2,
        verbose_name=_('Coût annuel'),
    )
    sla = models.CharField(max_length=255, verbose_name=_('SLA'))
    statut = models.CharField(
        max_length=15, choices=StatutChoices.choices,
        default=StatutChoices.ACTIF,
        verbose_name=_('Statut'),
    )
    application = models.ForeignKey(
        Application, on_delete=models.PROTECT,
        related_name='contrats', verbose_name=_('Application'),
    )
    fournisseur = models.ForeignKey(
        Fournisseur, on_delete=models.PROTECT,
        related_name='contrats', verbose_name=_('Fournisseur'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Créé le'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        verbose_name = _('Contrat')
        verbose_name_plural = _('Contrats')
        ordering = ['-date_debut', 'numero_contrat']

    def __str__(self):
        return self.numero_contrat

    # ── Calcul automatique du statut ──────────────────────────────────────────
    def _compute_statut(self):
        today = date.today()
        if self.date_fin < today:
            return self.StatutChoices.EXPIRE
        if self.date_debut > today:
            return self.StatutChoices.EN_ATTENTE
        return self.StatutChoices.ACTIF

    def save(self, *args, **kwargs):
        """Recalcule le statut automatiquement à chaque sauvegarde."""
        if self.date_fin and self.date_debut:
            self.statut = self._compute_statut()
        super().save(*args, **kwargs)

    # ── Propriétés utiles pour les templates ──────────────────────────────────
    @property
    def jours_restants(self):
        return (self.date_fin - date.today()).days

    @property
    def jours_restants_label(self):
        jours = self.jours_restants
        if jours < 0:
            return f'Expiré depuis {abs(jours)} j'
        if jours == 0:
            return "Expire aujourd'hui"
        return f'{jours} j restants'

    @property
    def statut_css(self):
        """Renvoie une classe CSS (success / warning / danger) selon le statut."""
        return {
            self.StatutChoices.ACTIF: 'success',
            self.StatutChoices.EN_ATTENTE: 'warning',
            self.StatutChoices.EXPIRE: 'danger',
        }.get(self.statut, 'default')

    @property
    def type_icon(self):
        return self.TYPE_META.get(self.contract_type, {}).get('icon', '📄')

    @property
    def type_color(self):
        return self.TYPE_META.get(self.contract_type, {}).get('color', '#6b7280')

    @property
    def type_bg(self):
        return self.TYPE_META.get(self.contract_type, {}).get('bg', 'rgba(107,114,128,0.12)')

    @property
    def est_proche_expiration(self):
        """True si le contrat expire dans les 90 prochains jours."""
        return 0 <= self.jours_restants <= 90
