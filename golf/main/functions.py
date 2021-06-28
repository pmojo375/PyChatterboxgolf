from main.models import Golfer, Score, Matchup, Hole, HandicapReal, Round
from datetime import *
from main.helper import *
from main.league import *
from django.db.models import Sum
from django.db.models import Avg
from django.db.models import Q
from operator import *

teams = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
holes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
holes_front = [1, 2, 3, 4, 5, 6, 7, 8, 9]
holes_back = [10, 11, 12, 13, 14, 15, 16, 17, 18]
golfers_2020 = [29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44]


def makeRounds(**kwargs):

    subs = Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week')
    golfers = getGolferIds(2021, subs=True)

    for golfer in golfers:
        for week in range(1, getWeek() + 1):
            makeRound(golfer, week, 2021, subs=subs)


def allScoresIn():
    week = getWeek()

    if Score.objects.filter(year=2021, week=week).count() == 180:

        if not HandicapReal.objects.filter(year=2021, week=week+1).exists():
            generateHcp2021()

            makeRounds()



def makeRound(golfer_id, week, year, **kwargs):
    """Creates a database entry for a golfers round with all if not most of the info needed

    Parameters
    ----------
    golfer_id : int
        The id of the golfer the round is for.
    week : int
        The week the round is for.
    year : int
        Sets the year you want the round for.

    Returns
    -------
    null
    """

    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    if golferPlayed(golfer_id, week, year=year):
        birdies = 0
        pars = 0
        bogeys = 0
        doubles = 0
        triples = 0
        fours = 0
        worse = 0
        scores = Score.objects.filter(golfer=golfer_id, week=week, year=year).values('score', 'hole')
        gross = getGross(golfer_id, week, year=year, subs=subs)
        net = getNet(golfer_id, week, year=year, subs=subs)
        team_id = Golfer.objects.get(id=golfer_id).team
        golfers = getTeamGolfers(team_id, week, year=year, subs=subs)
        is_front = Matchup.objects.filter(week=week, year=year).first().front
        points = getPoints(golfer_id, week, year=year, is_front=is_front, subs=subs)
        hole_hcps = {}
        par = {}
        std_dev = stDevRound(golfer_id, week)

        hole_data = Hole.objects.filter(year=2020).values('handicap9', 'par', 'hole')

        for hole in hole_data:
            hole_hcps[hole['hole']] = hole['handicap9']
            par[hole['hole']] = hole['par']

        # iterate through each weeks' score
        for score in scores:
            hole = int(score['hole'])
            # get strokes over/under
            strokes_over_under = score['score'] - par[hole]

            # add hole results to the correct array
            if strokes_over_under == -1:
                birdies = birdies + 1
            elif strokes_over_under == 0:
                pars = pars + 1
            elif strokes_over_under == 1:
                bogeys = bogeys + 1
            elif strokes_over_under == 2:
                doubles = doubles + 1
            elif strokes_over_under == 3:
                triples = triples + 1
            elif strokes_over_under == 4:
                fours = fours + 1
            else:
                worse = worse + 1

        if team_id == 0:
            team_id = getUnSubTeam(golfer_id, week)

        opp_team = getOppTeam(team_id, week)
        opp_golfers = getTeamGolfers(opp_team, week, subs=subs)

        # determine if golfer is the 'A' player
        if golfers['A'].id == golfer_id:
            is_a = True
        else:
            is_a = False

        if is_a:
            opp_golfer_id = opp_golfers['A'].id
            golfer_hcp = golfers['A_Hcp']
            opp_hcp = opp_golfers['A_Hcp']
        else:
            opp_golfer_id = opp_golfers['B'].id
            golfer_hcp = golfers['B_Hcp']
            opp_hcp = opp_golfers['B_Hcp']

        opp_points = getPoints(opp_golfer_id, week, year=year, subs=subs)
        opp_gross = getGross(opp_golfer_id, week, year=year, subs=subs)
        opp_net = getNet(opp_golfer_id, week, year=year, subs=subs)

        if Round.objects.filter(golfer=golfer_id, week=week, year=year).exists():
            roundD = Round.objects.get(golfer=golfer_id, week=week, year=year)
            roundD.golfer = golfer_id
            roundD.opp = opp_golfer_id
            roundD.front = is_front
            roundD.opp_net = opp_net
            roundD.opp_gross = opp_gross
            roundD.opp_points = opp_points
            roundD.opp_hcp = opp_hcp
            roundD.hcp = golfer_hcp
            roundD.week = week
            roundD.year = year
            roundD.points = points
            roundD.gross = gross
            roundD.pars = pars
            roundD.birdies = birdies
            roundD.bogeys = bogeys
            roundD.doubles = doubles
            roundD.triples = triples
            roundD.fours = fours
            roundD.worse = worse
            roundD.net = net
            roundD.std_dev = std_dev
            roundD.save()
        else:
            Round(golfer=golfer_id, week=week, year=year, opp=opp_golfer_id, front=is_front,
                    opp_net=opp_net, opp_gross=opp_gross, opp_points=opp_points, opp_hcp=opp_hcp,
                    hcp=golfer_hcp, points=points, gross=gross, pars=pars, birdies=birdies,
                    bogeys=bogeys, doubles=doubles, triples=triples, fours=fours, worse=worse,
                    net=net, std_dev=std_dev).save()


