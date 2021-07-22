from .models import *
from django.db.models import Sum
from datetime import datetime, timedelta
from django.db.models import Q

holes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
holes_front = [1, 2, 3, 4, 5, 6, 7, 8, 9]
holes_back = [10, 11, 12, 13, 14, 15, 16, 17, 18]

def getGolferIds(year, **kwargs):
    """Gets the ids of all golfers who played in 2021

    Parameters
    ----------
    subs : boolean, optional
        Set True if you would like to also include subs in the lookup 
        (default is false)

    Returns
    -------
    array
        Returns an array of all the golfer ids with or without subs.
    """

    # get optional parameters
    subs = kwargs.get('subs', False)

    if subs:
        golfers = Golfer.objects.filter(year=year).values('id')
    else:
        golfers = Golfer.objects.filter(year=year).exclude(team=0).values('id')

    returnArray = []

    for golfer in golfers:
        returnArray.append(golfer['id'])

    return returnArray


def getGolferObjects(year, **kwargs):
    """Gets the ids of all golfers who played in 2021

    Parameters
    ----------
    subs : boolean, optional
        Set True if you would like to also include subs in the lookup 
        (default is false)

    Returns
    -------
    array
        Returns an array of all the golfer ids with or without subs.
    """

    # get optional parameters
    subs = kwargs.get('subs', False)

    if subs:
        golfers = Golfer.objects.filter(year=year)
    else:
        golfers = Golfer.objects.filter(year=year).exclude(team=0)

    returnArray = []

    for golfer in golfers:
        returnArray.append(golfer)

    return returnArray


def getSkinsWinner(week, **kwargs):
    """Gets the skins winner for a specific week and year

    Parameters
    ----------
    week : int
        The week you want the winner(s) for
    year : int, optional
        The year you want the week in (default is the current year)

    Returns
    -------
    array
        Returns the weeks skins winners or winner if there is only one.
        If there are none, an empty array will be generated. The returned
        dict array will contain the ids and the hole they won the skin for.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    entered = SkinEntry.objects.filter(week=week, year=year)

    matchup = Matchup.objects.filter(week=week, year=year)[0]

    if matchup.front:
        holes = holes_front
    else:
        holes = holes_back

    skins = []

    for hole in holes:

        # initialize variables
        hole_min = 10
        min_score_golfer =[]

        # loop through those who are in skins the week in question
        for entry in entered:

            # get the golfers score for the hole in question
            score = Score.objects.get(golfer=entry.golfer, hole=hole, week=week, year=year).score

            # golfer is the current min score
            if hole_min > score:
                min_score_golfer = []
                hole_min = score
                min_score_golfer.append(entry.golfer)
            elif hole_min == score:
                min_score_golfer.append(entry.golfer)

        # golfer was only skin on hole
        if len(min_score_golfer) == 1:
            skins.append({'golfer_id':min_score_golfer[0], 'golfer': Golfer.objects.get(id=min_score_golfer[0]).name, 'hole': hole, 'score': hole_min})

    num_entries = entered.count()
    num_winners = len(skins)
    for winner in skins:
        winnings = (num_entries * 5)/num_winners

        winner['winnings'] = winnings

    return skins


def getSub(golfer_id, week, **kwargs):
    """Gets a sub id for an absent golfer

    Parameters
    ----------
    golfer_id : int
        The id of the absent golfer
    week : int
        The week the golfer was absent
    year : int, optional
        The year the golfer was absent (default is the current year)

    Returns
    -------
    int
        The id of the sub filling in for the absent golfer or th original
        golfer id if there is not sub found
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=year).values('sub_id', 'absent_id', 'week'))

    # looks through the array of sub record dicts and is true if golfer played
    if not any(d['absent_id'] == golfer_id and d['week'] == week for d in subs):
        return_id = golfer_id
    else:
        return_id = Subrecord.objects.get(absent_id=golfer_id, week=week, year=year).sub_id

    return return_id


