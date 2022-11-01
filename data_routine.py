import os
from metrics.ntr import NTR
from scrapers.ap import AP
from scrapers.rt import RT 
from scrapers.fox import Fox
from scrapers.nbc import NBC
from scrapers.cnn import CNN
from scrapers.mirror import Mirror
from scrapers.reuters import Reuters
from scrapers.express import Express
from scrapers.huffpost import Huffpost
from scrapers.guardian import Guardian
from scrapers.dailymail import DailyMail

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))

if __name__ == "__main__":
    # CNN().scraper()  # OK ## REMADE
    # RT().scraper() # OK ## REMADE
    Fox().scraper()
    # Guardian().scraper()  # OK
    # Reuters().scraper()  # OK
    # DailyMail().scraper()  # OK
    # AP().scraper() # OK, NEEDS RUN FROM SCRATCH
    # NBC().scraper() # OK, few articles (jul-22)
    # Mirror().scraper() # OK, few articles, needs title fix (feb-22)
    # Express().scraper()  # OK, NEEDS RUN FROM SCRATCH
    # Huffpost().scraper() # OK, NEEDS RUN FROM SCRATCH, almost all news are AP
    # NTR().routine(period=7, topicnum=30, vocabsize=10000, num_iter=2000)
    pass
