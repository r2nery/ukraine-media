import os
import warnings
import requests
import pandas as pd
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
CNN_DIR = os.path.join(ROOT_DIR, "data", "raw", "CNN.csv")


class CNN:
    def __init__(self) -> None:
        self.source = "CNN"
        self.dir = CNN_DIR
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

    def article_scraper(self):

        if not self.from_scratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            print(f"-> {self.source}: No CSV file found. Creating...")
            last_urls = [
                "https://www.cnn.com/2019/01/05/politics/nasa-cancels-russian-space"
                "-official-visit/index.html"
            ]

        with alive_bar(
            title=f"-> {self.source}: Article scraper",
            bar=None,
            spinner="dots",
            force_tty=True,
        ) as bar:
            bodies, titles, dates, urls = [], [], [], []
            session = requests.Session()
            loop_break = None
            for page in range(0, 95):  # 95
                exc_list = [
                    "/tennis/",
                    "/live-news/",
                    "/opinions/",
                    "/tech/",
                    "/sport/",
                    "/us/",
                    "/football/",
                    "/china/",
                    "/style/",
                    "/business-food/",
                    "/americas/",
                    "/travel/",
                    "/business/",
                ]
                source = (
                    "https://search.api.cnn.com/content?q=ukraine%20russia&size=50&from="
                    + str(page * 50)
                    + "&page=1&sort=newest&types=article"
                )
                request = session.get(source).json()
                results = [i for i in request["result"] if not any(s in i["url"] for s in exc_list)]
                for _, result in enumerate(results):
                    if result["url"] in last_urls:
                        loop_break = 1
                        break
                    urls.append(result["url"])
                    bodies.append(" ".join(result["body"].split()))
                    titles.append(result["headline"])
                    dates.append(result["firstPublishDate"][:10])
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
