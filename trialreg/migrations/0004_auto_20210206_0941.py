# Generated by Django 3.0.6 on 2021-02-06 09:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trialreg', '0003_auto_20210206_0936'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='registration',
            name='parent_email',
        ),
        migrations.RemoveField(
            model_name='registration',
            name='parent_phone',
        ),
    ]
