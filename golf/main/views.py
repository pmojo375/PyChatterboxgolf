from django.shortcuts import render
import csv
import io
from django.contrib import messages
from main.models import *
from main.functions import *
from main.league import *
from main.helper import *
from .forms import *
from django.http import HttpResponseRedirect
from operator import itemgetter
from django.db.models import Avg
from plotly.offline import plot
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
import plotly.graph_objs as go
from django.views.decorators.cache import cache_page

# Create your views here.
def main(request):
    week = getWeek()
    lastGameWinner = []
    unestablished = Golfer.objects.filter(year=2021, established=False).exclude(team=0)

    if week > 8:
        secondHalf = True
    else:
        secondHalf = False

    seeds = []

    # get the next weeks schedule
    schedule = getSchedule(week + 1)

    # check if there are handicaps for the given week
    check = HandicapReal.objects.filter(week=week, year=2021).exists()

    # if the week is not the first of the year and there are not handicaps decrement the week
    if week != 0:
        if not check:
            week = week - 1

    # get standings for the current week
    standings = getStandings(week)

    # get standings in correct order
    firstHalfStandings = sorted(standings, key=itemgetter('firstHalfPoints'), reverse=True)
    secondHalfStandings = sorted(standings, key=itemgetter('secondHalfPoints'), reverse=True)
    fullStandings = sorted(standings, key=itemgetter('seasonPoints'), reverse=True)

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

    lastSkinWinner = getSkinsWinner(week, year=2021)

    currentGame = Game.objects.get(year=2021, week=week+1)
    lastGame = Game.objects.get(year=2021, week=week)

    if GameEntry.objects.filter(won=True, week=week, year=2021).exists():
        winners =  GameEntry.objects.filter(won=True, week=week, year=2021)
        for winner in winners:
                lastGameWinner.append(Golfer.objects.get(id=winner.golfer).name)
    else:
        lastGameWinner.append('Not Set')

    game_pot = (GameEntry.objects.filter(week=week, year=2021).count() * 2)/len(lastGameWinner)

    context = {
        'lastSkinWinner': lastSkinWinner,
        'week': week + 1,
        'lastweek': week,
        'currentGame': currentGame,
        'lastGame': lastGame,
        'lastGameWinner': lastGameWinner,
        'game_pot': game_pot,
        'firstHalfStandings': firstHalfStandings,
        'secondHalfStandings': secondHalfStandings,
        'fullStandings': fullStandings,
        'schedule': schedule,
        'secondHalf': secondHalf,
        'unestablished': unestablished,
    }
    return render(request, 'main.html', context)


