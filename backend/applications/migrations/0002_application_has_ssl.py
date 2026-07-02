# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('applications', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='has_ssl',
            field=models.BooleanField(
                default=False,
                help_text="Indique si l'application nécessite un certificat SSL.",
                verbose_name='Certificat SSL requis',
            ),
        ),
    ]
