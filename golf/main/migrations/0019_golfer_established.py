# Generated by Django 3.1.7 on 2021-05-12 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0018_game'),
    ]

    operations = [
        migrations.AddField(
            model_name='golfer',
            name='established',
            field=models.BooleanField(default=False),
        ),
    ]