def games(request):
    lastGameWinner = []

    week = getWeek()

    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        if 'golfer_game' in request.POST:
            # create a form instance and populate it with data from the request:
            gameForm = GameEntryForm(request.POST)

            if gameForm.is_valid():
                GameEntry.objects.update_or_create(
                    golfer=gameForm.cleaned_data['golfer_game'].id,
                    year=2021,
                    week=gameForm.cleaned_data['week']
                )

                # redirect to a new URL:
                return HttpResponseRedirect('/games/')
                pass
        if 'golfer_skins' in request.POST:
            # create a form instance and populate it with data from the request:
            skinsForm = SkinEntryForm(request.POST)

            if skinsForm.is_valid():
                SkinEntry.objects.update_or_create(
                    golfer=skinsForm.cleaned_data['golfer_skins'].id,
                    year=2021,
                    week=skinsForm.cleaned_data['week']
                )

                # redirect to a new URL:
                return HttpResponseRedirect('/games/')
                pass
        if 'game_winner' in request.POST:
            # create a form instance and populate it with data from the request:
            gameWinnerForm = GameWinnerForm(request.POST)

            if gameWinnerForm.is_valid():
                entry = GameEntry.objects.get(golfer=gameWinnerForm.cleaned_data['game_winner'].golfer, week=week, year=2021)
                entry.won = True
                entry.save()

                # redirect to a new URL:
                return HttpResponseRedirect('/games/')
                pass


        gameForm = GameEntryForm()
        skinsForm = SkinEntryForm()
        gameWinnerForm = GameWinnerForm()
    # if a GET (or any other method) we'll create a blank form
    else:
        gameForm = GameEntryForm()
        skinsForm = SkinEntryForm()
        gameWinnerForm = GameWinnerForm()

    lastWeekWinner = getSkinsWinner(week, year=2021)

    games = Game.objects.filter(year=2021)

    # determine if there is a game winner set for the current week yet and the next week
    lastEnteredGameWeekExists = GameEntry.objects.filter(year=2021, week=week, won=True).exists()
    nextEnteredGameWeekExists = GameEntry.objects.filter(year=2021, week=week+1, won=True).exists()

    # if there was a game winner for the last week (based on the getWeek functions returned week) then get the entries for the next week else get last weeks
    if lastEnteredGameWeekExists:
        gameEntry = GameEntry.objects.filter(year=2021, week=week+1)
        skinEntry = SkinEntry.objects.filter(year=2021, week=week+1)
    else:
        gameEntry = GameEntry.objects.filter(year=2021, week=week)
        skinEntry = SkinEntry.objects.filter(year=2021, week=week)

    # determine if there is a skins winner set for the current week yet and the next week
    lastEnteredSkinWeekExists = SkinEntry.objects.filter(year=2021, week=week, won=True).exists()
    nextEnteredSkinWeekExists = SkinEntry.objects.filter(year=2021, week=week+1, won=True).exists()

    gameEntries = []
    skinEntries = []

    # for each game and skin entry (this weeks or next weeks depending on the above) put the names in an array
    for entry in gameEntry:
        gameEntries.append(Golfer.objects.get(id=entry.golfer).name)
    for entry in skinEntry:
        skinEntries.append(Golfer.objects.get(id=entry.golfer).name)

    # get the nexts and last weeks game (determined by the next week without scores entered)
    currentGame = Game.objects.get(year=2021, week=week+1)
    lastGame = Game.objects.get(year=2021, week=week)

    game_pot = 0

    # get look for the last weeks game winners (week determined by the last week with winners set) currently wont allow multiple winners in a week!
    # TODO: have the week update at midnight or use another system so multiple winners can be set if applicable)
    if GameEntry.objects.filter(won=True, week=week+1, year=2021).exists():
        winners = GameEntry.objects.filter(won=True, week=week, year=2021)
        for winner in winners:
               lastGameWinner.append(Golfer.objects.get(id=winner.golfer).name)      
        game_pot = (GameEntry.objects.filter(week=week, year=2021).count() * 2)/len(lastGameWinner)
    elif GameEntry.objects.filter(won=True, week=week, year=2021).exists():
        winners = GameEntry.objects.filter(won=True, week=week, year=2021)
        for winner in winners:
               lastGameWinner.append(Golfer.objects.get(id=winner.golfer).name)
        game_pot = (GameEntry.objects.filter(week=week-1, year=2021).count() * 2)/len(lastGameWinner)
    else:
        lastGameWinner.append('Not Set')

    context = {
        'week': week + 1,
        'game_pot': game_pot,
        'lastweek': week,
        'games': games,
        'gameForm': gameForm,
        'skinsForm': skinsForm,
        'gameEntries': gameEntries,
        'skinEntries': skinEntries,
        'currentGame': currentGame,
        'gameWinnerForm': gameWinnerForm,
        'lastSkinWinner': lastWeekWinner,
        'lastGameWinner': lastGameWinner,
    }

    return render(request, 'games.html', context)

#temp @cache_page(60 * 60)
def team(request, team):


    context = {
        'Scores': Scores
    }
    return render(request, 'team.html', context)