def getUnSubTeam(sub_id, week, **kwargs):
    """Gets the team that a sub is playing for

    Parameters
    ----------
    sub_id : int
        The id of the sub that is playng for someone
    week : int
        The week the sub is playing
    year : int, optional
        The year the sub is playing (default is the current year)

    Returns
    -------
    int
        The team id for the team the sub is subbing for. Returns 0 if the
        function could not get a team
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    try:
        absent_id = Subrecord.objects.get(sub_id=sub_id, week=week, year=year).absent_id
        team = Golfer.objects.get(id=absent_id).team
    except Golfer.DoesNotExist:
        team = 0
    except Subrecord.DoesNotExist:
        team = 0

    return team


def golferPlayed(golfer_id, week, **kwargs):
    """Checks if a golfer played in a given week and year

    Parameters
    ----------
    golfer_id : int
        The golfer's id that you want the handicap for.
    week : int
        The week you want the golfers handicap for.
    year : int, optional
        The year you are wanting the golfer handicap for (default is the
        current year)

    Returns
    -------
    bool
        True or False depending on whether the golfer has any scores posted for
        the specified week and year.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    if Score.objects.filter(golfer=golfer_id, week=week, year=year).exists():
        return True
    else:
        return False


def getHcp(golfer_id, week, **kwargs):
    """Gets a golfers handicap

    Parameters
    ----------
    golfer_id : int
        The golfer's id that you want the handicap for.
    week : int
        The week you want the golfers handicap for.
    year : int, optional
        The year you are wanting the golfer handicap for (default is the
        current year)

    Returns
    -------
    int
        The golfers handicap unrounded. Returns 0 if no handicap exists
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    try:
        hcp = HandicapReal.objects.get(golfer=golfer_id, week=week, year=year).handicap
    except HandicapReal.DoesNotExist:
        hcp = 0

    return hcp


def getSubIds():
    """Gets a list of all the subs ids and names

    Parameters
    ----------
    None

    Returns
    -------
    list
        A list of dictionaries with all the subs' names and ids
    """

    returnList = []
    subs = Golfer.objects.all().filter(team=0).values('name', 'id')

    for sub in subs:
        returnList.append({'name': sub['name'], 'id': sub['id']})

    return returnList


def getTeamGolfers(team_id, week, **kwargs):
    """Gets a teams golfers with the option to replace with subs.

    Parameters
    ----------
    team_id : int
        The team you want to get the golfers for.
    week : int
        Used to get subs for a teams golfers if they missed the week.
    year : int, optional
        Sets the year you are wanting to get the golfers and subs for (default
        is the current year).
    get_sub : bool, optional
        A flag used to get subs if there were any for the specified week and
        year (default is True).
    golfers : Tuple(Golfer), optional
        A tuple of the golfer objects for the team if known. Would use this
        function to determine the handicaps and A/B status without the golfer
        lookup.

    Returns
    -------
    dict
        A dictionary with the database object for the 'A' and 'B' golfers (or
        subs) on the team for the specified week and year.
    """

    # get optional parameters
    get_sub = kwargs.get('get_sub', True)
    year = kwargs.get('year', 2021)
    golfers = kwargs.get('golfers', Golfer.objects.filter(team=team_id, year=year))
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    golfer0 = golfers[0]
    golfer1 = golfers[1]

    # replace golfer with sub if week was missed
    if get_sub:
        golfer0 = Golfer.objects.get(id=getSub(golfer0.id, week, subs=subs))
        golfer1 = Golfer.objects.get(id=getSub(golfer1.id, week, subs=subs))

    # get handicaps
    golfer0_handicap = getHcp(golfer0.id, week, year=year)
    golfer1_handicap = getHcp(golfer1.id, week, year=year)

    # if both handicaps are the same just use golfer0 as the A
    if golfer0_handicap == golfer1_handicap:
        A = golfer0
        A_Hcp = golfer0_handicap
        B = golfer1
        B_Hcp = golfer1_handicap
    elif golfer0_handicap < golfer1_handicap:
        A = golfer0
        A_Hcp = golfer0_handicap
        B = golfer1
        B_Hcp = golfer1_handicap
    else:
        A = golfer1
        A_Hcp = golfer1_handicap
        B = golfer0
        B_Hcp = golfer0_handicap

    # look into this - might not be needed
    #A.team = team_id
    #B.team = team_id

    return {'A': A, 'A_Hcp': A_Hcp, 'B_Hcp': B_Hcp, 'B': B, 'Golfers': golfers}


def getWeekScores(week, **kwargs):
    """Gets the gross and net scores for a specified week and year.

    Parameters
    ----------
    week : int
        The week you want to get scores for.
    year : int, optional
        The year you want to get scores for (default is the current year).

    Returns
    -------
    list
        A list with dictionaries for the 'A' and 'B' golfers, including subs,
        for each team that played in the year (defaults to the current year if
        not specified as an argument). The dictionaries contain the following
        keys:
            id : int
                The golfer's id
            Name : string
                The golfer's name
            Gross : int
                The golfer's gross score for the speified week and year
            Net : int
                The golfer's net score for the specified week and year
    """

    # get the optional parameters
    year = kwargs.get('year', 2021)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    # for now, year year has had the same teams so year is not used
    teams = range(1,11)
    returnList = []

    for team in teams:

        golfers = getTeamGolfers(team, week, get_sub=True, subs=subs)

        A = {'id': golfers['A'].id, 'Name': golfers['A'].name, 'Gross': getGross(
            golfers['A'].id, week, year=year, subs=subs), 'Net': getNet(golfers['A'].id, week, year=year, subs=subs)}
        B = {'id': golfers['B'].id, 'Name': golfers['B'].name, 'Gross': getGross(
            golfers['B'].id, week, year=year, subs=subs), 'Net': getNet(golfers['B'].id, week, year=year, subs=subs)}

        returnList.append(A)
        returnList.append(B)

    return returnList


def getGross(golfer_id, week, **kwargs):
    """Gets a golfer's gross score

    Parameters
    ----------
    golfer_id : int
        The id of the golfer.
    week : int
        The week you want the score for.
    year : int, optional
        Sets the year you want the score for (default is the current year).
    get_sub : bool, optional
        A flag used to replace the golfer with a sub if they did not post a
        score for the given weeks (default is False).

    Returns
    -------
    int
        The golfer or sub's gross score for the specified week and year. If the
        golfer does not have any scores posted, 0 will be returned.
    """

    # get optional parameters
    get_sub = kwargs.get('get_sub', False)
    year = kwargs.get('year', 2021)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    # get the golfer's sub if requested
    if get_sub:
        golfer_id = getSub(golfer_id, week, subs=subs)

    gross = Score.objects.filter(golfer=golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum']

    return gross


def getNet(golfer_id, week, **kwargs):
    """Gets a golfer's net score

    Parameters
    ----------
    golfer_id : int
        The id of the golfer.
    week : int
        The week you want the score for.
    year : int, optional
        Sets the year you want the score for (default is the current year).
    get_sub : bool, optional
        A flag used to replace the golfer with a sub if they did not post a
        score for the given weeks (default is False).

    Returns
    -------
    int
        The golfer or sub's net score for the specified week and year. If the
        golfer does not have any scores posted, 0 will be returned.
    """

    # get optional parameters
    get_sub = kwargs.get('get_sub', False)
    year = kwargs.get('year', 2021)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    # get the golfer's sub if requested
    if get_sub:
        golfer_id = getSub(golfer_id, week, subs=subs)

    gross = Score.objects.filter(golfer=golfer_id, week=week, year=year).aggregate(Sum('score'))['score__sum']

    hcp = round(getHcp(golfer_id, week, year=year))
    net = gross - hcp

    if hcp == 0:
        net = 0

    return net


def getSchedule(week, **kwargs):
    """Gets the schedule for a given week

    Parameters
    ----------
    week : int
        The week you want the score for.
    year : int, optional
        Sets the year you want the score for (default is the current year).

    Returns
    -------
    list
        The list of tuples with the first element being the 'home' and the next being the 'away' team.
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    matchups = Matchup.objects.filter(year=year, week=week)

    returnList = []

    for matchup in matchups:
        team1 = Golfer.objects.filter(team=matchup.team1, year=year)
        team2 = Golfer.objects.filter(team=matchup.team2, year=year)
        home = {'A': team1[0], 'B': team1[1]}
        away = {'A': team2[0], 'B': team2[1]}
        returnList.append((away, home))

    return returnList


