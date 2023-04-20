import os
import warnings
import json
import requests
import regex as re
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
ABC_DIR = os.path.join(ROOT_DIR, "data", "raw", "ABC.csv")


class ABC:
    def __init__(self) -> None:
        self.source = "ABC"
        self.dir = ABC_DIR
        self.urls = []
        self.old_data = None
        self.new_data = None

    def from_scratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            return True

        self.old_data = pd.read_csv(self.dir)
        return False

    def concat_data(self):
        result = pd.concat([self.old_data, self.new_data])
        result = result.dropna()
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def url_fetcher(self):
        self.urls = []

        if not self.from_scratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            print(f"-> {self.source}: No CSV file found. Creating...")
            last_urls = [
                "https://abcnews.go.com/Politics/bail-revoked-rudy-"
                "giuliani-associate-lev-parnas/story?id=67670466"
            ]

        with alive_bar(
            title=f"-> {self.source}: Fetching URLs",
            bar=None,
            spinner="dots",
            force_tty=True,
        ) as bar:
            source = (
                "https://abcnews.go.com/meta/api/search?q=ukraine%20"
                "russia&limit=125&sort=date&totalrecords=true&offset="
            )
            print(source)
            session = requests.Session()
            for page in range(0, 75):  # 75
                exc_list = [
                    "technology",
                    "sports",
                    "business",
                    "theview",
                    "gma",
                    "MovingImage",
                    "Video",
                    "WireStory",
                ]
                url_exc_list = ["transcript"]
                request = session.get(source + str(page * 125)).json()
                for i in request["item"]:
                    exclusions = [i["category"]["text"], i["dcType"][0], i["dcType"][1]]
                    url = i["link"]
                    if not any(s in exclusions for s in exc_list) and not any(
                        s in url for s in url_exc_list
                    ):
                        self.urls.append(url)
                        bar()
                    if url in last_urls:
                        break
                if url in last_urls:
                    break
            self.urls = list(dict.fromkeys(self.urls))

    def article_scraper(self):
        titles, bodies, dates, urls = [], [], [], []
        rep = {"": ""}

        def replace_all(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(
            len(self.urls),
            title=f"-> {self.source}: Article scraper",
            length=20,
            spinner="dots",
            bar="smooth",
            force_tty=True,
        ) as bar:
            session = requests.Session()
            for url in self.urls:
                try:
                    if len(urls) % 20 == 0:
                        session = requests.Session()
                    html_text = session.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    source = soup.find("script", attrs={"type": "application/ld+json"})
                    info_json = json.loads(source.text)
                    title = info_json["headline"]
                    title = " ".join(title.split())
                    date = info_json["datePublished"][:10]
                    paragraphs = soup.select("article > p")
                    body = ""
                    for _, paragraph in enumerate(paragraphs):
                        body += " " + paragraph.text
                    body = replace_all(body, rep)
                    body = " ".join(body.split())
                    bodies.append(body)
                    titles.append(title)
                    urls.append(url)
                    dates.append(date)
                    bar()
                except Exception as exc:
                    print(f"URL couldn't be scraped: {url} because {exc}")
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        self.new_data = data

    def scraper(self):
        self.url_fetcher()
        self.article_scraper()
        data = self.concat_data()
        len_after = len(data) - len(self.old_data)
        if len_after == 0:
            print(f"-> No new articles found. Total articles: {len(data)}")
        else:
            print(
                f"-> {len_after} new articles saved to {self.source}.csv! Total articles: {len(data)}"
            )
        print("")
        data.to_csv(self.dir, index=True)

        return data
