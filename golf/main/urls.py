from django.urls import path
from main import views

urlpatterns = [
    path('', views.main, name='main'),
    path('upload-csv/', views.upload, name="upload"),
    path('<int:week>/', views.weekSummary, name="weekSummary"),
    path('golfer/<int:golfer>/', views.golferSummary, name="golferSummary"),
    path('addround/', views.addRound, name="addRound"),
    path('addsub/', views.addSub, name="addSub"),
    path('creategolfer/', views.createGolfer, name="createGolfer"),
    path('averageScores/', views.aveScores, name='aveScores'),
    path('updateHcp/', views.updateHcp, name='updateHcp'),
    path('leagueStats/', views.leagueStats, name='leagueStats'),
    path('games/', views.games, name='games'),
    path('enterSchedule/', views.enterSchedule, name='enterSchedule'),
]