def getScore(golfer_id, week, hole, **kwargs):
    """Gets the score for a golfer one a specific week and hole.

    Parameters
    ----------
    golfer_id : int
        The golfers id you are wanting the score for.
    week : int
        The week you want the score for.
    hole : int
        The hole you want the score for.
    year : int, optional
        Sets the year you want the score for (default is the current year).

    Returns
    -------
    int
        The score the golfer shot on the hole that week
    """

    # get optional parameters
    year = kwargs.get('year', 2021)

    if 'isFront' in kwargs:
        isFront = kwargs.get('isFront')
    else:
        isFront = Matchup.objects.filter(week=week, year=year).first().front

    if not isFront and hole < 10:
        hole = hole + 9

    try:
        score = Score.objects.get(golfer=golfer_id, week=week, hole=hole, year=year).score
    except Score.DoesNotExist:
        score = 0

    return score


def getPoints(golfer_id, week, **kwargs):
    """Gets the points for a golfer one a specific week.

    Parameters
    ----------
    golfer_id : int
        The golfers id you are wanting the points for.
    week : int
        The week you want the points for.
    team_id : int, optional
        The team ID of the golfer
    is_front : bool, optional
        Status of front or back for the given week (default looks up the status from the database)
    opp_team : int, optional
        The opponents team id for the given golfer (default looks up the team id from the database)
    opp_golfers : dict, optional
        The golfer objects for the opponents team (default looks up the golfers from the database)
    golfers : dict, optional
        The getTeamGolfer dict for the golfers team (default looks up the golfers from the database)
    year : int, optional
        Sets the year you want the golfers points for (default is the current year).

    Returns
    -------
    int
        The total points the golfer got in a week
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    team_id = kwargs.get('team_id', Golfer.objects.get(id=golfer_id).team)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    if team_id == 0:
        team_id = getUnSubTeam(golfer_id, week)

    is_front = kwargs.get('is_front', Matchup.objects.filter(week=week, year=year).first().front)

    if is_front:
        holes = holes_front
    else:
        holes = holes_back
    
    opp_team = kwargs.get('opp_team', getOppTeam(team_id, week))
    opp_golfers = kwargs.get('opp_golfers', getTeamGolfers(opp_team, week, subs=subs))
    golfers = kwargs.get('golfers', getTeamGolfers(team_id, week, subs=subs))

    points = 0

    hole_hcps = {}

    if 'hole_hcp' in kwargs:
        hole_hcps = kwargs.get('hole_hcp')
    else:
        hole_data = Hole.objects.filter(year=2020).values('handicap9', 'hole')

        for hole in hole_data:
            hole_hcps[str(hole['hole'])] = hole['handicap9']

    for hole in holes:
        hole_hcp = hole_hcps[str(hole)]
        points = points + getHolePoints(golfer_id, week, hole, hole_hcp=hole_hcp, opp_golfers=opp_golfers, opp_team=opp_team, isFront=is_front, team_id=team_id, golfers=golfers, subs=subs)

    points = points + getRoundPoints(golfer_id, week, hole_hcp=hole_hcp, opp_golfers=opp_golfers, opp_team=opp_team, isFront=is_front, team_id=team_id, golfers=golfers, subs=subs)

    return points


def getOppTeam(team_id, week):

    schedule = Matchup.objects.get(Q(week=week) & Q(year=2021) & (Q(team1=team_id) | Q(team2=team_id)))

    if schedule.team1 == team_id:
        return schedule.team2
    else:
        return schedule.team1


def getHolePoints(golfer_id, week, hole, **kwargs):
    """Gets the points for a golfer one a specific week.

    Parameters
    ----------
    golfer_id : int
        The golfers id you are wanting the hole points for.
    week : int
        The week you want the points for.
    hole : int
        The hole you want the points for.
    team_id : int, optional
        The team ID of the golfer
    is_front : bool, optional
        Status of front or back for the given week (default looks up the status from the database)
    opp_team : int, optional
        The opponents team id for the given golfer (default looks up the team id from the database)
    opp_golfers : dict, optional
        The golfer objects for the opponents team (default looks up the golfers from the database)
    golfers : dict, optional
        The golfer objects for the golfers team (default looks up the golfers from the database)
    year : int, optional
        Sets the year you want the golfers points for (default is the current year).

    Returns
    -------
    int
        The total points the golfer got in a week
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    team_id = kwargs.get('team_id', Golfer.objects.get(id=golfer_id).team)
    subs = Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week')

    if team_id == 0:
        team_id = getUnSubTeam(golfer_id, week)

    is_front = kwargs.get('isFront', Matchup.objects.filter(week=week, year=year).first().front)

    # set the appropriate hole array
    if is_front:
        if hole > 9:
            hole = hole - 9
    else:
        if hole < 10:
            hole = hole + 9

    opp_team = kwargs.get('opp_team', getOppTeam(team_id, week))
    opp_golfers = kwargs.get('opp_golfers', getTeamGolfers(opp_team, week, subs=subs))
    golfers = kwargs.get('golfers', getTeamGolfers(team_id, week, subs=subs))
    hole_hcp = kwargs.get('hole_hcp', Hole.objects.get(hole=hole, year=2020).handicap9)

    # determine if golfer is the 'A' player
    if golfers['A'].id == golfer_id:
        is_a = True
    else:
        is_a = False

    if is_a:
        opp_golfer_id = opp_golfers['A'].id
        golfer_hcp = round(golfers['A_Hcp'])
        opp_hcp = round(opp_golfers['A_Hcp'])
        hcp_diff = golfer_hcp - opp_hcp
    else:
        golfer_id = golfers['B'].id
        opp_golfer_id = opp_golfers['B'].id
        golfer_hcp = round(golfers['B_Hcp'])
        opp_hcp = round(opp_golfers['B_Hcp'])
        hcp_diff = golfer_hcp - opp_hcp

    golfer_score = getScore(golfer_id, week, hole)
    opp_score = getScore(opp_golfer_id, week, hole)

    abs_hcp_diff = abs(hcp_diff)

    if hcp_diff == 0:
        if golfer_score > opp_score:
            points = 0
        elif golfer_score < opp_score:
            points = 1
        else:
            points = .5
    elif hcp_diff < 0:
        if hole_hcp <= abs_hcp_diff:
            opp_score = opp_score - 1
        if hole_hcp <= (abs_hcp_diff - 9):
            opp_score = opp_score - 1

        if golfer_score > opp_score:
            points = 0
        elif golfer_score < opp_score:
            points = 1
        else:
            points = .5
    else:
        if hole_hcp <= abs_hcp_diff:
            golfer_score = golfer_score - 1
        if hole_hcp <= (abs_hcp_diff - 9):
            golfer_score = golfer_score - 1

        if golfer_score > opp_score:
            points = 0
        elif golfer_score < opp_score:
            points = 1
        else:
            points = .5

    return points


