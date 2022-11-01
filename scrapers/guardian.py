
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
GUARDIAN_DIR = os.path.join(ROOT_DIR, "data", "Guardian.csv")

class Guardian:
    def __init__(self) -> None:
        self.keyG = "fad78733-31a0-4ea7-8823-ba815b578899"

    def getLen(self):
        if os.path.exists(GUARDIAN_DIR):
            check = pd.read_csv(GUARDIAN_DIR)
            return len(check)
        else:
            return 0

    def getDate(self):
        if os.path.exists(GUARDIAN_DIR):
            check = pd.read_csv(GUARDIAN_DIR)
            return check.iloc[0, 0]
        else:
            return "2021-07-20"

    def numArticlesInPage(self, json):
        if json["response"]["total"] - json["response"]["startIndex"] >= 200:
            return 200
        else:
            return json["response"]["total"] - json["response"]["startIndex"] + 1

    def replaceAll(self, text, dic):
        for i, j in dic.items():
            text = text.replace(i, j)
        return text

    def concatData(self, old, new):
        result = pd.concat([old, new])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def guardian(self, page, tag):
        return requests.get("https://content.guardianapis.com/search?api-key=" + self.keyG + "&from-date=" + str(self.getDate()) + "&type=article" + "&page=" + str(page) + "&tag=world/" + tag + "&order-by=oldest" + "&show-fields=body" + "&page-size=200")

    def scraper(self):

        os.makedirs(os.path.join(ROOT_DIR, "data"), exist_ok=True)

        rep = {
            "Sign up to First Edition, our free daily newsletter – every weekday morning at 7am": "",
            "Sign up to First Edition, our free daily newsletter – every weekday at 7am BST": "",
            "Sign up to receive Guardian Australia’s fortnightly Rural Network email newsletter": "",
            "Sign up for the Rural Network email newsletter Join the Rural Network group on Facebook to be part of the community": "",
            "Sign up to the daily Business Today email or follow Guardian Business on Twitter at @BusinessDesk": "",
            "Photograph:": "",
            "Related:": "",
        }

        if os.path.exists(GUARDIAN_DIR):
            print("-> Guardian: Checking articles from latest date onward...")
        else:
            print(f"-> Guardian: No CSV file found. Creating...")

        lenBefore = self.getLen()
        urls = []
        titles = []
        bodies = []
        dates = []

        with alive_bar(title="-> Guardian: API Request", bar=None, spinner="dots", force_tty=True) as bar:
            numPages = self.guardian(1, "ukraine").json()["response"]["pages"]
            for i in range(1, numPages + 1):
                json_guardian = self.guardian(i, "ukraine").json()
                for j in range(0, self.numArticlesInPage(json_guardian)):
                    if os.path.exists(GUARDIAN_DIR):
                        old_data = pd.read_csv(GUARDIAN_DIR)
                        if json_guardian["response"]["results"][j]["webUrl"] == old_data.iloc[-1, 0]:
                            continue
                    urls.append(json_guardian["response"]["results"][j]["webUrl"])
                    fulldate = json_guardian["response"]["results"][j]["webPublicationDate"]
                    dates.append(fulldate[: len(fulldate) - 10])
                    title = json_guardian["response"]["results"][j]["webTitle"]
                    titles.append(re.sub(r"\|.*$", "", title))  # removing authors from titles
                    body = BeautifulSoup(json_guardian["response"]["results"][j]["fields"]["body"], "html.parser").get_text()
                    body = self.replaceAll(body, rep)  # replacing substrings
                    bodies.append(re.sub(r"[\t\r\n]", "", body))  # removing line breaks
                    bar()
            numPages = self.guardian(1, "russia").json()["response"]["pages"]
            for i in range(1, numPages + 1):
                json_guardian = self.guardian(i, "russia").json()
                for j in range(0, self.numArticlesInPage(json_guardian)):
                    if os.path.exists(GUARDIAN_DIR):
                        old_data = pd.read_csv(GUARDIAN_DIR)
                        if json_guardian["response"]["results"][j]["webUrl"] == old_data.iloc[-1, 0]:
                            continue
                    urls.append(json_guardian["response"]["results"][j]["webUrl"])
                    fulldate = json_guardian["response"]["results"][j]["webPublicationDate"]
                    dates.append(fulldate[: len(fulldate) - 10])
                    title = json_guardian["response"]["results"][j]["webTitle"]
                    titles.append(re.sub(r"\|.*$", "", title))  # removing authors from titles
                    body = BeautifulSoup(json_guardian["response"]["results"][j]["fields"]["body"], "html.parser").get_text()
                    body = self.replaceAll(body, rep)  # replacing substrings
                    bodies.append(re.sub(r"[\t\r\n]", "", body))  # removing line breaks
                    bar()
        new_data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        data = self.concatData(old_data, new_data)
        lenAfter = len(data) - lenBefore
        if lenAfter == 0:
            print(f"-> No new articles found. Total articles: {len(data)}")
        else:
            print(f"-> {lenAfter} new articles saved to Guardian.csv! Total articles: {len(data)}")
        print("")
        data.to_csv(GUARDIAN_DIR)
        return data
