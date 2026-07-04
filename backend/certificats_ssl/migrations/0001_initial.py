# Generated manually

import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('applications', '0002_application_has_ssl'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertificatSSL',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('domaine', models.CharField(max_length=255, verbose_name='Domaine / FQDN')),
                ('emetteur', models.CharField(max_length=255, verbose_name='Émetteur (CA)')),
                ('type_certificat', models.CharField(
                    choices=[('DV', 'Domain Validation (DV)'), ('OV', 'Organization Validation (OV)'), ('EV', 'Extended Validation (EV)')],
                    max_length=5,
                    verbose_name='Type de certificat',
                )),
                ('algorithme', models.CharField(max_length=100, verbose_name='Algorithme')),
                ('date_emission', models.DateField(verbose_name="Date d'émission")),
                ('date_expiration', models.DateField(verbose_name="Date d'expiration")),
                ('auto_renouvellement', models.BooleanField(default=False, verbose_name='Renouvellement automatique')),
                ('statut', models.CharField(
                    choices=[('ACTIF', 'Actif'), ('EXPIRE', 'Expiré'), ('A_RENOUVELER', 'À renouveler')],
                    default='ACTIF',
                    max_length=15,
                    verbose_name='Statut',
                )),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('application', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='certificat_ssl',
                    to='applications.application',
                    verbose_name='Application',
                )),
            ],
            options={
                'verbose_name': 'Certificat SSL',
                'verbose_name_plural': 'Certificats SSL',
                'ordering': ['domaine'],
            },
        ),
    ]
