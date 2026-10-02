from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_add_is_placeholder_to_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='temp_password_expires_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Mot de passe temporaire expire le'),
        ),
    ]
