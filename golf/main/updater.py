from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from main.functions import *

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(allScoresIn, 'interval', minutes=5)
    scheduler.start()