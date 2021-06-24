from django import template
from main.models import Golfer
from main.functions import *

register = template.Library()


@register.filter
def getName(value, arg):
    name = Golfer.objects.get(id=arg).name
    return value.replace(arg, name)


@register.filter
def getTeam(value, arg):
    team = value[arg]
    return team


@register.simple_tag()
def HoleScore(golfer_id, week, hole):
    return getScore(golfer_id, week, hole)


@register.simple_tag()
def css(golfer_id, week, hole, is_front,):
    return getScoreString(golfer_id, week, hole, isFront=is_front)


@register.simple_tag()
def HolePoint(golfer_id, week, hole, is_front, opp_team, opp_golfers, team_id, golfers):
    return getHolePoints(golfer_id, week, hole, isFront=is_front, opp_team=opp_team, opp_golfers=opp_golfers, golfers=golfers, team_id=team_id)


@register.simple_tag()
def RoundPoints(golfer_id, week, is_front, opp_team, opp_golfers, team_id, golfers):
    return getRoundPoints(golfer_id, week, isFront=is_front, opp_team=opp_team, opp_golfers=opp_golfers, golfers=golfers, team_id=team_id)


@register.simple_tag()
def TotalPoints(golfer_id, week, is_front, opp_team, opp_golfers, team_id, golfers):
    return getPoints(golfer_id, week, isFront=is_front, opp_team=opp_team, opp_golfers=opp_golfers, golfers=golfers, team_id=team_id)


@register.simple_tag()
def getGolferHcp(golfer_id, week):
    return round(getHcp(golfer_id, week))


@register.simple_tag()
def Gross(golfer_id, week):
    return getGross(golfer_id, week)


@register.simple_tag()
def Net(golfer_id, week):
    return getNet(golfer_id, week)
