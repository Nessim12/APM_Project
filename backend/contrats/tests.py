from django.contrib.auth import get_user_model
from django.test import TestCase

from applications.models import Application
from .models import Contract, Fournisseur


class ContractArchiveTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='testadmin',
            email='admin@example.com',
            password='secret123',
            role='ADMIN',
        )
        self.application = Application.objects.create(
            nom='App Test',
            description='Desc',
            criticite=Application.CriticiteChoices.MOYENNE,
            statut=Application.StatutChoices.ACTIF,
            date_mise_en_production='2024-01-01',
            date_fin_vie='2030-01-01',
            direction_metier='IT',
            nombre_utilisateurs=10,
            responsable_metier=self.user,
            responsable_technique=self.user,
            chef_de_projet=self.user,
            equipe_support=self.user,
        )
        self.fournisseur = Fournisseur.objects.create(
            nom='Fournisseur Test',
            email='fournisseur@example.com',
        )

    def test_delete_archives_contract_instead_of_removing_it(self):
        contract = Contract.objects.create(
            numero_contrat='CT-001',
            contract_type=Contract.ContractTypeChoices.MAINTENANCE,
            date_debut='2024-01-01',
            date_fin='2025-01-01',
            cout_annuel='1000.00',
            sla='99.9%',
            application=self.application,
            fournisseur=self.fournisseur,
        )

        contract.delete()

        self.assertTrue(contract.archived)
        self.assertFalse(Contract.objects.filter(pk=contract.pk).exists())
        self.assertTrue(Contract.all_objects.filter(pk=contract.pk).exists())

    def test_restore_reactivates_archived_contract(self):
        contract = Contract.objects.create(
            numero_contrat='CT-002',
            contract_type=Contract.ContractTypeChoices.SUPPORT,
            date_debut='2024-01-01',
            date_fin='2025-01-01',
            cout_annuel='500.00',
            sla='95%',
            application=self.application,
            fournisseur=self.fournisseur,
        )

        contract.delete()
        contract.restore()

        self.assertFalse(contract.archived)
        self.assertTrue(Contract.objects.filter(pk=contract.pk).exists())
