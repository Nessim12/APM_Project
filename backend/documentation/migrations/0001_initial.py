import documentation.models
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('applications', '0002_application_has_ssl'),
        ('domaines', '0001_initial'),
        ('environments', '0001_initial'),
        ('ssl', '0002_alertes_notifications'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Identifiant')),
                ('nom', models.CharField(max_length=255, verbose_name='Nom')),
                ('type_fichier', models.CharField(blank=True, help_text='Extension du fichier (pdf, png, docx…).', max_length=20, verbose_name='Type de fichier')),
                ('categorie', models.CharField(choices=[('TECHNIQUE', 'Documentation technique'), ('PROCEDURE', 'Procédure'), ('MANUEL', 'Manuel utilisateur'), ('CONTRAT', 'Contrat'), ('ARCHITECTURE', 'Architecture'), ('AUTRE', 'Autre')], default='TECHNIQUE', max_length=20, verbose_name='Catégorie')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('date_upload', models.DateTimeField(auto_now_add=True, verbose_name='Date de téléversement')),
                ('type_gestion', models.CharField(choices=[('APPLICATION', 'Application'), ('ENVIRONNEMENT', 'Environnement'), ('SSL', 'Certificat SSL'), ('DOMAINE', 'Domaine'), ('GENERAL', 'Général')], default='GENERAL', max_length=20, verbose_name='Module de gestion')),
                ('fichier', models.FileField(upload_to=documentation.models.document_upload_path, verbose_name='Fichier')),
                ('taille_octets', models.PositiveBigIntegerField(default=0, verbose_name='Taille (octets)')),
                ('application', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='applications.application', verbose_name='Application')),
                ('certificat_ssl', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='ssl.certificatssl', verbose_name='Certificat SSL')),
                ('domaine', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='domaines.domaine', verbose_name='Domaine')),
                ('environnement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='environments.environnement', verbose_name='Environnement')),
                ('uploaded_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents_uploaded', to=settings.AUTH_USER_MODEL, verbose_name='Téléversé par')),
            ],
            options={
                'verbose_name': 'Document',
                'verbose_name_plural': 'Documents',
                'ordering': ['-date_upload'],
            },
        ),
    ]
