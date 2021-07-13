from main.models import Golfer, Tiebreaker, Score, Subrecord, Matchup, Hole
from datetime import date, datetime
from main.functions import *
from django.db.models import Q
from django.db.models import Avg
from django.db.models import Max, Min
from main.helper import *
import statistics
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

def stDevScores(golfer, **kwargs):
    """Gets the standard deviation of a golfers scores for the season.

    Parameters
    ----------
    golfer : int
        The golfer you want the standard deviation for.
    year : int, optional
        Sets the year you want the golfers standard deviation for (default is the current year).

    Returns
    -------
    int
        The standard deviation for the golfers scores in the year 2020.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    if year == 2021:
        endWeek = getWeek() + 1
    else:
        endWeek = 21


    roundArray = []
    for week in range(1, endWeek):
        if golferPlayed(golfer, week, year=year):
            roundArray.append(Score.objects.filter(golfer=golfer, week=week, year=year).aggregate(Sum('score'))['score__sum'])

    stdev = statistics.pstdev(roundArray)

    print(Golfer.objects.get(id=golfer).name)
    print(stdev)

    return(stdev)


def stDevRound(golfer, week, **kwargs):
    """Gets the standard deviation of a golfers scores for a round.

    Parameters
    ----------
    golfer : int
        The golfer you want the standard deviation for.
    week : int
        The week you want the standard deviation for.
    year : int, optional
        Sets the year you want the golfers standard deviation for (default is the current year).

    Returns
    -------
    float
        The standard deviation for the golfers scores in a round.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    scores = Score.objects.all().filter(golfer=golfer, week=week, year=year)

    scoreArray = []
    for score in scores:
        scoreArray.append(score.score - Hole.objects.get(hole=score.hole, year=2020).par)

    stdev = statistics.pstdev(scoreArray)

    return(stdev)


