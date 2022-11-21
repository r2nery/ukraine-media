import os
import warnings
import requests
import regex as re
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
EXPRESS_DIR = os.path.join(ROOT_DIR, "data", "Express.csv")


class Express:
    def __init__(self) -> None:
        self.source = "Express"
        self.dir = EXPRESS_DIR

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            print(f"-> {self.source}: No CSV file found. Creating...")
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
            last_urls = ["https://www.express.co.uk/news/world/1212144/putin-news-russia-missile-weapons-nato-spt"]

        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            sources = ["https://www.express.co.uk/latest/ukraine?pageNumber=", "https://www.express.co.uk/latest/russia?pageNumber="]
            for source in sources:
                session = requests.Session()
                for page in range(0, 630):  # 630
                    url = source + str(page)
                    leading_url = "https://www.express.co.uk"
                    title_tag = "post"
                    inc_list = ["/science/", "/world/", "/politics/", "/uk/"]
                    try:
                        html_text = session.get(url).text
                        soup = BeautifulSoup(html_text, "lxml")
                        headlines = soup.find_all("li", class_=title_tag)
                        for headline in headlines:
                            div = headline.find("div")
                            _ = div.find("a", href=True)
                            url = leading_url + _["href"]
                            if any(s in url for s in inc_list):
                                self.urls.append(url)
                                bar()
                            if url in last_urls:
                                break
                        if url in last_urls:
                            break
                    except Exception as e:
                        print(f"Error in page {page}: {e}")
                        pass
        self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        bodies, titles, dates, urls = [], [], [], []
        replacements_dict = {"FOLLOW BELOW FOR LIVE UPDATES…": ""}

        def replaceAll(text, dict):
            for i, j in dict.items():
                text = text.replace(i, j)
                text = re.sub(r"[\\].....", "", text)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = requests.Session()
            for url in self.unique_urls:
                try:
                    if len(urls) % 20 == 0:
                        session = requests.Session()
                    title_box_tags = ["clearfix"]
                    text_tags = ["text-description"]
                    exc_p = ["<strong>"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title_box = soup.find("header", class_=title_box_tags)
                    title = title_box.find("h1").text
                    date_box = soup.find("time")
                    date = date_box["datetime"][:10]
                    blocks = soup.find_all("div", class_=text_tags)
                    body = ""
                    for block in blocks:
                        paragraphs = block.find_all("p")
                        for p in paragraphs:
                            if not any(s in str(p) for s in exc_p):
                                body += " " + p.text
                    body = replaceAll(body, replacements_dict)
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