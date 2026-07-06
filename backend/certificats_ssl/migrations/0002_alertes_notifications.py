# Generated manually

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ssl', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AlerteSSLEnvoyee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('niveau', models.CharField(choices=[('J60', 'Expiration sous 60 jours'), ('J30', 'Expiration sous 30 jours'), ('EXPIRE', 'Certificat expiré')], max_length=10)),
                ('canal', models.CharField(choices=[('EMAIL', 'E-mail'), ('SMS', 'SMS'), ('APP', 'Application')], max_length=10)),
                ('envoyee_le', models.DateTimeField(auto_now=True)),
                ('certificat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertes_envoyees', to='ssl.certificatssl')),
            ],
            options={
                'verbose_name': 'Alerte SSL envoyée',
                'verbose_name_plural': 'Alertes SSL envoyées',
            },
        ),
        migrations.CreateModel(
            name='NotificationAdmin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('niveau', models.CharField(choices=[('J60', 'Expiration sous 60 jours'), ('J30', 'Expiration sous 30 jours'), ('EXPIRE', 'Certificat expiré')], max_length=10)),
                ('titre', models.CharField(max_length=255)),
                ('message', models.TextField()),
                ('lue', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('certificat', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='ssl.certificatssl')),
                ('destinataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications_ssl', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification admin SSL',
                'verbose_name_plural': 'Notifications admin SSL',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='alertesslenvoyee',
            constraint=models.UniqueConstraint(fields=('certificat', 'niveau', 'canal'), name='unique_alerte_ssl_par_canal'),
        ),
    ]