def stDevHoles(golfer, **kwargs):
    """Gets the standard deviation of a golfers scores for each hole in the season.

    Parameters
    ----------
    golfer : int
        The golfer you want the holes standard deviation for.
    year : int, optional
        Sets the year you want the golfers holes standard deviation for (default is the current year).

    Returns
    -------
    dict
        A dictionary with the standard deviation for the golfers scores per hole in the year 2020. The hole numbers are
        the keys for each result.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    holeArray = {}
    stdevHoles = {}
    print(Golfer.objects.get(id=golfer).name)
    for hole in range(1, 19):
        if Score.objects.filter(golfer=golfer, hole=hole, year=year).exists():
            scores = Score.objects.filter(golfer=golfer, hole=hole, year=year)
            holeArray[str(hole)] = []
            for score in scores:
                holeArray[str(hole)].append(score.score)

            stdevHoles[str(hole)] = statistics.pstdev(holeArray[str(hole)])
        else:
            stdevHoles[str(hole)] = 0
        print(str(hole))
        print(stdevHoles[str(hole)])

    return stdevHoles


def getNetDiffLeague(**kwargs):
    """Gets the net difference of a all the golfers scores and their opponents for the season with additional week by
    week data included.

    Parameters
    ----------
    year : int, optional
        Sets the year you want the golfers holes standard deviation for (default is the current year).

    Returns
    -------
    dict
        Gets the net difference for the leagues golfers' scores and their opponents for the season with additional week
        by week data included.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    if year == 2021:
        endWeek = getWeek() + 1
    else:
        endWeek = 21

    returnDict = {}

    # get the golfer ids for the year
    golferIds = []
    for golfer in Golfer.objects.all().filter(year=year).exclude(team=0):
        golferIds.append(golfer.id)

    for golfer_id in golferIds:
        hcpDiff = 0
        oppHcpDiff = 0
        count = 0
        golferDataArray = []

        # iterate through all weeks in the season
        for week in range(1, endWeek):

            # skip flag for when golfer missed a week
            skip = False

            # get golfers team
            team_id = Golfer.objects.get(id=golfer_id).team

            if team_id == 0:
                team_id = getUnSubTeam(golfer_id, week)

            # get the opponents team
            schedule = Matchup.objects.all().filter(Q(week=week) & Q(year=year) & (Q(team1=team_id) | Q(team2=team_id)))[0]
            if schedule.team1 == team_id:
                opp_team = schedule.team2
            else:
                opp_team = schedule.team1

            # get all golfers on team with subs replacing absent golfers
            golfers = getTeamGolfers(team_id, week, subs=subs)

            # determine if golfer is the 'A' player
            if golfers['A'].id == golfer_id:
                isA = True
            elif golfers['B'].id == golfer_id:
                isA = False
            else:
                skip = True

            if not skip:

                # get oppenent teams golfers replacing absent golfers with subs
                opp_golfers = getTeamGolfers(opp_team, week)

                if isA:
                    golfer_id = golfers['A'].id
                    opp_golfer_id = opp_golfers['A'].id
                    golfer_hcp = round(HandicapReal.objects.get(golfer=golfers['A'].id, year=year, week=week).handicap)
                    opp_hcp = round(HandicapReal.objects.get(golfer=opp_golfers['A'].id, year=year, week=week).handicap)
                else:
                    golfer_id = golfers['B'].id
                    opp_golfer_id = opp_golfers['B'].id
                    golfer_hcp = round(HandicapReal.objects.get(golfer=golfers['B'].id, year=year, week=week).handicap)
                    opp_hcp = round(HandicapReal.objects.get(golfer=opp_golfers['B'].id, year=year, week=week).handicap)

                count = count + 1

                hcpDiffWeek = Score.objects.filter(golfer=golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum'] - 36 - golfer_hcp
                hcpDiff = hcpDiff + hcpDiffWeek
                oppHcpDiffWeek = Score.objects.filter(golfer=opp_golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum'] - 36 - opp_hcp
                oppHcpDiff = oppHcpDiff + oppHcpDiffWeek
                golferDataArray.append({'week': week, 'hcpDiff': hcpDiffWeek, 'oppHcpDiff': oppHcpDiffWeek})
        hcpDiff = hcpDiff / count
        oppHcpDiff = oppHcpDiff / count
        name = Golfer.objects.get(id=golfer_id).name
        returnDict[str(golfer_id)] = {'name': name, 'data': golferDataArray, 'totalHcpDiff': hcpDiff, 'totalOppHcpDiff': oppHcpDiff}

    for key, entry in returnDict.items():
        print("--------------")
        print(entry['name'])
        print(entry['totalHcpDiff'])
        print(entry['totalOppHcpDiff'])
        for week in entry['data']:
            print(('Week: ' + str(week['week'])))
            print(('Hcp Diff: ' + str(week['hcpDiff'])))
            print(('Opp Hcp Diff: ' + str(week['oppHcpDiff'])))
        print("--------------")

    return returnDict


def getNetDiff(golfer_id, **kwargs):
    """Gets the net difference for a specific golfers' scores and their opponents for the season with additional week by
    week data included.

    Parameters
    ----------
    year : int, optional
        Sets the year you want the golfers holes standard deviation for (default is the current year).

    Returns
    -------
    dict
        Returns the net difference for a specific golfers' scores and their opponents for the season with additional week by
        week data included.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    subs = Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week')

    if year == 2021:
        endWeek = getWeek() + 1
    else:
        endWeek = 21

    returnDict = {}
    hcpDiff = 0
    oppHcpDiff = 0
    count = 0
    golferDataArray = []

    for week in range(1, endWeek):

        # skip flag for when golfer missed a week
        skip = False

        # get golfers team
        team_id = Golfer.objects.get(id=golfer_id).team

        if team_id == 0:
            team_id = getUnSubTeam(golfer_id, week)

        # get the opponents team
        schedule = Matchup.objects.all().filter(Q(week=week) & Q(year=2021) & (Q(team1=team_id) | Q(team2=team_id)))[0]

        if schedule.team1 == team_id:
            opp_team = schedule.team2
        else:
            opp_team = schedule.team1

        # get all golfers on team with subs replacing absent golfers
        golfers = getTeamGolfers(team_id, week, subs=subs)

        # determine if golfer is the 'A' player
        if golfers['A'].id == golfer_id:
            isA = True
        elif golfers['B'].id == golfer_id:
            isA = False
        else:
            skip = True

        if not skip:

            # get oppenent teams golfers replacing absent golfers with subs
            opp_golfers = getTeamGolfers(opp_team, week, subs=subs)

            if isA:
                golfer_id = golfers['A'].id
                opp_golfer_id = opp_golfers['A'].id
                golfer_hcp = round(HandicapReal.objects.get(golfer=golfers['A'].id, year=2021, week=week).handicap)
                opp_hcp = round(HandicapReal.objects.get(golfer=opp_golfers['A'].id, year=2021, week=week).handicap)
            else:
                golfer_id = golfers['B'].id
                opp_golfer_id = opp_golfers['B'].id
                golfer_hcp = round(HandicapReal.objects.get(golfer=golfers['B'].id, year=2021, week=week).handicap)
                opp_hcp = round(HandicapReal.objects.get(golfer=opp_golfers['B'].id, year=2021, week=week).handicap)

            count = count + 1

            hcpDiffWeek = Score.objects.filter(golfer=golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum'] - 36 - golfer_hcp
            hcpDiff = hcpDiff + hcpDiffWeek
            oppHcpDiffWeek = Score.objects.filter(golfer=opp_golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum'] - 36 - opp_hcp
            oppHcpDiff = oppHcpDiff + oppHcpDiffWeek
            golferDataArray.append({'week': week, 'hcpDiff': hcpDiffWeek, 'oppHcpDiff': oppHcpDiffWeek})
    hcpDiff = hcpDiff / count
    oppHcpDiff = oppHcpDiff / count
    name = Golfer.objects.get(id=golfer_id).name
    returnDict = {'name': name, 'data': golferDataArray, 'totalHcpDiff': hcpDiff, 'totalOppHcpDiff': oppHcpDiff}

    print("--------------")
    print(returnDict['name'])
    print(returnDict['totalHcpDiff'])
    print(returnDict['totalOppHcpDiff'])
    for week in returnDict['data']:
        print(('Week: ' + str(week['week'])))
        print(('Hcp Diff: ' + str(week['hcpDiff'])))
        print(('Opp Hcp Diff: ' + str(week['oppHcpDiff'])))
    print("--------------")

    return returnDict


def getAverageHoleStats(**kwargs):

    # get optional parameters
    year = kwargs.get('year', 2021)

    data = {}

    for hole in range(1, 19):
        data.update({str(hole): Score.objects.all().filter(year=year, hole=hole).aggregate(Avg('score'))['score__avg']})

    return data


def getGolferHoleStats(golfer_id, **kwargs):

    # get optional parameters
    year = kwargs.get('year', 2021)

    data = {}

    for hole in range(1, 19):
        data.update({str(hole): Score.objects.all().filter(year=year, hole=hole, golfer=golfer_id).aggregate(Avg('score'))['score__avg']})

    return data


def golferData(golfer_id, **kwargs):

    # get optional parameters
    year = kwargs.get('year', 2021)

    total_points = 0
    best_gross_round = 99
    best_gross_round_week = 0
    worst_gross_round = 0
    worst_gross_round_week = 0
    ave_hole_scores = []
    points_array = []
    score_array = []
    best_ave_hole_score = 99
    worst_ave_hole_score = 0
    best_net_round = 99
    best_net_round_week = 0
    worst_net_round = 0
    worst_net_round_week = 0
    include2019 = False
    birdies = {}
    pars = {}
    bogeys = {}
    doubles = {}
    triples = {}
    fours = {}
    worse = {}

    # add 2019 system soon!
    if Golfer.objects.get(id=golfer_id).team == 0:
        include2019 = True

    # iterate over all holes
    for hole in range(1, 19):

        hole_par = Hole.objects.get(year=2020, hole=hole).par

        hole_string = str(hole)
        birdies[hole_string] = 0
        pars[hole_string] = 0
        bogeys[hole_string] = 0
        doubles[hole_string] = 0
        triples[hole_string] = 0
        fours[hole_string] = 0
        worse[hole_string] = 0

        # initialize total count
        total_counted_holes = 0

        # add average hole score to array
        if Score.objects.filter(year=year, hole=hole, golfer=golfer_id).exists():
            score = Score.objects.filter(year=year, hole=hole, golfer=golfer_id).aggregate(Avg('score'))['score__avg'] - hole_par

            ave_hole_scores.append(score)

            # update best and worst average hole scores if needed
            if score < best_ave_hole_score:
                best_ave_hole_score = score
            if score > worst_ave_hole_score:
                worst_ave_hole_score = score
        else:
            ave_hole_scores.append(0)

        # get all scores for the given hole
        scores = Score.objects.all().filter(year=year, hole=hole, golfer=golfer_id)

        # iterate through each weeks' score
        for score in scores:

            # get strokes over/under
            strokes_over_under = score.score - hole_par

            # increment total holes counted
            total_counted_holes = total_counted_holes + 1

            # add hole results to the correct array
            if strokes_over_under == -1:
                birdies[str(hole)] = birdies[str(hole)] + 1
            elif strokes_over_under == 0:
                pars[str(hole)] = pars[str(hole)] + 1
            elif strokes_over_under == 1:
                bogeys[str(hole)] = bogeys[str(hole)] + 1
            elif strokes_over_under == 2:
                doubles[str(hole)] = doubles[str(hole)] + 1
            elif strokes_over_under == 3:
                triples[str(hole)] = triples[str(hole)] + 1
            elif strokes_over_under == 4:
                fours[str(hole)] = fours[str(hole)] + 1
            else:
                worse[str(hole)] = worse[str(hole)] + 1

        # convert results into a percentage
        if total_counted_holes == 0:
            total_counted_holes = 1

        birdies[str(hole)] = 100 * birdies[str(hole)] / total_counted_holes
        pars[str(hole)] = 100 * pars[str(hole)] / total_counted_holes
        bogeys[str(hole)] = 100 * bogeys[str(hole)] / total_counted_holes
        doubles[str(hole)] = 100 * doubles[str(hole)] / total_counted_holes
        triples[str(hole)] = 100 * triples[str(hole)] / total_counted_holes
        fours[str(hole)] = 100 * fours[str(hole)] / total_counted_holes
        worse[str(hole)] = 100 * worse[str(hole)] / total_counted_holes

    # iterate over the current season
    for week in range(1, getWeek() + 1):
        if golferPlayed(golfer_id, week, year=year):
            gross = Score.objects.filter(golfer=golfer_id, week=week).aggregate(Sum('score'))['score__sum']
            net = Score.objects.filter(golfer=golfer_id, week=week).aggregate(Sum('score'))['score__sum'] - round(getHcp(golfer_id, week))

            if gross < best_gross_round:
                best_gross_round = gross
                best_gross_round_week = week
            if gross > worst_gross_round:
                worst_gross_round = gross
                worst_gross_round_week = week
            if net < best_net_round:
                best_net_round = net
                best_net_round_week = week
            if net > worst_net_round:
                worst_net_round = net
                worst_net_round_week = week
            pts = getPoints(golfer_id, week)
            points_array.append(pts)
            score_array.append(gross)
            total_points = total_points + pts
        else:
            points_array.append(None)
            score_array.append(None)

    hole_data = {'birdies': birdies, 'pars': pars, 'bogeys': bogeys,
                'doubles': doubles, 'triples': triples, 'fours': fours, 'worse': worse}

    return {'scoreArray': score_array, 'totalPoints': total_points, 'pointsArray': points_array, 'aveHoleScores': ave_hole_scores, 'bestAveHoleScore': best_ave_hole_score, 'worstAveHoleScore': worst_ave_hole_score, 'bestGrossRound': best_gross_round, 'bestGrossRoundWeek': best_gross_round_week, 'worstGrossRound': worst_gross_round, 'worstGrossRoundWeek': worst_gross_round_week, 'bestNetRound': best_net_round, 'bestNetRoundWeek': best_net_round_week, 'worstNetRound': worst_net_round, 'worstNetRoundWeek': worst_net_round_week, 'holeData': hole_data}


def hcpData(golfer_id, **kwargs):

    currentWeek = getWeek()

    # get optional parameters
    # this prevents the first few weeks from being overwritten by their computed values after we establish
    endingWeek = kwargs.get('recent', -1)

    # initialize variables
    golferHcpArray = []
    missed2019 = False
    golfer2020 = golfer_id

    # get the golfer object for 2020 and 2019 if they played then
    golfer = Golfer.objects.get(id=golfer_id)

    if Golfer.objects.filter(name=golfer.name, year=2019).exists() and golfer.team != 0:
        golfer2019 = Golfer.objects.get(name=golfer.name, year=2019).id
    else:
        missed2019 = True

    # iterate over the current season to get handicap array
    for hcpWeek in range(currentWeek, endingWeek, -1):

        # initialize variables
        week = hcpWeek
        golfer_id = golfer2020
        done = False
        maxScore = 0
        minScore = 99
        maxScoreWeek = 0
        minScoreWeek = 0
        maxScoreYear = 0
        minScoreYear = 0
        removedMinMax = False
        score = 0
        year = 2020
        firstScoreFlag = True
        prevScore = 0
        weeks = 0
        weekScores = []

        if week == 0 and year == 2020:
            week = 20
            year = 2019

            # if golfer did not play in 2019, end the calculation or update id
            if missed2019:
                done = True
            else:
                golfer_id = golfer2019

        # iterate over the golfers last 10 rounds
        while weeks < 10 and not done:

            # if golfer played week in question, add score
            if golferPlayed(golfer_id, week, year=year):

                # get the golfers score and add to count
                weekScore = Score.objects.filter(
                    golfer=golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum']
                weekScores.append(
                    {'weekScore': weekScore, 'week': week, 'year': year})
                score = score + weekScore

                # if this is the first score to work from prior to this week, record it for reference
                if firstScoreFlag:
                    firstScoreFlag = False
                    prevScore = weekScore

                # check if score is the new max or min that will be thrown out
                if weekScore > maxScore:
                    maxScore = weekScore
                    maxScoreWeek = week
                    maxScoreYear = year

                if weekScore < minScore:
                    minScore = weekScore
                    minScoreWeek = week
                    minScoreYear = year

                # increment week
                weeks = weeks + 1

            # rollover to 2019s scores if at week 1 in 2020
            if week == 1 and year == 2020:
                week = 20
                year = 2019

                # if golfer did not play in 2019, end the calculation or update id
                if missed2019:
                    done = True
                else:
                    golfer_id = golfer2019

            # if week 1 in 2019, end the calculation
            elif week == 1 and year == 2019:
                done = True
            # decrement week if weeks remain
            else:
                week = week - 1

        # if golfer has played over 5 weeks, subtract best and worst rounds
        if weeks > 5:
            score = score - minScore - maxScore
            weeks = weeks - 2
            removedMinMax = True

        # if there is any score data, determine handicap or set handicap to 0
        if weeks != 0:
            hcp = round(((score - (36 * weeks)) * .8) / weeks, 2)
        else:
            hcp = 0

        # append results to the array
        golferHcpArray.append({'removedMinMax': removedMinMax, 'week': hcpWeek + 1, 'hcp': hcp, 'score': prevScore, 'minScoreWeek': minScoreWeek, 'minScoreYear': minScoreYear,
                               'minScore': minScore, 'maxScoreWeek': maxScoreWeek, 'maxScoreYear': maxScoreYear, 'maxScore': maxScore, 'weekScores': weekScores})

        # print data for debug
        info = golfer.name + ": Week " + str(hcpWeek + 1) + " - " + str(hcp)
        print(info)
        print(weekScores)
        info = "Previous Weeks Score: " + str(prevScore)
        print(info)
        if removedMinMax:
            info = "Max Score: " + \
                str(maxScore) + " Week " + \
                str(maxScoreWeek) + " " + str(maxScoreYear)
            print(info)
            info = "Min Score: " + \
                str(minScore) + " Week " + \
                str(minScoreWeek) + " " + str(minScoreYear)
            print(info)

    return golferHcpArray

def hcpData2021(golfer_id, **kwargs):

    currentWeek = getWeek()

    hole_pars = {}

    for hole in range(1,19):
        hole_pars[str(hole)] = (Hole.objects.get(year=2020, hole=hole).par)

    # get optional parameters
    # this prevents the first few weeks from being overwritten by their computed values after we establish
    endingWeek = kwargs.get('recent', 0)

    # initialize variables
    golferHcpArray = []
    year = 2021

    # get the golfer object
    golfer = Golfer.objects.get(id=golfer_id)

    # iterate backwards over the current seasons weeks to get handicap array
    for week in range(currentWeek, endingWeek, -1):

        # initialize variables
        weekLoop = week
        maxScore = 0
        done = False
        minScore = 99
        maxScoreWeek = 0
        minScoreWeek = 0
        removedMinMax = False
        score = 0
        firstScoreFlag = True
        prevScore = 0
        weeks = 0
        weekScores = []

        while weeks < 10 and not done:
            # if golfer played week in question, process the scores
            if golferPlayed(golfer_id, weekLoop, year=year):

                # get the golfers score and add to count
                weekScore = Score.objects.filter(
                    golfer=golfer_id, week=weekLoop, year=year).aggregate(Sum('score'))['score__sum']
                weekScoresQS = Score.objects.filter(golfer=golfer_id, week=weekLoop, year=year)

                weekScores.append(
                    {'weekScore': weekScore, 'week': weekLoop})
                score = score + weekScore

                # if this is the first score to work from prior to this week, record it for reference
                if firstScoreFlag:
                    firstScoreFlag = False
                    prevScore = weekScore

                # check if week is the best or worst score of the season
                if weekScore > maxScore:
                    maxScore = weekScore
                    maxScoreWeek = weekLoop
                if weekScore < minScore:
                    minScore = weekScore
                    minScoreWeek = weekLoop

                # increment weeks count to stop the computation at 10 rounds max
                weeks = weeks + 1

            if weekLoop == 1:
                done = True
            else:
                weekLoop = weekLoop - 1



        # if golfer has played over 5 weeks, subtract best and worst rounds
        if weeks >= 5:
            score = score - minScore - maxScore
            weeks = weeks - 2
            removedMinMax = True

        # if there is any score data, determine handicap or set handicap to 0
        if weeks != 0:
            hcp = round(((score - (36 * weeks)) * .8) / weeks, 2)
        else:
            hcp = 0

        # append results to the array
        golferHcpArray.append({'removedMinMax': removedMinMax, 'week': week + 1, 'hcp': hcp, 'score': prevScore, 'minScoreWeek': minScoreWeek, 
            'minScore': minScore, 'maxScoreWeek': maxScoreWeek, 'maxScore': maxScore, 'weekScores': weekScores})

        # print data for debug
        info = golfer.name + ": Week " + str(week + 1) + " - " + str(hcp)
        print(info)
        print(weekScores)
        info = "Previous Weeks Score: " + str(prevScore)
        print(info)
        if removedMinMax:
            info = "Max Score: " + \
                str(maxScore) + " Week " + \
                str(maxScoreWeek)
            print(info)
            info = "Min Score: " + \
                str(minScore) + " Week " + \
                str(minScoreWeek)
            print(info)

    return golferHcpArray

def updateRealHcp(golfer, data):
    for entry in data:
        if HandicapReal.objects.filter(golfer=golfer, week=entry['week'], year=2021).exists():
            hcp = HandicapReal.objects.get(
                golfer=golfer, week=entry['week'], year=2021)
            hcp.handicap = entry['hcp']
            hcp.save()
        else:
            HandicapReal.objects.create(golfer=golfer, handicap=entry['hcp'], week=entry['week'], year=2021)


def hcpUpdate():
    for golfer in range(50, 74):
        data = hcpData(golfer, recent=5)
        updateRealHcp(golfer, data)

def generateHcp2021():

    golfers = getGolferIds(2021, subs=True)

    for golfer in golfers:
        data = hcpData2021(golfer)
        updateRealHcp(golfer, data)

    logger.info(f'Handicaps created and updated')

def getGolfers3rdWeekPlayed(golfer_id, **kwargs):
    """Gets the week number the golfer hit 3 total weeks of data for the season.

    Parameters
    ----------
    golfer_id : int
        The golfer you want the week returned for.
    year : int, optional
        Sets the year you want the week returned for (default is the current year).

    Returns
    -------
    int
        The week the golfer completed his third round on. Returns 0 if golfer has not yet completed 3 rounds.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    # initalize variables
    count = 0
    return_week = 0

    for week in range(1, 21):
        if golferPlayed(golfer_id, week, year=year):
            count = count + 1

        if count == 3:
            return_week = week
            break;

    return return_week


def copyHcp():

    # get the current week
    week = getWeek()

    # get all the golfers for the 2021 season
    golfers = getGolferObjects(2021, subs=True)

    # loop through golfers
    for golfer in golfers:

        # initalize the weeks played array
        weeksPlayed = []

        golfers3rdWeek = getGolfers3rdWeekPlayed(golfer.id)

        # deteremine if golfer has established (played 3 weeks)
        if golfers3rdWeek == 0:
            golfer.established = False
        else:
            golfer.established = True

        golfer.save()

        # loop through all weeks 
        for wk in range(1, week + 2):

            # did the golfer play that week
            if golferPlayed(golfer.id, wk, year=2021):
                # add week to weeks played array
                weeksPlayed.append(wk)

                # update the last hcp
                if HandicapReal.objects.filter(golfer=golfer.id, week=wk, year=2021).exists():
                    latestHcp = HandicapReal.objects.get(golfer=golfer.id, week=wk, year=2021)

                # if week played is the 4th week the golfer has played
                if len(weeksPlayed) == 4 and golfer.team != 0:

                    # check if handicap exists already
                    if HandicapReal.objects.filter(golfer=golfer.id, week=wk, year=2021).exists():
                        handicap = HandicapReal.objects.get(golfer=golfer.id, week=wk, year=2021)

                        # get the handicap to apply to the first 3 weeks played
                        fourthHcp = handicap.handicap

                    # iterate through the weeks the golfer has played and set them all to the handicap on the 4th round played
                    for rd in weeksPlayed:

                        # check if handicap exists already
                        if HandicapReal.objects.filter(golfer=golfer.id, week=rd, year=2021).exists():
                            handicap = HandicapReal.objects.get(golfer=golfer.id, week=rd, year=2021)
                            handicap.handicap = fourthHcp
                            handicap.save()
                            print(f'Has 4 - Wrote {fourthHcp} to {golfer.name} on week {rd}')
                        else:
                            HandicapReal(golfer=golfer.id, week=rd, year=2021, handicap=fourthHcp).save()
                            print(f'Has 4 NO EXISTING HCP - Wrote {fourthHcp} to {golfer.name} on week {rd}')

                    break
                    

            # last week of loop (next played week)
            if wk == week + 1:

                # 3 weeks havent been played yet
                # if the golfer is a sub
                if golfer.team == 0 and len(weeksPlayed) > 1:
                    # ensure the weeks are in the correct order (they should be this is just in case though)
                    weeksPlayed.sort()

                    secondWeekPlayed = weeksPlayed[1]
                    firstWeekPlayed = weeksPlayed[0]

                    # check if handicap exists already
                    if HandicapReal.objects.filter(golfer=golfer.id, week=firstWeekPlayed, year=2021).exists():
                        handicap = HandicapReal.objects.get(golfer=golfer.id, week=firstWeekPlayed, year=2021)
                        handicap.handicap = HandicapReal.objects.get(golfer=golfer.id, week=secondWeekPlayed, year=2021).handicap
                        handicap.save()
                        print(f'Under 3 - Wrote second week played hcp of {HandicapReal.objects.get(golfer=golfer.id, week=secondWeekPlayed, year=2021).handicap} to {golfer.name} on first week {firstWeekPlayed}')
                    else:
                        HandicapReal(golfer=golfer.id, week=firstWeekPlayed, year=2021, handicap=HandicapReal.objects.get(golfer=golfer.id, week=secondWeekPlayed, year=2021).handicap).save()
                        print(f'Under 3 NO EXISTING HCP - Wrote second week played hcp of {HandicapReal.objects.get(golfer=golfer.id, week=secondWeekPlayed, year=2021).handicap} to {golfer.name} on first week {firstWeekPlayed}')
                if len(weeksPlayed) == 1 and golfer.team == 0:
                    # check if handicap exists already
                    if HandicapReal.objects.filter(golfer=golfer.id, week=weeksPlayed[0], year=2021).exists():
                        handicap = HandicapReal.objects.get(golfer=golfer.id, week=weeksPlayed[0], year=2021)
                        handicap.handicap = HandicapReal.objects.get(golfer=golfer.id, week=weeksPlayed[0]+1, year=2021).handicap
                        handicap.save()
                        print(f'1 Week - Wrote second week played hcp of {HandicapReal.objects.get(golfer=golfer.id, week=weeksPlayed[0]+1, year=2021).handicap} to {golfer.name} on first week {weeksPlayed[0]}')
                    else:
                        HandicapReal(golfer=golfer.id, week=weeksPlayed[0], year=2021, handicap=HandicapReal.objects.get(golfer=golfer.id, week=weeksPlayed[0]+1, year=2021).handicap).save()
                        print(f'1 Week NO EXISTING HCP - Wrote second week played hcp of {HandicapReal.objects.get(golfer=golfer.id, week=weeksPlayed[0]+1, year=2021).handicap} to {golfer.name} on first week {weeksPlayed[0]}')




