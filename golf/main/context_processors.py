from main.functions import getWeek, getGolferIds, getSubIds


def weekList(request):

    week = getWeek()

    list = range(1, week+1)

    return {
        'weekList': list
    }


def golferList(request):

    golfers = getGolferIds()

    return {
        'golferList': golfers
    }


def subList(request):

    golfers = getSubIds()

    return {
        'subList': golfers
    }
