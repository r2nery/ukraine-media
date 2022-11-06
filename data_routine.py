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
    # Guardian().scraper() # opinion on /commentisfree/
    # RT().scraper()
    # Fox().scraper() # opinion on /opinion/
    # Reuters().scraper()
    # AP().scraper()
    # Mirror().scraper() # few articles
    # Express().scraper()  
    # Huffpost().scraper()

    # CBS().scraper() # needs run from scratch
    # DailyMail().scraper() # needs run from scratch
    # ABC().scraper() # needs run from scratch
    NYT().scraper()

    
    
    # NTR().routine(period=7, topicnum=30, vocabsize=10000, num_iter=2000)
    pass
