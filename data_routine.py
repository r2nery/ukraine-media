import os
from datetime import datetime
from metrics import utils
from metrics.ntr import NTR
from scrapers.ap import AP
from scrapers.fox import Fox
from scrapers.cnn import CNN
from scrapers.abc import ABC
from scrapers.cbs import CBS
from scrapers.nyt import NYT
from scrapers.mirror import Mirror
from scrapers.reuters import Reuters
from scrapers.express import Express
from scrapers.huffpost import Huffpost
from scrapers.guardian import Guardian
from scrapers.dailymail import DailyMail

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))


if __name__ == "__main__":

    # NYT().scraper()  # opinion on /opinion/'
    # CNN().scraper()
    # Guardian().scraper()  # opinion on /commentisfree/
    # Fox().scraper()  # opinion on /opinion/
    # Reuters().scraper()
    # AP().scraper()
    # CBS().scraper() 
    # ABC().scraper()
    # Express().scraper()
    # Mirror().scraper()  # few articles
    # DailyMail().scraper()  # comments ok

    # utils.unite_sources()
    for scale in [1,3,5,7,10,15,20,25,30]:
        NTR().routine(date_start="2022-04-01", date_end="2022-12-29", kld_days_window=scale, topicnum=30, vocabsize=10000, num_iter=700)