def getPlayoffTeams(**kwargs):
    """Gets the playoff teams for a given year

    Parameters
    ----------
    year : int, optional
        Sets the year you want the playoffs for (default is the current year).

    Returns
    -------
    list
        The 4 playoff seed teams as dictionaries from the standings return data
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    week = getWeek()
    standings = getStandings(week)
    seeds = []

    # create a seperate sorted array for each half and the season
    firstHalfStandings = sorted(
        standings, key=itemgetter('firstHalfPoints'), reverse=True)
    secondHalfStandings = sorted(
        standings, key=itemgetter('secondHalfPoints'), reverse=True)
    fullStandings = sorted(standings, key=itemgetter(
        'seasonPoints'), reverse=True)
    i = 0

    # add the first half winner to the playoff team list
    seeds.append(firstHalfStandings[0])

    # add the second half winner to the playoff team list as long as they are not the same as the first half
    while secondHalfStandings[i] == seeds[0]:
        i = i + 1
    seeds.append(secondHalfStandings[i])

    # add the next two teams with the highest total season point totals that are not the first and second half winners
    i = 0
    while fullStandings[i] == seeds[0] or fullStandings[i] == seeds[1]:
        i = i + 1
    seeds.append(fullStandings[i])

    i = 0
    while fullStandings[i] == seeds[0] or fullStandings[i] == seeds[1] or fullStandings[i] == seeds[2]:
        i = i + 1
    seeds.append(fullStandings[i])

    # reshuffle teams to set seeding properly
    if seeds[0]['seasonPoints'] < seeds[1]['seasonPoints']:
        temp = seeds[0]
        seeds[0] = seeds[1]
        seeds[1] = temp
    if seeds[2]['seasonPoints'] < seeds[3]['seasonPoints']:
        temp = seeds[2]
        seeds[2] = seeds[3]
        seeds[3] = temp

    return seeds


# returns the weekly scores recorded for a specified year and week
# returns an array of x and y data points for a plot
def getWeeklyScores(week, year, **kwargs):
    # golfer ids from the 2021 season
    x_data = []
    y_data = []

    golfers = getGolferIds(2021)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    for golfer in golfers:
        if golferPlayed(golfer, week, year=year):
            y_data.append(Score.objects.filter(golfer=golfer, week=week).aggregate(
                Sum('score'))['score__sum'] - 36)
            x_data.append(Golfer.objects.get(id=golfer, year=year).name)
        else:
            golfer = getSub(golfer, week, year=year, subs=subs)
            y_data.append(Score.objects.filter(golfer=golfer, week=week).aggregate(
                Sum('score'))['score__sum'] - 36)
            x_data.append(Golfer.objects.get(id=golfer).name)

    return [x_data, y_data]


# this is a mess of logic - consider cleaning up or seperating
def getLeagueStats(week, **kwargs):
    par = {}
    hole_hcp = {}

    if 'hole_hcp' in kwargs and 'par' in kwargs:
        hole_hcp = kwargs.get('hole_hcp')
        par = kwargs.get('par')
    else:
        for hole in range(1, 19):
            hole_data = Hole.objects.get(year=2020, hole=hole)
            par[str(hole)] = hole_data.par
            hole_hcp[str(hole)] = hole_data.handicap9
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))


    year = 2021
    ave_hole_scores = []
    min_ave = 99
    max_ave = 0
    min_gross = 99
    max_gross = 0
    min_net = 99
    max_net = 0
    min_gross_names = []
    max_gross_names = []
    min_net_names = []
    max_net_names = []
    points_array = []
    hole_data = {}
    points_data = []
    birdies = {}
    pars = {}
    bogeys = {}
    doubles = {}
    triples = {}
    fours = {}
    worse = {}

    for hole in range(1, 19):
        hole_string = str(hole)
        birdies[hole_string] = 0
        pars[hole_string] = 0
        bogeys[hole_string] = 0
        doubles[hole_string] = 0
        triples[hole_string] = 0
        fours[hole_string] = 0
        worse[hole_string] = 0

        ave_hole_score = Score.objects.filter(year=year, hole=hole).aggregate(Avg('score'))['score__avg'] - par[
            str(hole)]
        ave_hole_scores.append(ave_hole_score)

        if ave_hole_score < min_ave:
            min_ave = ave_hole_score
        if ave_hole_score > max_ave:
            max_ave = ave_hole_score

        scores = Score.objects.all().filter(year=2021, hole=hole)
        hole_par = par[hole_string]

        total = 0

        for score in scores:
            temp = score.score - hole_par
            total = total + 1
            if temp == -1:
                birdies[hole_string] = birdies[hole_string] + 1
            elif temp == 0:
                pars[hole_string] = pars[hole_string] + 1
            elif temp == 1:
                bogeys[hole_string] = bogeys[hole_string] + 1
            elif temp == 2:
                doubles[hole_string] = doubles[hole_string] + 1
            elif temp == 3:
                triples[hole_string] = triples[hole_string] + 1
            elif temp == 4:
                fours[hole_string] = fours[hole_string] + 1
            else:
                worse[hole_string] = worse[hole_string] + 1

        birdies[hole_string] = 100 * birdies[hole_string] / total
        pars[hole_string] = 100 * pars[hole_string] / total
        bogeys[hole_string] = 100 * bogeys[hole_string] / total
        doubles[hole_string] = 100 * doubles[hole_string] / total
        triples[hole_string] = 100 * triples[hole_string] / total
        fours[hole_string] = 100 * fours[hole_string] / total
        worse[hole_string] = 100 * worse[hole_string] / total

        hole_data = {'birdies': birdies, 'pars': pars, 'bogeys': bogeys,
                     'doubles': doubles, 'triples': triples, 'fours': fours, 'worse': worse}

        golfer_names = {}

        golfers = Golfer.objects.filter(year=year).exclude(team=0)
        for golfer in golfers:
            golfer_names[str(golfer.id)] = golfer.name

    golfers = getGolferIds(2021)

    for wk in range(1, week + 1):
        is_front = Matchup.objects.filter(week=week, year=year).first().front

        for golfer in golfers:
            gross = Score.objects.filter(golfer=golfer, week=wk, year=year).aggregate(Sum('score'))['score__sum']

            if gross != None:
                net = gross - round(getHcp(golfer, wk))
                name = golfer_names[str(golfer)]

                if gross < min_gross:
                    min_gross = gross
                    min_gross_names.clear()
                    min_gross_names.append(name)
                elif gross == min_gross:
                    min_gross_names.append(name)
                if gross > max_gross:
                    max_gross = gross
                    max_gross_names.clear()
                    max_gross_names.append(name)
                elif gross == max_gross:
                    max_gross_names.append(name)
                if net < min_net:
                    min_net = net
                    min_net_names.clear()
                    min_net_names.append(name)
                elif net == min_net:
                    min_net_names.append(name)
                if net > max_net:
                    max_net = net
                    max_net_names.clear()
                    max_net_names.append(name)
                elif net == max_net:
                    max_net_names.append(name)

                points_data.append(getPoints(golfer, wk, year=year, is_front=is_front, hole_hcp=hole_hcp, par=par, subs=subs))
            else:
                points_data.append(None)

        points_array.append(points_data.copy())

        points_data.clear()

    return {'pointsArray': points_array, 'aveHoleScores': ave_hole_scores, 'minAve': min_ave, 'maxAve': max_ave,
            'minGross': min_gross, 'minGrossNames': min_gross_names, 'maxGross': max_gross,
            'maxGrossNames': max_gross_names, 'minNet': min_net, 'minNetNames': min_net_names, 'maxNet': max_net,
            'maxNetNames': max_net_names, 'holeData': hole_data}


def getStandingsFast(week, **kwargs):
    week = getWeek()

    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    standings = []

    # get the total points for each half if needed
    if week > 9:
        firstHalfPoints = getPointsFast(9, subs=subs)
        secondHalfPoints = getPointsFast(week, subs=subs)
    else:
        firstHalfPoints = getPointsFast(week, subs=subs)
        secondHalfPoints = 0

    # itereate through the teams
    for team in teams:

        team_golfers = Golfer.objects.filter(team=team, year=2021)

        teamPoints = 0

        if week > 9:
            firstHalfTeam = firstHalfPoints[team_golfers[0].id] + firstHalfPoints[team_golfers[1].id]
            secondHalfTeam = secondHalfPoints[team_golfers[0].id] + secondHalfPoints[team_golfers[1].id]
            teamPoints = firstHalfTeam + secondHalfTeam
        else:
            teamPoints = firstHalfPoints[team_golfers[0].id] + firstHalfPoints[team_golfers[1].id]
            firstHalfTeam = teamPoints
            secondHalfTeam = 0

        standings.append({'golfer1Hcp': getHcp(team_golfers[0].id, week+1), 'golfer2Hcp': getHcp(team_golfers[1].id, week+1), 'golfer1': team_golfers[0].name, 'golfer2': team_golfers[1].name, 'first': firstHalfTeam, 'second': secondHalfTeam, 'total': teamPoints})

    return standings

def getPointsFast(week, **kwargs):
    """Gets all the golfers points in a dictionary format for the given week.

    Parameters
    ----------
    week : int
        Sets the week you want the accumulated points for.
    year : int, optional
        Sets the year you want the accumulated points for (default is the current year).
    seperate_subs : bool, optional
        Set to true if you want to pull the subs' points out of the absent golfers totals
        and include the subs in the dictionary results. This would be set to true in places
        where you would like to show stats and left false for standings calcs (default is
        false).

    Returns
    -------
    dictionary
        Returns a dict of the golfer IDs and their point totals at the end of the inputted
        week with sub contributions pulled out if specified.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    seperate_subs = kwargs.get('seperate_subs', False)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    week_range = range(1, week + 1)

    golferPoints = {}

    # gets the 2021 golfer IDs with or without subs
    golfers = getGolferIds(2021, subs=seperate_subs)

    for golfer in golfers:

        # initalize the golfers points
        golferPoints[golfer] = 0

        for week in week_range:

            if seperate_subs:
                if golferPlayed(golfer, week, year=2021):
                    rnd = Round.objects.get(golfer=golfer, year=2021, week=week)
                    golferPoints[golfer] = rnd.points + golferPoints[golfer]

            else:
                golfer_or_sub = getSub(golfer, week, year=2021, subs=subs)
                rnd = Round.objects.get(golfer=golfer_or_sub, year=2021, week=week)
                golferPoints[golfer] = rnd.points + golferPoints[golfer]

    return golferPoints

