from main.functions import *
from main.league import *
from main.helper import *

def teamPoints(team_id, year):
    golfer_A_total_points = 0
    golfer_B_total_points = 0

    for week in range(1, getWeek() + 1):
        golfers = getTeamGolfers(team_id=team_id, week=week, get_sub=False)

        golfer_A_points = getPoints(golfer_id=golfers['A'].id, week=week, year=year, get_sub=False)
        golfer_B_points = getPoints(golfer_id=golfers['B'].id, week=week, year=year, get_sub=False)

        golfer_A_total_points = golfer_A_total_points + golfer_A_points
        golfer_B_total_points = golfer_B_total_points + golfer_B_points

    return {'golfer_A_points': golfer_A_total_points, 'golfer_B_points': golfer_B_total_points}

def teamAveScore(team_id, week, **kwargs):

    golfers = getTeamGolfers(team_id=team_id, week=week, get_sub=False)

    getScore(golfer_id=golfers['A'])








