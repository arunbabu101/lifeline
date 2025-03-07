# Generated by Django 5.1.4 on 2025-01-07 09:02

import core.models
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='donor',
            options={'ordering': ['-created_at'], 'verbose_name': 'Blood Donor', 'verbose_name_plural': 'Blood Donors'},
        ),
        migrations.AddField(
            model_name='donor',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='donor',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='donor',
            name='profile_pic',
            field=models.ImageField(blank=True, null=True, upload_to='media/donor_profile_pics'),
        ),
        migrations.AddField(
            model_name='donor',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='blog',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='blogcategory',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='donor',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='donor',
            name='is_blood_donor',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='donor',
            name='last_donated',
            field=models.IntegerField(choices=[(1, '1 week'), (2, '2 weeks'), (3, '3 weeks'), (4, '4 weeks'), (5, '5 weeks'), (6, '6 weeks'), (7, '7 weeks'), (8, '8 weeks')], help_text='Number of weeks since last donation'),
        ),
        migrations.AlterField(
            model_name='donor',
            name='weight',
            field=models.DecimalField(decimal_places=2, help_text='Weight must be between 45 and 150 kg', max_digits=5, validators=[core.models.validate_weight]),
        ),
        migrations.AlterField(
            model_name='hospital',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