def getStandings(week, **kwargs):
    """Gets the standings for the given week

    Parameters
    ----------
    week : int
        Sets the week you want the standings for.
    year : int, optional
        Sets the year you want the standings for (default is the current year).

    Returns
    -------
    list
        A list of each teams scores and handicaps including both halves
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    out = []
    firstHalfHcpA = 0
    firstHalfHcpB = 0
    secondHalfHcpA = 0
    secondHalfHcpB = 0

    if week != 0:
        for team in teams:

            # initialize golfers variable
            golferObjects = None

            firstHalfPoints = 0
            secondHalfPoints = 0

            # get the first half points
            for wk in range(1, week + 1):

                is_front = Matchup.objects.filter(week=wk, year=year).first().front

                opp_team = getOppTeam(team, wk)
                opp_golfers = getTeamGolfers(opp_team, wk, subs=subs)

                # get the golfers that played the week in question

                if wk == 1:
                    golfers = getTeamGolfers(team, wk, subs=subs)
                else:
                    golfers = getTeamGolfers(team, wk, golfers=golferObjects, subs=subs)

                golferObjects = golfers['Golfers']

                # get the golfers points for the week in question
                golferAPoints = getPoints(golfers['A'].id, wk, team_id=golfers['A'].team, golfers=golfers, is_front=is_front, opp_team=opp_team, opp_golfers=opp_golfers, subs=subs)
                golferBPoints = getPoints(golfers['B'].id, wk, team_id=golfers['B'].team, golfers=golfers, is_front=is_front, opp_team=opp_team, opp_golfers=opp_golfers, subs=subs)

                # add points to proper half
                if wk < 10:
                    firstHalfPoints = firstHalfPoints + golferAPoints + golferBPoints
                else:
                    secondHalfPoints = secondHalfPoints + golferAPoints + golferBPoints

            # if in first half still
            # using week + 1 becuase the most current hcp is the next weeks
            if week + 1 < 10:
                firstHalfHcp1 = getHcp(golferObjects[0].id, week + 1)
                firstHalfHcp2 = getHcp(golferObjects[1].id, week + 1)

                if firstHalfHcp1 >= firstHalfHcp2:
                    firstHalfHcpA = firstHalfHcp2
                    firstHalfHcpB = firstHalfHcp1

                    golferAName = golferObjects[1].name
                    golferBName = golferObjects[0].name
                else:
                    firstHalfHcpA = firstHalfHcp1
                    firstHalfHcpB = firstHalfHcp2

                    golferAName = golferObjects[0].name
                    golferBName = golferObjects[1].name
            else:                
                firstHalfHcp1 = getHcp(golferObjects[0].id, 10)
                firstHalfHcp2 = getHcp(golferObjects[1].id, 10)

                if firstHalfHcp1 >= firstHalfHcp2:
                    firstHalfHcpA = firstHalfHcp2
                    firstHalfHcpB = firstHalfHcp1
                else:
                    firstHalfHcpA = firstHalfHcp1
                    firstHalfHcpB = firstHalfHcp2

                secondHalfHcp1 = getHcp(golferObjects[0].id, week + 1)
                secondHalfHcp2 = getHcp(golferObjects[1].id, week + 1)

                if secondHalfHcp1 >= secondHalfHcp2:
                    secondHalfHcpA = secondHalfHcp2
                    secondHalfHcpB = secondHalfHcp1

                    golferAName = golferObjects[1].name
                    golferBName = golferObjects[0].name

                else:
                    secondHalfHcpA = secondHalfHcp1
                    secondHalfHcpB = secondHalfHcp2\

                    golferAName = golferObjects[0].name
                    golferBName = golferObjects[1].name

            seasonPoints = firstHalfPoints + secondHalfPoints

            out.append({'A': golferAName, 'B': golferBName, 'firstHalfPoints': firstHalfPoints,
                        'secondHalfPoints': secondHalfPoints, 'firstHalfHcpA': firstHalfHcpA,
                        'firstHalfHcpB': firstHalfHcpB, 'secondHalfHcpA': secondHalfHcpA, 'secondHalfHcpB': secondHalfHcpB,
                        'seasonPoints': seasonPoints})
    else:
        for team in teams:
            golfers = getTeamGolfers(team, week + 1, subs=subs)

            # first week point are 0
            golferAPoints = 0
            golferBPoints = 0

            firstHalfPoints = 0
            secondHalfPoints = 0

            firstHalfHcpA = getHcp(golfers['A'].id, week + 1)
            firstHalfHcpB = getHcp(golfers['B'].id, week + 1)

            golferAName = golfers['A'].name
            golferBName = golfers['B'].name

            seasonPoints = firstHalfPoints + secondHalfPoints

            out.append({'A': golferAName, 'B': golferBName, 'firstHalfPoints': firstHalfPoints,
                        'secondHalfPoints': secondHalfPoints, 'firstHalfHcpA': firstHalfHcpA,
                        'firstHalfHcpB': firstHalfHcpB, 'secondHalfHcpA': secondHalfHcpA, 'secondHalfHcpB': secondHalfHcpB,
                        'seasonPoints': seasonPoints})
    return out


def getScoreString(golfer_id, week, hole, **kwargs):
    team_id = Golfer.objects.all().filter(id=golfer_id)[0].team

    # if team id is 0, get absent golfer sub is playing for
    if team_id == 0:
        team_id = getUnSubTeam(golfer_id, week)

    subs = Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week')

    # get the opponents team
    if 'opp_team' in kwargs and 'isFront' in kwargs:
        opp_team = kwargs.get('opp_team')
        isFront = kwargs.get('isFront')

        # get oppenent teams golfers replacing absent golfers with subs
        opp_golfers = getTeamGolfers(opp_team, week, subs=subs)

    elif 'opp_golfers' in kwargs and 'isFront' in kwargs:
        opp_golfers = kwargs.get('opp_golfers')
        isFront = kwargs.get('isFront')
    else:
        schedule = Matchup.objects.get(Q(week=week) & Q(
            year=2021) & (Q(team1=team_id) | Q(team2=team_id)))

        if schedule.team1 == team_id:
            opp_team = schedule.team2
        else:
            opp_team = schedule.team1

        # get oppenent teams golfers replacing absent golfers with subs
        opp_golfers = getTeamGolfers(opp_team, week, subs=subs)

        # set the appropriate hole array
        isFront = schedule.front

    # get all golfers on team with subs replacing absent golfers
    if 'golfers' in kwargs:
        golfers = kwargs.get('golfers')
    else:
        golfers = getTeamGolfers(team_id, week, subs=subs)

    score = getScore(golfer_id, week, hole)

    # determine if golfer is the 'A' player
    if golfers['A'].id == golfer_id:
        isA = True
    else:
        isA = False

    # get the opponents team
    schedule = Matchup.objects.all().filter(Q(week=week) & Q(
        year=2021) & (Q(team1=team_id) | Q(team2=team_id)))[0]

    if schedule.team1 == team_id:
        opp_team = schedule.team2
    else:
        opp_team = schedule.team1

    # set the appropriate hole array
    if isFront:
        hole = hole
    else:
        hole = hole + 9

    if isA:
        golfer_id = golfers['A'].id
        golfer_hcp = round(golfers['A_Hcp'])
        opp_hcp = round(opp_golfers['A_Hcp'])
        hcp_diff = golfer_hcp - opp_hcp
    else:
        golfer_id = golfers['B'].id
        golfer_hcp = round(golfers['B_Hcp'])
        opp_hcp = round(opp_golfers['B_Hcp'])
        hcp_diff = golfer_hcp - opp_hcp

    rank = score - Hole.objects.get(year=2020, hole=hole).par

    if hcp_diff > 9:
        getting_two_count = hcp_diff - 9
    else:
        getting_two_count = 0

    if hcp_diff > 0:
        if getting_two_count > 0:
            if Hole.objects.get(year=2020, hole=hole).handicap9 <= getting_two_count:
                if rank == -2:
                    rankStr = 'getting2-stroke_eagle'
                elif rank == -1:
                    rankStr = 'getting2-stroke_birdie'
                elif rank == 0:
                    rankStr = 'getting2-stroke_par'
                elif rank == 1:
                    rankStr = 'getting2-stroke_bogey'
                else:
                    rankStr = 'getting2-stroke_worst'
            elif Hole.objects.get(year=2020, hole=hole).handicap9 <= hcp_diff:
                if rank == -2:
                    rankStr = 'getting-stroke_eagle'
                elif rank == -1:
                    rankStr = 'getting-stroke_birdie'
                elif rank == 0:
                    rankStr = 'getting-stroke_par'
                elif rank == 1:
                    rankStr = 'getting-stroke_bogey'
                else:
                    rankStr = 'getting-stroke_worst'
        elif getting_two_count == 0:
            if Hole.objects.get(year=2020, hole=hole).handicap9 <= hcp_diff:
                if rank == -2:
                    rankStr = 'getting-stroke_eagle'
                elif rank == -1:
                    rankStr = 'getting-stroke_birdie'
                elif rank == 0:
                    rankStr = 'getting-stroke_par'
                elif rank == 1:
                    rankStr = 'getting-stroke_bogey'
                else:
                    rankStr = 'getting-stroke_worst'
            else:
                if rank == -2:
                    rankStr = 'eagle'
                elif rank == -1:
                    rankStr = 'birdie'
                elif rank == 0:
                    rankStr = 'par'
                elif rank == 1:
                    rankStr = 'bogey'
                else:
                    rankStr = 'worst'
    else:
        if rank == -2:
            rankStr = 'eagle'
        elif rank == -1:
            rankStr = 'birdie'
        elif rank == 0:
            rankStr = 'par'
        elif rank == 1:
            rankStr = 'bogey'
        else:
            rankStr = 'worst'

    return rankStr
