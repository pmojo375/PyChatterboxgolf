from main.functions import getWeek, getGolferObjects


def weekList(request):

    week = getWeek()

    list = range(1, week+1)

    return {
        'weekList': list
    }


def golferList(request):

    golfers = getGolferObjects(2021)

    return {
        'golferList': golfers
    }
