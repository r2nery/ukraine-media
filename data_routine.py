import os
from datetime import datetime
from metrics_utilities import utils
from metrics_utilities.ntr import NTR
from scrapers.ap import AP
from scrapers.fox import Fox
from scrapers.cnn import CNN
from scrapers.abc import ABC
from scrapers.cbs import CBS
from scrapers.nyt import NYT
from scrapers.mirror import Mirror
from scrapers.reuters import Reuters
from scrapers.express import Express
from scrapers.guardian import Guardian
from scrapers.dailymail import DailyMail
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))


if __name__ == "__main__":

    # # NYT().scraper()  # opinion on /opinion/, needs cookies
    # CNN().scraper()
    # Guardian().scraper()  # opinion on /commentisfree/
    # Fox().scraper()  # opinion on /opinion/
    # Reuters().scraper()
    # AP().scraper()
    # CBS().scraper()
    # ABC().scraper()
    # Express().scraper()
    # Mirror().scraper()
    # DailyMail().scraper()

    # utils.unite_sources()

    # NTR().lda_only(100, 10000, 700)

    scales = [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        13,
        19,
        26,
        37,
        51,
        71,
        100,
        138,
        193,
        268,
        372,
        517,
        719,
        1000,
    ]

    for scale in scales:
        NTR().routine(kld_days_window=scale, topicnum=200, vocabsize=10000, num_iter=300)
