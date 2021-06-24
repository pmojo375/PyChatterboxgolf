from .models import Round

def getStandingsFast():
    rounds = Round.objects.all().filter(year=year)

    for week in range(1, getWeek + 1):
        weekRounds = rounds.filter(week=week)

        for team in range(1, 8):
            teamGolfers = Golfer.objects.all().filter(team=team)
            golfer1Round = weekRounds.filter(golfer=teamGolfer[0].id)
            golfer2Round = weekRounds.filter(golfer=teamGolfer[1].id)

        for round in weekRounds:
            teamGolfers




