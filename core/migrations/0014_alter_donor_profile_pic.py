# Generated by Django 5.1.4 on 2025-01-28 10:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_hospital_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donor',
            name='profile_pic',
            field=models.ImageField(blank=True, null=True, upload_to='donor_profile_pics/'),
        ),
    ]