def getRoundPoints(golfer_id, week, **kwargs):
    """Gets the points for a golfer one a specific week.

    Parameters
    ----------
    golfer_id : int
        The golfers id you are wanting the round points for.
    week : int
        The week you want the round points for.
    team_id : int, optional
        The team ID of the golfer
    is_front : bool, optional
        Status of front or back for the given week (default looks up the status from the database)
    opp_team : int, optional
        The opponents team id for the given golfer (default looks up the team id from the database)
    opp_golfers : dict, optional
        The golfer objects for the opponents team (default looks up the golfers from the database)
    golfers : dict, optional
        The golfer objects for the golfers team (default looks up the golfers from the database)
    year : int, optional
        Sets the year you want the golfers points for (default is the current year).

    Returns
    -------
    int
        The round points the golfer got in the week (3 points for winning, 1.5 points for a tie)
    """

    # get optional parameters
    year = kwargs.get('year', 2021)
    team_id = kwargs.get('team_id', Golfer.objects.get(id=golfer_id).team)
    subs = kwargs.get('subs', Subrecord.objects.filter(year=2021).values('sub_id', 'absent_id', 'week'))

    if team_id == 0:
        team_id = getUnSubTeam(golfer_id, week)

    is_front = kwargs.get('isFront', Matchup.objects.filter(week=week, year=year).first().front)
    opp_team = kwargs.get('opp_team', getOppTeam(team_id, week))
    opp_golfers = kwargs.get('opp_golfers', getTeamGolfers(opp_team, week, subs=subs))
    golfers = kwargs.get('golfers', getTeamGolfers(team_id, week, subs=subs))

    # determine if golfer is the 'A' player
    if golfers['A'].id == golfer_id:
        isA = True
    else:
        isA = False

    if isA:
        opp_golfer_id = opp_golfers['A'].id
    else:
        golfer_id = golfers['B'].id
        opp_golfer_id = opp_golfers['B'].id

    net = getNet(golfer_id, week, year=year, get_sub=True, subs=subs)
    opp_net = getNet(opp_golfer_id, week, year=year, get_sub=True, subs=subs)

    if net < opp_net:
        points = 3
    elif net == opp_net:
        points = 1.5
    else:
        points = 0

    return points

