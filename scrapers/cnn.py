import os
import warnings
import requests
import pandas as pd
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
CNN_DIR = os.path.join(ROOT_DIR, "data", "CNN.csv")

class CNN:
    def __init__(self) -> None:
        self.source = "CNN"
        self.dir = CNN_DIR

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

    def articleScraper(self):
        
        if self.from_scratch == False:
            last_url = self.old_data.iloc[0, 1]
            print(f"last url {last_url}")
        elif self.from_scratch == True:
            print(f"-> {self.source}: No CSV file found. Creating...")
            last_url = ["https://www.cnn.com/2019/01/05/politics/nasa-cancels-russian-space-official-visit/index.html"]

        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            bodies, titles, dates, urls = [], [], [], []
            session = requests.Session()
            for page in range(0, 95):  # 95
                exc_list = ["/tennis/", "/live-news/", "/opinions/", "/tech/", "/sport/", "/us/", "/football/", "/china/", "/style/", "/business-food/", "/americas/", "/travel/", "/business/"]
                source = "https://search.api.cnn.com/content?q=ukraine%20russia&size=50&from=" + str(page * 50) + "&page=1&sort=newest&types=article"
                r = session.get(source).json()
                results = [i for i in r["result"] if not any(s in i["url"] for s in exc_list)]
                for i in range(0, len(results)):
                    if results[i]["url"] in last_url:
                        break
                    urls.append(results[i]["url"])
                    bodies.append(" ".join(results[i]["body"].split()))
                    titles.append(results[i]["headline"])
                    dates.append(results[i]["firstPublishDate"][:10])
                    bar()
                if results[i]["url"] in last_url:
                    break
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        self.new_data = data

    def scraper(self):
        self.fromScratch()
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