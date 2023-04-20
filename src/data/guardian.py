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
GUARDIAN_DIR = os.path.join(ROOT_DIR, "data", "raw", "Guardian.csv")


class Guardian:
    def __init__(self) -> None:
        self.source = "Guardian"
        self.dir = GUARDIAN_DIR
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

    def replace_all(self, text, dic):
        for i, j in dic.items():
            text = text.replace(i, j)
        return text

    def article_scraper(self):

        if not self.from_scratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            print(f"-> {self.source}: No CSV file found. Creating...")
            last_urls = [""]

        with alive_bar(
            title=f"-> {self.source}: Article scraper",
            bar=None,
            spinner="dots",
            force_tty=True,
        ) as bar:
            bodies, titles, dates, urls = [], [], [], []
            tags = ["russia", "ukraine"]
            rep = {
                "Sign up to First Edition, our free daily newsletter – every weekday morning at 7am": "",
                "Sign up to First Edition, our free daily newsletter – every weekday at 7am BST": "",
                "Sign up to receive Guardian Australia’s fortnightly Rural Network email newsletter": "",
                "Sign up for the Rural Network email newsletter Join the Rural Network group on Facebook to be part of the community": "",
                "Sign up to the daily Business Today email or follow Guardian Business on Twitter at @BusinessDesk": "",
                "Photograph:": "",
                "Related:": "",
            }
            session = requests.Session()
            for tag in tags:
                for page in range(1, 95):  # 95
                    exc_list = ["/film/", "/books/", "/music/"]
                    loop_break = None
                    source = (
                        "https://content.guardianapis.com/search?"
                        "api-key=fad78733-31a0-4ea7-8823-ba815b578899&type=article&page="
                        + str(page)
                        + "&tag=world/"
                        + tag
                        + "&order-by=newest&show-fields=body&page-size=200"
                    )
                    req = session.get(source).json()
                    results = [
                        i
                        for i in req["response"]["results"]
                        if not any(s in i["webUrl"] for s in exc_list)
                    ]
                    for _, result in enumerate(results):
                        if result["webUrl"] in last_urls:
                            loop_break = 1
                            break
                        urls.append(result["webUrl"])
                        body = BeautifulSoup(result["fields"]["body"], "html.parser").get_text()
                        body = self.replace_all(body, rep)
                        bodies.append(" ".join(body.split()))
                        titles.append(result["webTitle"])
                        dates.append(result["webPublicationDate"][:10])
                        bar()
                    if loop_break is not None:
                        break
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        self.new_data = data

    def scraper(self):
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
