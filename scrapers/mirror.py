import os
import warnings
import requests
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
MIRROR_DIR = os.path.join(ROOT_DIR, "data", "Mirror.csv")

class Mirror:
    def __init__(self) -> None:
        self.source = "Mirror"
        self.dir = MIRROR_DIR

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
        self.dates = []

        if self.from_scratch == False:
            last_url = self.old_data.iloc[0, 1]
        elif self.from_scratch == True:
            last_url = "https://www.mirror.co.uk/news/world-news/inside-chernobyls-mega-tomb-protects-26120551"
            print(f"-> {self.source}: No CSV file found. Creating...")

        agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            inc_list = ["/world-news/", "/politics/"]
            for i in range(1, 200):
                source = "https://www.mirror.co.uk/all-about/russia-ukraine-war?pageNumber=" + str(i)
                html_text = requests.get(source, headers=agent).text
                soup = BeautifulSoup(html_text, "lxml")
                articles = soup.find_all("article", class_="story story--news")
                for article in articles:
                    url = article.find("a")
                    url = url["href"]
                    if any(s in url for s in inc_list):
                        self.urls.append(url)
                        self.unique_urls = list(dict.fromkeys(self.urls))
                        bar()
                    if url == last_url:
                        break
                if url == last_url:
                    break

    def articleScraper(self):
        bodies = []
        titles = []
        dates = []
        urls = []
        rep = {"": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    article_tag = ["article-body"]
                    html_text = requests.get(url, headers=agent).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("title").text
                    date = soup.find("time", class_="date-published")
                    date = date["datetime"][:10]
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