import os
from metrics.ntr import NTR
from scrapers.ap import AP
from scrapers.rt import RT
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

    # CNN().scraper()
    # Guardian().scraper()  # opinion on /commentisfree/
    # RT().scraper()
    # Fox().scraper()  # opinion on /opinion/
    # Reuters().scraper()
    # Mirror().scraper()  # few articles
    Express().scraper()
    # Huffpost().scraper()
    # NYT().scraper()  # opinion on /opinion/ # error updating
    # AP().scraper()
    # CBS().scraper()  # needs run from scratch
    # DailyMail().scraper()
    # ABC().scraper()  # needs run from scratch

    NTR().routine(period=7, topicnum=10, vocabsize=10000, num_iter=100)
    pass
