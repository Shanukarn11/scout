# Generated by Django 4.0.5 on 2022-09-05 07:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoutcourse',
            name='amount',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
