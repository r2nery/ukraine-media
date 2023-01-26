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
        0.08,
        # 1,
        # 5, 
        # 10,
        # 30,
    ]

    for scale in scales:
        NTR().routine(date_start="2022-04-01", date_end="2022-12-31", kld_days_window=scale, topicnum=200, vocabsize=10000, num_iter=1500)

    # #def kld_window(self, dataframe, date_start, date_end, kld_days_window):
    #     df = pd.read_csv(os.path.join(ROOT_DIR, "data", "All" + ".csv"))
    #     NTR().kld_window(df, date_start="2022-04-01", date_end="2022-12-31", kld_days_window=scale)
