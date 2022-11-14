import os
import time
import warnings
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from requests_html import HTMLSession

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
NYT_DIR = os.path.join(ROOT_DIR, "data", "NYT.csv")


class NYT:
    def __init__(self,amount=100) -> None:
        self.source = "NYT"
        self.dir = NYT_DIR
        self.amount = amount

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text", "Comments"])
            return True
        else:
            self.old_data = pd.read_csv(self.dir)
            return False

    def concatData(self):
        result = pd.concat([self.old_data, self.new_data])
        result = result.dropna()
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
            last_urls = []

        with alive_bar(title=f"-> {self.source}: Fetching URLs", bar=None, spinner="dots", force_tty=True) as bar:
            if self.fromScratch():
                begin_dates, sort = ["20191201", "20220425"], "oldest"
            else:
                begin_dates, sort = ["20220425"], "newest"
            for date in begin_dates:
                source = "https://api.nytimes.com/svc/search/v2/articlesearch.json?facet=false&fq=source%3A(%22The%20New%20York%20Times%22)%20AND%20section_name%3A(%22Opinion%22%20%22Politics%22%20%22Foreign%22%20%22U.S%22%20%22World%22)%20AND%20glocations%3A(%22Russia%22%20%22Ukraine%22)%20AND%20document_type%3A(%22article%22)&api-key=DeNQy6aiS8FdkQdIgPmNUcQzohAQ0q6G&sort=" + sort + "&begin_date=" + date + "&fl=web_url&page="
                session = requests.Session()
                for page in range(0, 200*int(self.amount/100)):  # 75
                    time.sleep(6)
                    r = session.get(source + str(page)).json()
                    for i in r["response"]["docs"]:
                        url = i["web_url"]
                        self.urls.append(url)
                        bar()
                        if url in last_urls:
                            break
                    if url in last_urls:
                        break
            self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        titles, bodies, dates, urls, comments = [], [], [], [], []
        rep = {"": ""}
        # Add your headers here (w/ cookies, beware)

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = HTMLSession()
            for url in self.unique_urls:
                try:
                    html_text = session.get(url, headers=headers)
                    html_text.html.render()
                    html_text = html_text.text
                    soup = BeautifulSoup(html_text, "lxml")
                    info_json = json.loads(soup.find("script", attrs={"type": "application/ld+json"}).text)
                    title = info_json["headline"]
                    title = " ".join(title.split())
                    date = info_json["datePublished"][:10]
                    comment_count = soup.select_one("#comments-speech-bubble-header > div > span").text
                    paragraphs = soup.select("section > div > div > p")
                    body = ""
                    for i in range(0, len(paragraphs)):
                        body += " " + paragraphs[i].text
                    body = replaceAll(body, rep)
                    body = " ".join(body.split())
                    bodies.append(body)
                    titles.append(title)
                    urls.append(url)
                    dates.append(date)
                    comments.append(comment_count)
                    bar()
                except Exception as e:
                    print(f"URL couldn't be scraped: {url} because {e}")
                    pass
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies, "Comments": comments})
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
