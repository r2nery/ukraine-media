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
    def __init__(self, amount=100) -> None:
        self.source = "Mirror"
        self.dir = MIRROR_DIR
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

        if not self.fromScratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            last_urls = ["https://www.mirror.co.uk/news/world-news/inside-chernobyls-mega-tomb-protects-26120551"]
            print(f"-> {self.source}: No CSV file found. Creating...")

        agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            inc_list = ["/world-news/", "/politics/"]
            session = requests.Session()
            for i in range(1, 200*int(self.amount/100)): #200
                source = "https://www.mirror.co.uk/all-about/russia-ukraine-war?pageNumber=" + str(i)
                html_text = session.get(source, headers=agent).text
                soup = BeautifulSoup(html_text, "lxml")
                articles = soup.find_all("article", class_="story story--news")
                for article in articles:
                    url = article.find("a")
                    url = url["href"]
                    if any(s in url for s in inc_list):
                        self.urls.append(url)
                        self.unique_urls = list(dict.fromkeys(self.urls))
                        bar()
                    if url in last_urls:
                        break
                if url in last_urls:
                    break

    def articleScraper(self):
        bodies, titles, dates, urls, comments = [], [], [], [], []
        rep = {"": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        agent = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"}
        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = requests.Session()
            for url in self.unique_urls:
                try:
                    if len(urls) % 20 == 0:
                        session = requests.Session()  # restarting session every 20 urls
                    article_tag = ["article-body"]
                    html_text = session.get(url, headers=agent).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("meta", {"name":"parsely-title"})
                    title = title["content"]
                    date = soup.find("meta", {"name":"parsely-pub-date"})
                    date = date["content"][:10]
                    comment_count = soup.select_one("#share-top > ul > li.count-comments > a > span").text
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
                    comments.append(comment_count)
                    bar()
                except Exception as e:
                    print(f"URL couldn't be scraped: {url} because {e}")
                    pass

        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies, "Comments":comments})
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