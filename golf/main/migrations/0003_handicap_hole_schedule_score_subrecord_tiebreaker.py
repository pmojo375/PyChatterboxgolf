# Generated by Django 3.0.6 on 2020-05-27 23:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20200527_2308'),
    ]

    operations = [
        migrations.CreateModel(
            name='Handicap',
            fields=[
                ('golfer', models.IntegerField(primary_key=True, serialize=False)),
                ('week_1', models.IntegerField()),
                ('week_2', models.IntegerField()),
                ('week_3', models.IntegerField()),
                ('week_4', models.IntegerField()),
                ('week_5', models.IntegerField()),
                ('week_6', models.IntegerField()),
                ('week_7', models.IntegerField()),
                ('week_8', models.IntegerField()),
                ('week_9', models.IntegerField()),
                ('week_10', models.IntegerField()),
                ('week_11', models.IntegerField()),
                ('week_12', models.IntegerField()),
                ('week_13', models.IntegerField()),
                ('week_14', models.IntegerField()),
                ('week_15', models.IntegerField()),
                ('week_16', models.IntegerField()),
                ('week_17', models.IntegerField()),
                ('week_18', models.IntegerField()),
                ('week_19', models.IntegerField()),
                ('week_20', models.IntegerField()),
                ('year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Hole',
            fields=[
                ('hole', models.IntegerField(primary_key=True, serialize=False)),
                ('par', models.IntegerField()),
                ('handicap', models.IntegerField()),
                ('handicap9', models.IntegerField()),
                ('yards', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('week', models.IntegerField()),
                ('team_1', models.IntegerField()),
                ('team_2', models.IntegerField()),
                ('team_3', models.IntegerField()),
                ('team_4', models.IntegerField()),
                ('team_5', models.IntegerField()),
                ('team_6', models.IntegerField()),
                ('team_7', models.IntegerField()),
                ('team_8', models.IntegerField()),
                ('front', models.BooleanField()),
                ('year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('golfer', models.IntegerField()),
                ('hole', models.IntegerField()),
                ('score', models.IntegerField()),
                ('tookMax', models.BooleanField()),
                ('week', models.IntegerField()),
                ('year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Subrecord',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('week', models.IntegerField()),
                ('absent_id', models.IntegerField()),
                ('sub_id', models.IntegerField()),
                ('year', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Tiebreaker',
            fields=[
                ('golfer', models.IntegerField(primary_key=True, serialize=False)),
                ('week_1', models.IntegerField()),
                ('week_2', models.IntegerField()),
                ('week_3', models.IntegerField()),
                ('week_4', models.IntegerField()),
                ('week_5', models.IntegerField()),
                ('week_6', models.IntegerField()),
                ('week_7', models.IntegerField()),
                ('week_8', models.IntegerField()),
                ('week_9', models.IntegerField()),
                ('week_10', models.IntegerField()),
                ('week_11', models.IntegerField()),
                ('week_12', models.IntegerField()),
                ('week_13', models.IntegerField()),
                ('week_14', models.IntegerField()),
                ('week_15', models.IntegerField()),
                ('week_16', models.IntegerField()),
                ('week_17', models.IntegerField()),
                ('week_18', models.IntegerField()),
                ('week_19', models.IntegerField()),
                ('week_20', models.IntegerField()),
                ('year', models.IntegerField()),
            ],
        ),
    ]
