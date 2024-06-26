# Generated by Django 4.2.4 on 2023-09-26 02:00

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('chat', '0013_message_textmessage'),
    ]

    operations = [
        migrations.RenameField(
            model_name='message',
            old_name='time_tag',
            new_name='time_stamp',
        ),
        migrations.CreateModel(
            name='ChatClient',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_type', models.CharField(choices=[('PC', 'PRIVATE CHAT'), ('GC', 'GROUP CHAT')], max_length=2)),
                ('channel_name', models.CharField(max_length=255)),
                ('connection_time', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
