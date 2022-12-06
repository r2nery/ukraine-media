import os
import warnings
import requests
import regex as re
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar
import json

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
REUTERS_DIR = os.path.join(ROOT_DIR, "data", "Reuters.csv")


class Reuters:
    def __init__(self) -> None:
        self.source = "Reuters"
        self.dir = REUTERS_DIR
        self.urls = []
        self.old_data = None
        self.new_data = None

    def from_scratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            return True
        else:
            self.old_data = pd.read_csv(self.dir)
            return False

    def concat_data(self):
        result = pd.concat([self.old_data, self.new_data])
        result = result.dropna()
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def replace_all(self, text, dic):
        for i, j in dic.items():
            text = text.replace(i, j)
        return text

    def url_fetcher(self):
        self.urls = []

        if not self.from_scratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            last_urls = [
                "https://www.reuters.com/article/us-russia-wikipedia/"
                "russia-to-upgrade-homegrown-encyclopedia-after-"
                "putin-pans-wikipedia-idUSKBN1Y61DA",
                "https://www.reuters.com/article/us-ukraine-crisis-summit-communique/"
                "russia-and-ukraine-leaders-in-first-talks-agree-"
                "to-exchange-prisoners-idUSKBN1YD2GA",
            ]
            print(f"-> {self.source}: No CSV file found. Creating...")

        with alive_bar(
            title=f"-> {self.source}: Fetching URLs",
            bar=None,
            spinner="dots",
            force_tty=True,
        ) as bar:
            exc_list = ["/tennis/"]
            tags = ["ukraine", "russia"]
            for tag in tags:
                session = requests.Session()
                for page in range(1, 1300):  # 1300
                    source = (
                        "https://www.reuters.com/news/archive/" + tag + "?view=page"
                        "&page=" + str(page) + "&pageSize=10"
                    )
                    html_text = session.get(source).text
                    soup = BeautifulSoup(html_text, "lxml")
                    headline_list = soup.find("div", class_="column1 col col-10")
                    headlines = headline_list.find_all("div", class_="story-content")
                    for headline in headlines:
                        page_urls = headline.find_all("a", href=True)
                        url = "https://www.reuters.com" + page_urls[0]["href"]
                        if url in last_urls:
                            break
                        elif not any(s in url for s in exc_list):
                            self.urls.append(url)
                            bar()
                    if url in last_urls:
                        break
            self.urls = list(dict.fromkeys(self.urls))

    def article_scraper(self):
        bodies, titles, dates, urls = [], [], [], []
        rep = {
            "Our Standards: The Thomson Reuters Trust Principles.": "",
            "read more": "",
            "All quotes delayed a minimum of 15 minutes. See here for a complete list of "
            "exchanges and delays.": "",
            "© 2022 Reuters. All rights reserved": "",
            "2022 Reuters. All rights reserved": "",
        }

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
                        session = requests.Session()  # restarting session every 20 urls
                    text_tags = [
                        "text__text__1FZLe text__dark-grey__3Ml43 text__regular__2N1Xr"
                        " text__large__nEccO body__full_width__ekUdw body__large_body__"
                        "FV5_X article-body__element__2p5pI",
                        "text__text__1FZLe text__dark-grey__3Ml43 text__regular__2N1Xr"
                        " text__large__nEccO body__full_width__ekUdw body__large_body__"
                        "FV5_X article-body__element__2p5pI",
                        "Paragraph-paragraph-2Bgue ArticleBody-para-TD_9x",
                    ]
                    html_text = session.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    source = soup.find("script", attrs={"type": "application/ld+json"})
                    info_json = json.loads(source.text)
                    title = info_json["headline"]
                    date = info_json["dateCreated"][:10]
                    paragraphs = soup.find_all("p", class_=text_tags)
                    body = ""
                    for _ in paragraphs:
                        body += " " + _.text
                    body = replace_all(body, rep)
                    body = re.sub(r"^[^-]*-", "", " ".join(body.split()))
                    body = re.sub(r"http\S+", "", " ".join(body.split()))
                    bodies.append(body)
                    titles.append(title)
                    dates.append(date)
                    urls.append(url)
                    bar()
                except Exception as exc:
                    print(f"URL couldn't be parsed: {url} because {exc}")

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
                f"-> {len_after} new articles saved to {self.source}.csv! "
                f"Total articles: {len(data)}"
            )
        print("")
        data.to_csv(self.dir, index=True)

        return data
