# Generated by Django 4.1.7 on 2023-04-04 15:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_profile_is_active_alter_profilephoto_profile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profilephoto',
            old_name='updated_at',
            new_name='uploaded_at',
        ),
    ]
