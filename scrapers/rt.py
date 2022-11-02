import os
import warnings
import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
RT_DIR = os.path.join(ROOT_DIR, "data", "RT.csv")


class RT:
    def __init__(self) -> None:
        self.source = "RT"
        self.dir = RT_DIR

    def seleniumParams(self):
        s = Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE, path=ROOT_DIR).install())
        o = webdriver.ChromeOptions()
        # o.add_argument("headless")
        self.driver = webdriver.Chrome(service=s, options=o)
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)
        self.wait = WebDriverWait(self.driver, 30, ignored_exceptions=ignored_exceptions)

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            self.from_scratch = True
        else:
            self.old_data = pd.read_csv(self.dir)
            self.from_scratch = False

    def concatData(self):
        result = pd.concat([self.old_data, self.new_data])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def URLFetcher(self):
        self.urls = []
        self.unique_urls = []

        if not self.from_scratch:
            last_urls = [self.old_data.iloc[0, 1]]
        elif self.from_scratch:
            last_urls = [""]
            print(f"-> {self.source}: No CSV file found. Creating...")

        agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        with alive_bar(title=f"-> {self.source}: Fetching URLs", bar=None, spinner="dots", force_tty=True) as bar:
            inc_list = ["/world-news/", "/politics/"]
            session = requests.Session()
            for i in range(0, 2):
                source = "https://www.rt.com/listing/category.russia.xwidget.russiaWidgets/prepare/last-news/500/" + str(i)
                html_text = session.get(source, headers=agent).text
                soup = BeautifulSoup(html_text, "lxml")
                articles = soup.find_all("div", class_="list-card__content--title link_hover")
                for article in articles:
                    url = article.find("a")
                    url = "https://www.rt.com" + url["href"]
                    if url in last_urls:
                        break
                    # if any(s in url for s in inc_list):
                    self.urls.append(url)
                    bar()
                if url in last_urls:
                    break
                self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        bodies, titles, dates, urls = [], [], [], []
        rep = {}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = requests.Session()
            for url in self.unique_urls:
                try:
                    article_tag = ["article__text text"]
                    date_tag = ["date date_article-header"]
                    title_tag = ["article__heading"]
                    html_text = session.get(url, headers=agent).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h1", class_=title_tag).text
                    title = " ".join(title.split())
                    date = soup.find("span", class_=date_tag).text
                    date = str(datetime.strptime(date[:-8], "%d %b, %Y").date())
                    article = soup.find("div", class_=article_tag)
                    paragraphs = article.find_all("p")
                    body = ""
                    for i in range(0, len(paragraphs)):
                        body += " " + paragraphs[i].text
                    body = replaceAll(body, rep)
                    bodies.append(" ".join(body.split()))
                    titles.append(title)
                    urls.append(url)
                    dates.append(date)
                    bar()
                except Exception as e:
                    print(f"URL couldn't be scraped: {url} because {e}")
                    pass
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        self.new_data = data

    def scraper(self):
        self.fromScratch()
        self.URLFetcher()
        self.articleScraper()
        data = self.concatData()
        lenAfter = len(data) - len(self.old_data)
        if lenAfter == 0:
            print(f"-> No new articles found. Total articles: {len(data)}")
        else:
            print(f"-> {lenAfter} new articles saved to {self.source}.csv! Total articles: {len(data)}")
        print("")
        data.to_csv(self.dir, index=True)

        return data