#temp @cache_page(60 * 60)
def golferSummary(request, golfer):
    year = 2021
    holes = list(range(1, 19))
    golferName = Golfer.objects.get(id=golfer).name

    # get pregenerated round data
    rounds = Round.objects.filter(year=2021)

    data = golferData(golfer)
    dataHcp = hcpData2021(golfer)
    stDevHole = stDevHoles(golfer)
    aveHoleScores = []
    handicapData = {}
    hcpPlot = []
    stDevHoleList = []
    week = getWeek()
    netDiff = getNetDiff(golfer)

    for item in list(stDevHole.values()):
        stDevHoleList.append(round(item, 3))

    fig = px.bar(y=list(stDevHole.values()), x=holes, title="Standard Deviation Per Hole",
                 text=stDevHoleList, labels={"value": "StDev", "color": "StDev"})
    fig.update_xaxes(title="Hole", fixedrange=True)
    fig.update_yaxes(title="Standard Dev.", fixedrange=True)
    fig.update_layout(margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    holeStd_div = plot(fig, output_type='div', include_plotlyjs=False,
                       config={'displayModeBar': False})

    for data2 in data['aveHoleScores']:
        aveHoleScores.append(round(data2, 2))

    fig = px.bar(y=aveHoleScores, x=holes, title="Average Over Par",
                 text=aveHoleScores, labels={"value": "Score", "color": "Score"})
    fig.update_xaxes(title="Hole", fixedrange=True)
    fig.update_yaxes(title="Over Par", fixedrange=True)
    fig.update_layout(margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False,
                    config={'displayModeBar': False})

    labels = ['Birdie', 'Par', 'Bogey', 'Double', 'Triple', 'Worse']
    pieData = {}
    for hole in range(1, 19):
        pieData[str(hole)] = []
        pieData[str(hole)].append(data['holeData']['birdies'][str(hole)])
        pieData[str(hole)].append(data['holeData']['pars'][str(hole)])
        pieData[str(hole)].append(data['holeData']['bogeys'][str(hole)])
        pieData[str(hole)].append(data['holeData']['doubles'][str(hole)])
        pieData[str(hole)].append(data['holeData']['triples'][str(hole)])
        pieData[str(hole)].append(data['holeData']['worse'][str(hole)])

    # Create subplots: use 'domain' type for Pie subplot
    pie = make_subplots(rows=6, cols=3, specs=[[{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}], [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}], [{'type': 'domain'}, {'type': 'domain'}, {
                        'type': 'domain'}], [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}], [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}], [{'type': 'domain'}, {'type': 'domain'}, {'type': 'domain'}]])

    pie.add_trace(
        go.Pie(labels=labels, values=pieData['1'], name="Hole 1"), 1, 1)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['2'], name="Hole 2"), 1, 2)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['3'], name="Hole 3"), 1, 3)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['4'], name="Hole 4"), 2, 1)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['5'], name="Hole 5"), 2, 2)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['6'], name="Hole 6"), 2, 3)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['7'], name="Hole 7"), 3, 1)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['8'], name="Hole 8"), 3, 2)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['9'], name="Hole 9"), 3, 3)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['10'], name="Hole 10"), 4, 1)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['11'], name="Hole 11"), 4, 2)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['12'], name="Hole 12"), 4, 3)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['13'], name="Hole 13"), 5, 1)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['14'], name="Hole 14"), 5, 2)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['15'], name="Hole 15"), 5, 3)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['16'], name="Hole 16"), 6, 1)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['17'], name="Hole 17"), 6, 2)
    pie.add_trace(
        go.Pie(labels=labels, values=pieData['18'], name="Hole 18"), 6, 3)

    # Use `hole` to create a donut-like pie chart
    pie.update_traces(hole=.4, hoverinfo="label+percent+name")

    pie.update_layout(showlegend=False,
                      title_text="Hole Performance",
                      # Add annotations in the center of the donut pies.
                      annotations=[dict(text='1', x=1 / 6, y=1 / 12, font_size=20, showarrow=False),
                                   dict(text='2', x=3 / 6, y=1 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='3', x=5 / 6, y=1 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='4', x=1 / 6, y=3 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='5', x=3 / 6, y=3 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='6', x=5 / 6, y=3 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='7', x=1 / 6, y=5 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='8', x=3 / 6, y=5 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='9', x=5 / 6, y=5 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='10', x=1 / 6, y=7 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='11', x=3 / 6, y=7 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='12', x=5 / 6, y=7 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='13', x=1 / 6, y=9 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='14', x=3 / 6, y=9 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='15', x=5 / 6, y=9 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='16', x=1 / 6, y=11 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='17', x=3 / 6, y=11 / 12,
                                        font_size=20, showarrow=False),
                                   dict(text='18', x=5 / 6, y=11 / 12, font_size=20, showarrow=False)])

    pie.update_layout(height=3000)

    pie_div = plot(
        pie, output_type='div', include_plotlyjs=False, config={'displayModeBar': False})

    fig = px.bar(data['holeData'], labels={
                 "index": "Hole", "variable": "Result", "value": "Percent"}, title="Score Distribution")
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    scoreDistribution_div = plot(
        fig, output_type='div', include_plotlyjs=False, config={'displayModeBar': False})

    handicapCalcData = []
    handicapScores = []

    scoresUsed = dataHcp[0]['weekScores']

    for entry in dataHcp:
        entryWeek = entry['week']
        handicapData[str(entryWeek)] = str(entry['hcp'])

    for score in scoresUsed:
        info = "Week " + str(score['week']) + " - " + str(score['weekScore'])
        handicapScores.append(info)
    if dataHcp[0]['removedMinMax']:
        info = "Max score " + str(dataHcp[0]['maxScore']) + " in week " + str(dataHcp[0]['maxScoreWeek']) + \
            " was removed from calculations."
        handicapCalcData.append(info)
        info = "Min score " + str(dataHcp[0]['minScore']) + " in week " + str(dataHcp[0]['minScoreWeek']) + \
            " was removed from calculations."
        handicapCalcData.append(info)

    lastWeek = dataHcp[1]['week']

    check = False

    while not check:
        if golferPlayed(golfer, lastWeek, year=year):
            check = True
        elif lastWeek > 1:
            lastWeek = lastWeek - 1
        else:
            # golfer never played!
            check = True

    gross = Score.objects.filter(
        golfer=golfer, week=lastWeek, year=2021).aggregate(Sum('score'))['score__sum']
    net = Score.objects.filter(golfer=golfer, week=lastWeek, year=2021).aggregate(
        Sum('score'))['score__sum'] - round(getHcp(golfer, lastWeek))

    weekData = list(range(2, week + 2))

    for week in range(2, week + 2):
        hcpPlot.append(handicapData[str(week)])

    x_diff = []
    y_diff = []
    y_diffOpp = []

    for entry in netDiff['data']:
        x_diff.append(entry['week'])
        y_diff.append(entry['hcpDiff'])
        y_diffOpp.append(entry['oppHcpDiff'])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_diff, y=y_diff, name='You'))
    fig.add_trace(go.Scatter(x=x_diff, y=y_diffOpp, name='Opp'))
    fig.update_xaxes(title="Week", fixedrange=True)
    fig.update_yaxes(title="Net Difference", fixedrange=True)
    fig.update_layout(title="Net Difference Over/Under Par", margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    netDiff_div = plot(fig, output_type='div', include_plotlyjs=False, config={
                       'displayModeBar': False})

    fig = go.Figure(data=go.Scatter(x=weekData, y=hcpPlot))
    fig.update_xaxes(title="Week", fixedrange=True)
    fig.update_yaxes(title="Handicap", fixedrange=True)
    fig.update_layout(title="Handicap By Week", margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    hcp_div = plot(fig, output_type='div', include_plotlyjs=False,
                   config={'displayModeBar': False})

    fig = go.Figure(data=go.Scatter(x=weekData, y=data['pointsArray']))
    fig.update_xaxes(title="Week", fixedrange=True)
    fig.update_yaxes(title="Points", fixedrange=True)
    fig.update_layout(title="Points Per Week", margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    points_div = plot(fig, output_type='div', include_plotlyjs=False, config={
                      'displayModeBar': False})

    fig = go.Figure(data=go.Scatter(x=weekData, y=data['scoreArray']))
    fig.update_xaxes(title="Week", fixedrange=True)
    fig.update_yaxes(title="Score", fixedrange=True)
    fig.update_layout(title="Score Per Week", margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    scores_div = plot(fig, output_type='div', include_plotlyjs=False, config={
                      'displayModeBar': False})

    context = data
    context['lastWeek'] = lastWeek
    context['holeStd_div'] = holeStd_div
    context['pie'] = pie_div
    context['netDiff'] = round(netDiff['totalHcpDiff'], 2)
    context['oppNetDiff'] = round(netDiff['totalOppHcpDiff'], 2)
    context['name'] = golferName
    context['weekGross'] = gross
    context['weekNet'] = net
    context['hcpCalcData'] = handicapCalcData
    context['hcpScores'] = handicapScores
    context['hcp_div'] = hcp_div
    context['netDiff_div'] = netDiff_div
    context['points_div'] = points_div
    context['scores_div'] = scores_div
    context['plot_div'] = plot_div
    context['scoreDistribution_div'] = scoreDistribution_div

    return render(request, "golferSummary.html", context)

#temp @cache_page(60 * 60)
def leagueStats(request):

    par = {}
    year = 2021
    holeHcp = {}
    week = getWeek()

    # populate par and hole handicap arrays for use later in the view
    for hole in range(1, 19):
        hole_data = Hole.objects.get(year=2020, hole=hole)
        par[str(hole)] = hole_data.par
        holeHcp[str(hole)] = hole_data.handicap9

    data = getLeagueStats(week, hole_hcp=holeHcp, par=par)

    ave_hole_scores = []
    hcp_data = {}
    table_head = ['<b>Name</b>']
    column_width = [40]

    for average_hole_score in data['aveHoleScores']:
        ave_hole_scores.append(round(average_hole_score, 2))

    fig = px.bar(ave_hole_scores, text=ave_hole_scores, labels={
                 "value": "Score", "color": "Score"})
    fig.update_xaxes(title="Hole", fixedrange=True)
    fig.update_yaxes(title="Over Par", fixedrange=True)
    fig.update_layout(title="League Average Over Par", showlegend=False, margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    plot_div = plot(fig, output_type='div', include_plotlyjs=False,
                    config={'displayModeBar': False})

    fig2 = px.bar(data['holeData'], labels={
                  "index": "Hole", "variable": "Result", "value": "Percent"})
    fig2.update_xaxes(fixedrange=True)
    fig2.update_yaxes(fixedrange=True)
    fig.update_layout(title="Score Distribution", margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    plot_div2 = plot(fig2, output_type='div', include_plotlyjs=False, config={
                     'displayModeBar': False})

    for wk in range(1, week + 2):
        hcp_data[str(wk)] = []

    golfer_names = []

    golfers = get2021Golfers()

    for golfer in golfers:
        golfer_names.append(Golfer.objects.get(id=golfer, year=year).name)
        for wk in range(1, week + 2):
            hcp = HandicapReal.objects.get(golfer=golfer, year=year, week=wk).handicap
            hcp_data[str(wk)].append(round(hcp, 2))

    table_data = [golfer_names]

    for wk in range(1, week + 2):
        text = '<b>' + str(wk) + '</b>'
        table_head.append(text)
        column_width.append(5)
        table_data.append(hcp_data[str(wk)])

    header_color = 'grey'
    row_even_color = 'lightgrey'
    row_odd_color = 'white'

    data2 = [go.Table(
        header=dict(values=table_head, line_color='darkslategray', fill_color=header_color, align=[
                    'left', 'center'], font=dict(color='white', size=8)),
        columnwidth=column_width,
        cells=dict(values=table_data, line_color='darkslategray', fill_color=[[row_odd_color, row_even_color, row_odd_color, row_even_color] * 5], align=['left', 'center'], font=dict(color='darkslategray', size=9)))]

    table = go.Figure(data2)

    table.update_layout(margin=dict(t=5, b=10, l=20, r=20))
    table.update_xaxes(fixedrange=True)
    table.update_yaxes(automargin=True, fixedrange=True)

    table_div = plot(table, output_type='div',
                     include_plotlyjs=False, config={'displayModeBar': False})

    table_data = [golfer_names]
    table_head = ['<b>Name</b>']

    for wk in range(1, week + 1):
        text = '<b>' + str(wk) + '</b>'
        table_head.append(text)
        table_data.append(data['pointsArray'][wk - 1])
        print(data['pointsArray'][wk - 1])

    header_color = 'grey'
    row_even_color = 'lightgrey'
    row_odd_color = 'white'

    points_table = [go.Table(
        header=dict(values=table_head,
                    line_color='darkslategray',
                    fill_color=header_color,
                    align=['left', 'center'],
                    font=dict(color='white',
                              size=8)),
                    columnwidth=column_width,
                    cells=dict(values=table_data,
                               line_color='darkslategray',
                               fill_color=[[row_odd_color, row_even_color, row_odd_color, row_even_color] * 5],
                               align=['left', 'center'],
                               font=dict(color='darkslategray',
                                         size=9)))]

    points_table_fig = go.Figure(points_table)

    points_table_fig.update_layout(margin=dict(t=5, b=10, l=20, r=20))
    points_table_fig.update_yaxes(automargin=True, fixedrange=True)
    points_table_fig.update_xaxes(fixedrange=True)

    points_div = plot(points_table_fig, output_type='div',
                      include_plotlyjs=False, config={'displayModeBar': False})

    context = data
    context['table_div'] = table_div
    context['points_div'] = points_div
    context['plot_div'] = plot_div
    context['plot_div2'] = plot_div2
    return render(request, "leagueStats.html", context)


def updateHcp(request):
    return render(request, "updateHcp.html")

#temp @cache_page(60 * 60)
def aveScores(request):
    par = {}
    holeHcp = {}

    isFront = Matchup.objects.all().filter(week=getWeek(), year=2021)[0].front

    for hole in range(1, 19):
        par[str(hole)] = Hole.objects.all().filter(year=2020, hole=hole)[0].par
        holeHcp[str(hole)] = Hole.objects.all().filter(year=2020, hole=hole)[0].handicap9

    # set the appropriate hole array
    if isFront:
        holes = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    else:
        holes = [10, 11, 12, 13, 14, 15, 16, 17, 18]

    golfers = Golfer.objects.all().filter(year=2021).exclude(team=0)
    golferData = []
    holeRange = list(range(1, 19))
    golferIndex = 0
    golferNames = []
    holeIndex = 0
    data = []

    for golfer in golfers:
        holedata = []
        holeIndex = 0

        for hole in holeRange:
            if Score.objects.filter(golfer=golfer.id, hole=hole, year=2021).exists():
                average = round(Score.objects.filter(golfer=golfer.id, hole=hole, year=2021).aggregate(
                    Avg('score'))['score__avg'] - Hole.objects.get(year=2020, hole=hole).par, 2)
            else:
                average = 0
            holedata.append(average)
            holeIndex = holeIndex + 1

        data.append(holedata)
        golferNames.append(golfer.name)
        golferIndex = golferIndex + 1

    fig = ff.create_annotated_heatmap(data, y=golferNames, x=holeRange, colorscale=[
                                      [0, 'rgb(0,128,0)'], [.5, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']], font_colors=["black", "black"], showscale=True)
    fig.update_traces(
        hovertemplate="Golfer: %{y}<br>Hole: %{x}<br>Average: %{z:.2f}<extra></extra>")
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(title="Average Scores Over/Under Par For The 2021 Season", width=1000, height=700, margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    # Make text size smaller
    for i in range(len(fig.layout.annotations)):
        fig.layout.annotations[i].font.size = 8

    plot_div_2021 = plot(fig, output_type='div', include_plotlyjs=False, config={
                         'displayModeBar': False})

    golfers = Golfer.objects.all().filter(year=2020).exclude(team=0)
    golferData = []
    holeRange = list(range(1, 19))
    golferIndex = 0
    golferNames = []
    holeIndex = 0
    data = []

    for golfer in golfers:
        holedata = []
        holeIndex = 0

        for hole in holeRange:
            if Score.objects.filter(golfer=golfer.id, hole=hole, year=2020).exists():
                average = round(Score.objects.filter(golfer=golfer.id, hole=hole, year=2020).aggregate(
                    Avg('score'))['score__avg'] - Hole.objects.get(year=2020, hole=hole).par, 2)
            else:
                average = 0
            holedata.append(average)
            holeIndex = holeIndex + 1

        data.append(holedata)
        golferNames.append(golfer.name)
        golferIndex = golferIndex + 1

    fig = ff.create_annotated_heatmap(data, y=golferNames, x=holeRange, colorscale=[
                                      [0, 'rgb(0,128,0)'], [.5, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']], font_colors=["black", "black"], showscale=True)
    fig.update_traces(
        hovertemplate="Golfer: %{y}<br>Hole: %{x}<br>Average: %{z:.2f}<extra></extra>")
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(title="Average Scores Over/Under Par For The 2020 Season", width=1000, height=700, margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    # Make text size smaller
    for i in range(len(fig.layout.annotations)):
        fig.layout.annotations[i].font.size = 8

    plot_div_2020 = plot(fig, output_type='div', include_plotlyjs=False, config={
                         'displayModeBar': False})

    golfers = Golfer.objects.all().filter(year=2019).exclude(team=0)
    golferData = []
    golferIndex = 0
    golferNames = []
    holeIndex = 0
    data = []

    for golfer in golfers:
        holedata = []
        holeIndex = 0

        for hole in holeRange:
            average = round(Score.objects.filter(golfer=golfer.id, hole=hole, year=2019).aggregate(
                Avg('score'))['score__avg'] - Hole.objects.get(year=2019, hole=hole).par, 2)
            holedata.append(average)
            holeIndex = holeIndex + 1

        data.append(holedata)
        golferNames.append(golfer.name)
        golferIndex = golferIndex + 1

    fig = ff.create_annotated_heatmap(data, y=golferNames, x=holeRange, colorscale=[
                                      [0, 'rgb(0,128,0)'], [.5, 'rgb(255,255,255)'], [1, 'rgb(255,0,0)']], font_colors=["black", "black"], showscale=True)
    fig.update_traces(
        hovertemplate="Golfer: %{y}<br>Hole: %{x}<br>Average: %{z:.2f}<extra></extra>")
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(title="Average Scores Over/Under Par For The 2019 Season", width=1000, height=700, margin=dict(
        l=5,
        r=15,
        b=5,
        t=60,
        pad=4))
    # Make text size smaller
    for i in range(len(fig.layout.annotations)):
        fig.layout.annotations[i].font.size = 8

    plot_div_2019 = plot(fig, output_type='div', include_plotlyjs=False, config={
                         'displayModeBar': False})

    return render(request, "aveScores.html", context={'plot_div_2021': plot_div_2021, 'plot_div_2020': plot_div_2020, 'plot_div_2019': plot_div_2019})

def addSub(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = SubForm(request.POST)

        if form.is_valid():
            Subrecord.objects.update_or_create(
                absent_id=form.cleaned_data['absent'].id,
                sub_id=form.cleaned_data['sub'].id,
                week=form.cleaned_data['week'],
                year=form.cleaned_data['year']
            )

            # redirect to a new URL:
            return HttpResponseRedirect('/addsub/')
            pass
    # if a GET (or any other method) we'll create a blank form
    else:
        form = SubForm()

    return render(request, 'addSub.html', {'form': form})


def enterSchedule(request):
    # if this is a POST request we need to process the form data

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ScheduleForm(request.POST)

        if form.is_valid():
            if Matchup.objects.filter(Q(year=form.cleaned_data['year']) & Q(week=form.cleaned_data['week']) & ((Q(team1=form.cleaned_data['team1']) | Q(team2=form.cleaned_data['team1'])) & (Q(team1=form.cleaned_data['team2']) | Q(team2=form.cleaned_data['team2'])))).exists():
                match = Matchup.objects.get(Q(year=form.cleaned_data['year']) & Q(week=form.cleaned_data['week']) & ((Q(team1=form.cleaned_data['team1']) | Q(team2=form.cleaned_data['team1'])) & (Q(team1=form.cleaned_data['team2']) | Q(team2=form.cleaned_data['team2']))))
                match.team1 = form.cleaned_data['team1']
                match.team2 = form.cleaned_data['team2']
                match.front = form.cleaned_data['front']

                match.save()
            else:
                match = Matchup.objects.create(year=form.cleaned_data['year'], week=form.cleaned_data['week'], team1=form.cleaned_data['team1'], team2=form.cleaned_data['team2'], front=form.cleaned_data['front'])

            # redirect to a new URL:
            return HttpResponseRedirect('/enterSchedule/')
            pass
    # if a GET (or any other method) we'll create a blank form
    else:
        form = ScheduleForm()

    return render(request, 'enterSchedule.html', {'form': form})


def createGolfer(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = GolferForm(request.POST)

        if form.is_valid():
            Golfer.objects.update_or_create(
                name=form.cleaned_data['name'],
                team=form.cleaned_data['team'],
                year=form.cleaned_data['year']
            )

            # redirect to a new URL:
            return HttpResponseRedirect('/creategolfer/')
            pass
    # if a GET (or any other method) we'll create a blank form
    else:
        form = GolferForm()

    return render(request, 'createGolfer.html', {'form': form})

def addRound(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = RoundForm(request.POST)

        if form.is_valid():

            schedule = Matchup.objects.all().filter(
                week=form.cleaned_data['week'], year=2021)[0]

            # determine if playing front or back
            isFront = schedule.front

            # set the appropriate hole array
            if isFront:
                holes = [1, 2, 3, 4, 5, 6, 7, 8, 9]
            else:
                holes = [10, 11, 12, 13, 14, 15, 16, 17, 18]

            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[0], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[0],
                    score=form.cleaned_data['hole1'],
                    tookMax=form.cleaned_data['tookMax1'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[1], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[1],
                    score=form.cleaned_data['hole2'],
                    tookMax=form.cleaned_data['tookMax2'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[2], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[2],
                    score=form.cleaned_data['hole3'],
                    tookMax=form.cleaned_data['tookMax3'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[3], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[3],
                    score=form.cleaned_data['hole4'],
                    tookMax=form.cleaned_data['tookMax4'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[4], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[4],
                    score=form.cleaned_data['hole5'],
                    tookMax=form.cleaned_data['tookMax5'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[5], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[5],
                    score=form.cleaned_data['hole6'],
                    tookMax=form.cleaned_data['tookMax6'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[6], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[6],
                    score=form.cleaned_data['hole7'],
                    tookMax=form.cleaned_data['tookMax7'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[7], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[7],
                    score=form.cleaned_data['hole8'],
                    tookMax=form.cleaned_data['tookMax8'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )
            if not Score.objects.all().filter(golfer=form.cleaned_data['golfer'].id, week=form.cleaned_data['week'], hole=holes[8], year=form.cleaned_data['year']).exists():
                Score.objects.update_or_create(
                    golfer=form.cleaned_data['golfer'].id,
                    hole=holes[8],
                    score=form.cleaned_data['hole9'],
                    tookMax=form.cleaned_data['tookMax9'],
                    week=form.cleaned_data['week'],
                    year=form.cleaned_data['year']
                )

            # redirect to a new URL:
            return HttpResponseRedirect('/addround/')
            pass

    # if a GET (or any other method) we'll create a blank form
    else:
        form = RoundForm()

    return render(request, 'addRound.html', {'form': form})

#temp @cache_page(60 * 60)
def weekSummary(request, week):
    year = 2021
    par = {}
    holeHcp = {}

    isFront = Matchup.objects.filter(week=week, year=year).first().front

    for hole in range(1, 19):
        par[str(hole)] = Hole.objects.get(year=2020, hole=hole).par
        holeHcp[str(hole)] = Hole.objects.get(year=2020, hole=hole).handicap9

    # set the appropriate hole array
    if isFront:
        holes = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    else:
        holes = [10, 11, 12, 13, 14, 15, 16, 17, 18]

    h1 = []
    h2 = []
    h3 = []
    h4 = []
    h5 = []
    h6 = []
    h7 = []
    h8 = []
    h9 = []
    gross = []
    net = []
    chartData = getWeeklyScores(week, year)

    fig = px.bar(chartData[1], x=chartData[0], y=chartData[1],
                 title="Strokes Over Par", text=chartData[1])
    fig.update_layout(margin=dict(t=60, b=40, l=40, r=40))
    fig.update_xaxes(title="", fixedrange=True)
    fig.update_yaxes(title="", fixedrange=True, automargin=True)
    plot_div = plot(fig, output_type='div', include_plotlyjs=False,
                    config={'displayModeBar': False})

    holeData = []
    teamsGone = []
    teamsList = []
    oppList = []

    chart = getWeekScores(week)

    chart = sorted(chart, key=itemgetter('Gross'))

    # set the appropriate hole array
    if isFront:
        tableHead = ['<b>Name</b>', '<b>1</b>', '<b>2</b>', '<b>3</b>', '<b>4</b>',
                     '<b>5</b>', '<b>6</b>', '<b>7</b>', '<b>8</b>', '<b>9</b>', '<b>G</b>', '<b>N</b>']
        string = "Front 9"
    else:
        tableHead = ['<b>Name</b>', '<b>10</b>', '<b>11</b>', '<b>12</b>', '<b>13</b>',
                     '<b>14</b>', '<b>15</b>', '<b>16</b>', '<b>17</b>', '<b>18</b>', '<b>G</b>', '<b>N</b>']
        string = "Back 9"

    # get the hole data in a list
    for hole in holes:
        holeData.append(Hole.objects.get(hole=hole, year=2020))

    # get the golfers for the season excluding the subs
    golfers = Golfer.objects.all().filter(year=year).exclude(team=0)

    for golfer in golfers:

        # gets sub if there was one for the golfer that week
        golfer_id = getSub(golfer.id, week)

        h1.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[0]).score)
        h2.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[1]).score)
        h3.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[2]).score)
        h4.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[3]).score)
        h5.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[4]).score)
        h6.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[5]).score)
        h7.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[6]).score)
        h8.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[7]).score)
        h9.append(Score.objects.get(golfer=golfer_id, week=week, year=year, hole=holes[8]).score)

        gross.append(getGross(golfer_id, week, year=year))
        net.append(getNet(golfer_id, week, year=year))

    headerColor = 'grey'
    rowEvenColor = 'lightgrey'
    rowOddColor = 'white'
    count = 0

    data = [go.Table(
        header=dict(values=tableHead,
            line_color='darkslategray',
            fill_color=headerColor,
            align=['left', 'center'],
            font=dict(color='white',
                size=8)),
        columnwidth=[40, 5, 5, 5, 5, 5, 5, 5, 5, 5, 10, 10],
        cells=dict(
            values=[chartData[0], h1, h2, h3, h4, h5, h6, h7, h8, h9, gross, net],
            line_color='darkslategray',
            # 2-D list of colors for alternating rows
            fill_color=[[rowOddColor, rowEvenColor,
                         rowOddColor, rowEvenColor] * 5],
            align=['left', 'center'],
            font=dict(color='darkslategray',
                size=9)
        ))]

    table = go.Figure(data)

    table.update_layout(margin=dict(t=5, b=40, l=20, r=20))
    table.update_xaxes(fixedrange=True)
    table.update_yaxes(fixedrange=True, automargin=True)

    table_div = plot(table, output_type='div',
                     include_plotlyjs=False, config={'displayModeBar': False})

    # get the opponents team
    matchups = Matchup.objects.all().filter(week=week, year=year)

    week_teams = []
    home_golfers = []
    away_golfers = []

    for matchup in matchups:

        team1 = matchup.team1
        team2 = matchup.team2

        golfers = getTeamGolfers(team1, week)

        opps = getTeamGolfers(team2, week)

        week_teams.append(team1)
        week_teams.append(team2)
        home_golfers.append(golfers)
        away_golfers.append(opps)

    total = 0

    for hole in holeData:
        total = total + hole.yards

    data = (home_golfers, away_golfers)
    data = zip(data[0], data[1])

    context = {
        'string': string,
        'is_front': isFront,
        'hole_hcp': holeHcp,
        'chart': chart,
        'holeData': holeData,
        'total': total,
        'week': week,
        'golfers': golfers,
        'teams': week_teams,
        'data': data,
        'plot_div': plot_div,
        'table_div': table_div,
        'year': year,
    }

    return render(request, 'weekSummary.html', context)


# one parameter named request
def upload(request):
    # declaring template
    template = "upload.html"
    data = Score.objects.all()
# prompt is a context variable that can have different values      depending on their context
    prompt = {
        'order': 'Order of the CSV should be hole, par, handicap, handicap9, yards.',
        'score': data
    }
    # GET request returns the value of the data with the specified key.
    if request.method == "GET":
        return render(request, template, prompt)
    csv_file = request.FILES['file']
    # let's check if it is a csv file
    if not csv_file.name.endswith('.csv'):
        messages.error(request, 'THIS IS NOT A CSV FILE')

    data_set = csv_file.read().decode('UTF-8')

    # setup a stream which is when we loop through each line we are able to handle a data in a stream
    io_string = io.StringIO(data_set)
    next(io_string)
    for column in csv.reader(io_string, delimiter=',', quotechar="|"):
        _, created = Score.objects.update_or_create(
            id=column[0],
            golfer=column[1],
            handicap=column[2],
            week=column[3],
            year=column[4]
        )
    context = {}
    return render(request, template, context)
