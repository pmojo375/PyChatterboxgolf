from django.contrib import admin
from main.models import *


class GolferAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'team', 'year')

class GameAdmin(admin.ModelAdmin):
    list_display = ('name', 'desc', 'week', 'year')


class GameEntryAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'week', 'year', 'won')


class SkinEntryAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'week', 'year', 'won')


class HandicapRealAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'handicap', 'week', 'year')


class HoleAdmin(admin.ModelAdmin):
    list_display = ('hole', 'par', 'handicap9', 'yards')


class MatchupAdmin(admin.ModelAdmin):
    list_display = ('team1', 'team2', 'week', 'year')


class ScoreAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'week', 'year', 'score', 'hole',)


class RoundAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'week', 'year', 'opp', 'front', 'opp_net', 'opp_gross', 'opp_points', 'opp_hcp', 'hcp', 'points', 'gross', 'pars', 'birdies', 'bogeys', 'doubles', 'triples', 'fours', 'worse', 'net', 'std_dev')


class SubrecordAdmin(admin.ModelAdmin):
    list_display = ('week', 'absent_id', 'sub_id', 'year',)


class TiebreakerAdmin(admin.ModelAdmin):
    list_display = ('golfer', 'week_1', 'week_2', 'week_3', 'week_4', 'week_5', 'week_6', 'week_7', 'week_8', 'week_9',
                    'week_10', 'week_11', 'week_12', 'week_13', 'week_14', 'week_15', 'week_16', 'week_17', 'week_18', 'week_19', 'week_20')


admin.site.register(Golfer, GolferAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(GameEntry, GameEntryAdmin)
admin.site.register(SkinEntry, SkinEntryAdmin)
admin.site.register(HandicapReal, HandicapRealAdmin)
admin.site.register(Matchup, MatchupAdmin)
admin.site.register(Hole, HoleAdmin)
admin.site.register(Score, ScoreAdmin)
admin.site.register(Subrecord, SubrecordAdmin)
admin.site.register(Round, RoundAdmin)
admin.site.register(Tiebreaker, TiebreakerAdmin)
