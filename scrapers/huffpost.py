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
HUFFPOST_DIR = os.path.join(ROOT_DIR, "data", "HuffPost.csv")

class Huffpost:
    def __init__(self) -> None:
        self.source = "Huffpost"
        self.dir = HUFFPOST_DIR

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            print(f"-> {self.source}: No CSV file found. Creating...")
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
        self.urls, self.dates = [], []

        if self.from_scratch == False:
            last_urls = self.old_data.iloc[0:5, 1].tolist()
        elif self.from_scratch == True:
            last_urls = []

        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            sources = ["https://www.huffpost.com/news/topic/ukraine?page=", "https://www.huffpost.com/news/topic/russia?page="]
            for source in sources:
                for page in range(0, 10):  # 92
                    url = source + str(page)
                    title_tag = "card__headline card__headline--long"
                    inc_list = ["huffpost"]
                    try:
                        html_text = requests.get(url).text
                        soup = BeautifulSoup(html_text, "lxml")
                        headlines = soup.find_all("a", class_=title_tag)
                        for headline in headlines:
                            url = headline["href"]
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
        replacements_dict = {}

        def replaceAll(text, dict):
            for i, j in dict.items():
                text = text.replace(i, j)
                text = re.sub(r"[\\].....", "", text)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    title_box_tags = ["headline"]
                    text_box_tags = ["entry__content-list js-entry-content js-cet-subunit"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h1", class_=title_box_tags).text
                    date_box = soup.find("time")
                    date = date_box["datetime"][:10]
                    text_block = soup.find("section", class_=text_box_tags)
                    paragraphs = text_block.find_all("p")
                    body = ""
                    for p in paragraphs:
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