def getWeek(**kwargs):
    """Gets the week number from the current date. The week
    number returned is the last week we should have played but is offset by a
    week if no scores are posted for that week if the offset flag is not set to
    false.

    Parameters
    ----------
    offset : bool, optional
        A flag to offset if scores are not posted for returned week (default is
        True)

    Returns
    -------
    int
        The week number of the season requested offset by -1 if there are no
        posted scores.
    """

    offset = kwargs.get('offset', True)

    # current datetime
    now = datetime.now()

    # the starting date
    start = datetime(2021, 4, 20, 16)

    # a time delta of one week
    td_week = timedelta(days=7)

    # initalize the week
    week = 1

    # initialize the number of weeks in the season
    season_weeks = 21

    # get the number of rainouts for the season
    #dates = Date.objects.filter(date__year=2021)

    #rain_outs = dates.count()

    #season_weeks = season_weeks + rain_outs

    week_offset = 0

    # iterate through all of the seasons weeks
    for w in range(1, season_weeks + 1):
        #if dates.filter(rain=True, date=datetime(year=(start + w * td_week).year, day=(start + w * td_week).day, month=(start + w * td_week).month)).exists():
            #week_offset = week_offset + 1

        if now > start + w * td_week:
            week = w - 1#week_offset

    # offset by one week if not all scores are posted
    if offset:
        if Score.objects.filter(week=week, year=2021).count() == 180:
            week = week
        else:
            week = week - 1

    return week


def getWeek2020(**kwargs):
    """Gets the week number from the current date. The week
    number returned is the last week we should have played but is offset by a
    week if no scores are posted for that week if the offset flag is not set to
    false.

    Parameters
    ----------
    offset : bool, optional
        A flag to offset if scores are not posted for returned week (default is
        True)

    Returns
    -------
    int
        The week number of the season requested offset by -1 if there are no
        posted scores.
    """

    offset = kwargs.get('offset', True)

    # current datetime
    now = datetime.now()

    # the starting date
    start = datetime(2020, 5, 19, 16)

    # a time delta of one week
    td_week = timedelta(days=7)

    # initalize the week
    week = 1

    # iterate through all of the seasons weeks
    for w in range(1, 21):
        if now > start + w * td_week:
            week = w

    # offset by one week if not all scores are posted
    if offset:
        if Score.objects.filter(week=week, year=2021).count() == 180:
            week = week
        else:
            week = week - 1

    return week
