from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from main.functions import *
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# in minutes
INTERVAL = 5

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(allScoresIn, 'interval', minutes=INTERVAL)
    scheduler.start()
    logger.info(f'Background job started at {INTERVAL} minute intervals')