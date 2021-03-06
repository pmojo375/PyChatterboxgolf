# Generated by Django 3.2.3 on 2021-06-26 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0025_auto_20210626_0847'),
    ]

    operations = [
        migrations.RemoveIndex(
            model_name='golfer',
            name='main_golfer_year_9e4f54_idx',
        ),
        migrations.RemoveIndex(
            model_name='golfer',
            name='main_golfer_team_f93ff6_idx',
        ),
        migrations.RemoveIndex(
            model_name='handicapreal',
            name='main_handic_year_59f9c0_idx',
        ),
        migrations.RemoveIndex(
            model_name='hole',
            name='main_hole_year_012e66_idx',
        ),
        migrations.RemoveIndex(
            model_name='matchup',
            name='main_matchu_year_861886_idx',
        ),
        migrations.RemoveIndex(
            model_name='score',
            name='main_score_golfer_5f1846_idx',
        ),
        migrations.RemoveIndex(
            model_name='score',
            name='main_score_golfer_44ee3b_idx',
        ),
        migrations.RemoveIndex(
            model_name='score',
            name='main_score_week_c2329e_idx',
        ),
        migrations.AddIndex(
            model_name='golfer',
            index=models.Index(fields=['year', 'id'], name='main_golfer_year_8dc7e3_idx'),
        ),
        migrations.AddIndex(
            model_name='golfer',
            index=models.Index(fields=['team', 'year'], name='main_golfer_team_3db713_idx'),
        ),
        migrations.AddIndex(
            model_name='handicapreal',
            index=models.Index(fields=['year', 'week', 'golfer'], name='main_handic_year_72319b_idx'),
        ),
        migrations.AddIndex(
            model_name='hole',
            index=models.Index(fields=['year', 'hole'], name='main_hole_year_25c53c_idx'),
        ),
        migrations.AddIndex(
            model_name='matchup',
            index=models.Index(fields=['year', 'week'], name='main_matchu_year_7c7929_idx'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['golfer', 'week', 'year'], name='main_score_golfer_259fc2_idx'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['golfer', 'week'], name='main_score_golfer_08cd61_idx'),
        ),
        migrations.AddIndex(
            model_name='score',
            index=models.Index(fields=['week', 'year'], name='main_score_week_49f3f7_idx'),
        ),
    ]
