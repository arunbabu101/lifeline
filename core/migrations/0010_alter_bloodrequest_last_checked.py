# Generated by Django 5.1.4 on 2025-01-13 07:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_bloodrequest_blood_received_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bloodrequest',
            name='last_checked',
            field=models.DateField(null=True),
        ),
    ]
