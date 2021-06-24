from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from main.functions import *

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(makeRounds, 'cron', hour=23)
    scheduler.add_job(allScoresIn, 'interval', minutes=1)
    scheduler.start()