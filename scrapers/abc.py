import os
import warnings
import json
import requests
import regex as re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
ABC_DIR = os.path.join(ROOT_DIR, "data", "ABC.csv")


class ABC:
    def __init__(self) -> None:
        self.source = "ABC"
        self.dir = ABC_DIR

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            return True
        else:
            self.old_data = pd.read_csv(self.dir)
            return False

    def concatData(self):
        result = pd.concat([self.old_data, self.new_data])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def URLFetcher(self):
        self.urls = []
        self.last_url_found = False

        if not self.fromScratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            print(f"-> {self.source}: No CSV file found. Creating...")
            last_urls = ["https://abcnews.go.com/Politics/bail-revoked-rudy-giuliani-associate-lev-parnas\/story?id=67670466"]

        with alive_bar(title=f"-> {self.source}: Fetching URLs", bar=None, spinner="dots", force_tty=True) as bar:
            source = "https://abcnews.go.com/meta/api/search?q=ukraine%20russia&limit=125&sort=date&totalrecords=true&offset="
            session = requests.Session()
            for page in range(0, 5): #75
                exc_list = ["technology", "sports", "business", "theview", "gma", "MovingImage","Video","WireStory"]
                url_exc_list = ["transcript"]
                r = session.get(source + str(page * 125)).json()
                for i in r["item"]:
                    exclusions = [i["category"]["text"],i["dcType"][0],i["dcType"][1]]
                    url = i["link"]
                    if not any(s in exclusions for s in exc_list) and not any(s in url for s in url_exc_list):
                        self.urls.append(url)
                        bar()
                    if url in last_urls:
                        break
                if url in last_urls:
                    break
            self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        titles, bodies, dates, urls = [], [], [], []
        rep = {"": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = requests.Session()
            for url in self.unique_urls:
                try:
                    if len(urls) % 20 == 0:
                        session = requests.Session()
                    html_text = session.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    info_json = json.loads(soup.find("script", attrs={"type": "application/ld+json"}).text)
                    title = info_json["headline"]
                    title = " ".join(title.split())
                    date = info_json["datePublished"][:10]
                    paragraphs = soup.select("article > p")
                    body = ""
                    for i in range(0, len(paragraphs)):  # excluding last paragraph (journalist information)
                        body += " " + paragraphs[i].text
                    body = replaceAll(body, rep)
                    body = " ".join(body.split())
                    bodies.append(body)
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
