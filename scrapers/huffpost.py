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
        self.urls = []
        self.old_data = None
        self.new_data = None

    def from_scratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            print(f"-> {self.source}: No CSV file found. Creating...")
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

    def url_fetcher(self):
        self.urls = []

        if not self.from_scratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            last_urls = ["https://www.huffpost.com/entry/fiona-hill-impeachment-inquiry_n_5dd6b96fe4b0e29d72808ce5", "https://www.huffpost.com/entry/joe-biden-damn-liar-voter_n_5de97689e4b0d50f32b0d9d7"]

        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            sources = ["https://www.huffpost.com/news/topic/ukraine?page=", "https://www.huffpost.com/news/topic/russia?page="]
            for source in sources:
                session = requests.Session()
                for page in range(0, 130):  # 105
                    url = source + str(page)
                    section_tag = "zone zone--twilight js-cet-subunit"
                    card_tag = "card__text"
                    author_tag = "card__byline"
                    title_tag = "card__headline card__headline--long"
                    inc_list = ["huffpost"]
                    exc_list = ["AP","Video","Associated Press"]
                    html_text = session.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    sections = soup.find_all("section", class_=section_tag)
                    for section in sections:
                        cards = section.find_all("div", class_=card_tag)
                        headlines = []
                        for card in cards:
                            author = card.find("div",class_=author_tag).text
                            if not any(s in author for s in exc_list):
                                title = card.find("a",class_=title_tag)
                                headlines.append(title)
                        for headline in headlines:
                            url = headline["href"]
                            if any(s in url for s in inc_list):
                                self.urls.append(url)
                                bar()
                            if url in last_urls:
                                break
                        if url in last_urls:
                            break
                    if url in last_urls:
                        break

        self.urls = list(dict.fromkeys(self.urls))

    def article_scraper(self):
        bodies, titles, dates, urls = [], [], [], []
        replacements_dict = {}

        def replace_all(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
                text = re.sub(r"[\\].....", "", text)
            return text

        with alive_bar(len(self.urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = requests.Session()
            for url in self.urls:
                if len(urls) % 20 == 0:
                    session = requests.Session()
                title_box_tags = ["headline"]
                text_box_tags = ["entry__content-list js-entry-content js-cet-subunit"]
                html_text = session.get(url).text
                soup = BeautifulSoup(html_text, "lxml")
                title = soup.find("h1", class_=title_box_tags).text
                date_box = soup.find("time")
                date = date_box["datetime"][:10]
                text_block = soup.find("section", class_=text_box_tags)
                paragraphs = text_block.find_all("p")
                body = ""
                for phrase in paragraphs:
                    body += " " + phrase.text
                body = replace_all(body, replacements_dict)
                body = " ".join(body.split())
                body = re.sub(r"http\S+", "", " ".join(body.split()))
                body = re.sub(r"pic\.twitter\.com/\S+", "", " ".join(body.split()))
                bodies.append(body)
                titles.append(title)
                urls.append(url)
                dates.append(date)
                bar()

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
            print(f"-> {len_after} new articles saved to {self.source}.csv! Total articles: {len(data)}")
        print("")
        data.to_csv(self.dir, index=True)

        return data
