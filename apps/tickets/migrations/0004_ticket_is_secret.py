from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0003_ticket_responsable'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='is_secret',
            field=models.BooleanField(
                default=False,
                help_text=(
                    'Ticket confidentiel : visible uniquement par le demandeur, '
                    "l'agent de support et l'administrateur. "
                    'Utilisé pour les demandes de réinitialisation de mot de passe sans email.'
                ),
                verbose_name='Ticket secret',
            ),
        ),
    ]
