from django import forms
from django.db.models import Q
from main.models import *
from main.helper import *
from main.functions import *


def getWeekChoices():
    weeks = []

    for i in range(1, getWeek() + 2):
        weeks.insert(0, (i, "Week " + str(i)))

    return weeks


class GolferModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
         return obj.name

class GolferModelChoiceField2(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return Golfer.objects.get(id=obj.golfer).name


YEARS = [
    (2021, '2021'),
    (2020, '2020'),
    (2019, '2019')
]

WEEKS = [
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
    (5, '5'),
    (6, '6'),
    (7, '7'),
    (8, '8'),
    (9, '9'),
    (10, '10'),
    (11, '11'),
    (12, '12'),
    (13, '13'),
    (14, '14'),
    (15, '15'),
    (16, '16'),
    (17, '17'),
    (18, '18'),
    (19, '19'),
    (20, '20')
]


class GolferForm(forms.Form):
    name = forms.CharField(label='Name', strip=True)
    team = forms.IntegerField(label="Team", min_value=0, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    year = forms.ChoiceField(choices=YEARS, label='Year', widget=forms.Select(attrs={'class' : 'form-control'}))


class GameEntryForm(forms.Form):
    golfer_game = GolferModelChoiceField(queryset=Golfer.objects.all().filter(year=2021), label='Golfer', widget=forms.Select(attrs={'class' : 'form-control'}))
    week = forms.ChoiceField(choices=getWeekChoices(), initial=getWeek()+1, label='Week', widget=forms.Select(attrs={'class' : 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['week'].choices = getWeekChoices()

class GameWinnerForm(forms.Form):
    if not GameEntry.objects.filter(won=True, week=getWeek(), year=2021).exists():
        game_winner = GolferModelChoiceField2(queryset=GameEntry.objects.filter(week=getWeek(), year=2021), label='Winner', widget=forms.Select(attrs={'class' : 'form-control'}))
    else:
        game_winner = GolferModelChoiceField2(queryset=GameEntry.objects.filter(week=getWeek()+1, year=2021), label='Winner', widget=forms.Select(attrs={'class' : 'form-control'}))

class SkinEntryForm(forms.Form):
    golfer_skins = GolferModelChoiceField(queryset=Golfer.objects.all().filter(year=2021), label='Golfer', widget=forms.Select(attrs={'class' : 'form-control'}))
    week = forms.ChoiceField(choices=getWeekChoices(), initial=getWeek()+1, label='Week', widget=forms.Select(attrs={'class' : 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['week'].choices = getWeekChoices()


class ScheduleForm(forms.Form):
    week = forms.ChoiceField(choices=WEEKS, label='Week', widget=forms.Select(attrs={'class' : 'form-control'}))
    team1 = forms.IntegerField(label="Team 1", min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    team2 = forms.IntegerField(label="Team 2", min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    year = forms.ChoiceField(choices=YEARS, label='Year', widget=forms.Select(attrs={'class' : 'form-control'}))
    front = forms.BooleanField(required=False)

class SubForm(forms.Form):
    week = forms.ChoiceField(choices=getWeekChoices(), label='Week', widget=forms.Select(attrs={'class' : 'form-control'}))
    absent = GolferModelChoiceField(queryset=Golfer.objects.all().filter(year=2021).exclude(team=0), label='Absent', widget=forms.Select(attrs={'class' : 'form-control'}))
    sub = GolferModelChoiceField(queryset=Golfer.objects.all().filter(Q(team=0) & Q(year=2021)), label='Sub', widget=forms.Select(attrs={'class' : 'form-control'}))
    year = forms.ChoiceField(choices=YEARS, label='Year', widget=forms.Select(attrs={'class' : 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        weeks = getWeekChoices()
        weeks.append((weeks[0][0]+1, "Week " + str((weeks[0][0]+1))))
        self.fields['week'].choices = weeks

class RoundForm(forms.Form):
    golfer = GolferModelChoiceField(queryset=Golfer.objects.all().filter(Q(year=2021) | Q(team=0) & Q(year=2021)), label='Golfer', widget=forms.Select(attrs={'class' : 'form-control'}))
    hole1 = forms.IntegerField(label='Hole 1', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole2 = forms.IntegerField(label='Hole 2', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole3 = forms.IntegerField(label='Hole 3', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole4 = forms.IntegerField(label='Hole 4', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole5 = forms.IntegerField(label='Hole 5', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole6 = forms.IntegerField(label='Hole 6', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole7 = forms.IntegerField(label='Hole 7', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole8 = forms.IntegerField(label='Hole 8', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    hole9 = forms.IntegerField(label='Hole 9', max_value=10, min_value=1, widget=forms.NumberInput(attrs={'class' : 'form-control'}))
    tookMax1 = forms.BooleanField(required=False)
    tookMax2 = forms.BooleanField(required=False)
    tookMax3 = forms.BooleanField(required=False)
    tookMax4 = forms.BooleanField(required=False)
    tookMax5 = forms.BooleanField(required=False)
    tookMax6 = forms.BooleanField(required=False)
    tookMax7 = forms.BooleanField(required=False)
    tookMax8 = forms.BooleanField(required=False)
    tookMax9 = forms.BooleanField(required=False)
    week = forms.ChoiceField(choices=getWeekChoices(), label='Week', widget=forms.Select(attrs={'class' : 'form-control'}))
    year = forms.ChoiceField(choices=YEARS, label='Year', widget=forms.Select(attrs={'class' : 'form-control'}))


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['week'].choices = getWeekChoices()
