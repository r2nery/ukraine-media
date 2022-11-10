import os
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

    # CNN().scraper()
    # Guardian().scraper()  # opinion on /commentisfree/
    # Fox().scraper()  # opinion on /opinion/
    # Reuters().scraper()
    # Mirror().scraper()  # few articles
    # Express().scraper()
    # Huffpost().scraper()
    # NYT().scraper()  # opinion on /opinion/
    # AP().scraper()
    # CBS().scraper()
    # DailyMail().scraper()
    # ABC().scraper()

    NTR().routine(date_start="2022-03-01", date_end="2022-08-01", kld_days_window=3, topicnum=30, vocabsize=10000, num_iter=300)
    pass
