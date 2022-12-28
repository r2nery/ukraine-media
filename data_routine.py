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

    # Collect dates at url stage
    # add initial date to init of classes
    # CNN().scraper()
    # Guardian().scraper()  # opinion on /commentisfree/
    # Fox().scraper()  # opinion on /opinion/
    # Reuters().scraper()
    # Huffpost().scraper()
    # AP().scraper()
    # # CBS().scraper() # Run from scratch to update
    # ABC().scraper()
    # # NYT().scraper()  # opinion on /opinion/

    # Express().scraper()
    # Mirror().scraper()  # few articles
    # DailyMail().scraper() # comments ok

    # utils.unite_sources()
    NTR().routine(date_start="2022-03-01", date_end="2022-08-01",
                  kld_days_window=30, topicnum=30, vocabsize=10000,
                  num_iter=300)
    