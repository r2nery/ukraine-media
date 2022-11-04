import os
import warnings
import requests
import regex as re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
FOX_DIR = os.path.join(ROOT_DIR, "data", "Fox.csv")


class Fox:
    def __init__(self) -> None:
        self.source = "FOX"
        self.dir = FOX_DIR

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
            last_urls = ["https://www.foxnews.com/media/mark-levin-alexandra-chalupa-trump-impeachment-inquiry-witness"]

        with alive_bar(title=f"-> {self.source}: Fetching URLs", bar=None, spinner="dots", force_tty=True) as bar:
            sources = [
                "https://www.foxnews.com/api/article-search?searchBy=tags&values=fox-news%2Fworld%2Fworld-regions%2Frussia&excludeBy=tags&excludeValues&size=30&from=",
                "https://www.foxnews.com/api/article-search?searchBy=tags&values=fox-news%2Fworld%2Fconflicts%2Fukraine&excludeBy=tags&excludeValues&size=30&from=",
            ]
            session = requests.Session()
            for source in sources:
                for page in range(0, 165):
                    exc_list = ["/video/", "/lifestyle/", "/sports/"]
                    domain = "https://www.foxnews.com"
                    r = session.get(source + str(page * 30)).json()
                    for i in r:
                        url = domain + i["url"]
                        url = url.strip()
                        if not any(s in url for s in exc_list):
                            self.urls.append(url)
                            bar()
                        if url in last_urls:
                            break
                    if url in last_urls:
                        break
            self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        titles, bodies, dates, urls = [], [], [], []
        rep = {
            "CLICK HERE TO GET THE FOX NEWS APP": "",
            "is a Fox News Digital reporter. You can reach": "",
            "Fox News Flash top headlines are here. Check out what's clicking on Foxnews.com.": "",
        }

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    article_tag = ["article-body"]
                    title_tags = ["headline"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h1", class_=title_tags).text
                    date = soup.find("time").text
                    date = str(datetime.strptime(date[1:-6], "%B %d, %Y %H:%M"))[:-9]
                    article = soup.find("div", class_=article_tag)
                    paragraphs = article.find_all("p")
                    body = ""
                    for i in range(0, len(paragraphs) - 1):  # excluding last paragraph (journalist information)
                        body += " " + paragraphs[i].text
                    body = replaceAll(body, rep)
                    body = re.sub(r"\(([^\)]+)\)", "", body)  # inside parenthesis
                    body = re.sub(r"(\b[A-Z][A-Z]+|\b[A-Z][A-Z]\b)", "", body)  # all caps text
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
