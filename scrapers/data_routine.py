import pandas as pd
import os
import regex as re
import requests
from datetime import datetime
from alive_progress import alive_bar
from bs4 import BeautifulSoup


ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
PARENT_DIR = os.path.dirname(ROOT_DIR)
GUARDIAN_DIR = os.path.join(ROOT_DIR, "data", "Guardian.csv")
REUTERS_DIR = os.path.join(ROOT_DIR, "data", "Reuters.csv")


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

    def save(self, dataF):
        if os.path.exists(GUARDIAN_DIR):
            existingData = pd.read_csv(GUARDIAN_DIR)
            data = pd.concat([existingData, dataF])
            data = data.drop_duplicates(keep="first")
            data.to_csv(GUARDIAN_DIR, index=False)
            return data
        else:
            dataF.to_csv(GUARDIAN_DIR, index=False)
            return dataF

    def concatData(self, old, new):
        result = pd.concat([old, new])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def guardian(self, page, tag):
        return requests.get("https://content.guardianapis.com/search?api-key=" + self.keyG + "&from-date=" + str(self.getDate()) + "&type=article" + "&page=" + str(page) + "&tag=world/" + tag + "&order-by=oldest" + "&show-fields=body" + "&page-size=200")

    def scraper(self):

        os.makedirs(os.path.join(PARENT_DIR, "data"), exist_ok=True)

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
            print(f"-> CSV file found with {self.getLen()} articles! Latest article date: {self.getDate()}")
            print("-> Checking articles from latest date onward...")
        else:
            print(f"-> No CSV file found. Creating...")

        lenBefore = self.getLen()
        urls = []
        titles = []
        bodies = []
        dates = []

        with alive_bar(title="→ Guardian API Request", bar=None, spinner="dots", force_tty=True) as bar:
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
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to Guardian.csv! Total articles: {len(data)}")

        data.to_csv(GUARDIAN_DIR, index=True)
        return data


class Reuters:
    def fromScratch(self):
        if not os.path.exists(REUTERS_DIR):
            self.reuters_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            self.reuters_data.loc[0, "URL"] = "https://www.reuters.com/article/us-shipping-seafarers-insight/sos-stranded-and-shattered-seafarers-threaten-global-supply-lines-idUSKBN2EQ0BQ"
            return True
        else:
            self.reuters_data = pd.read_csv(REUTERS_DIR)
            return False

    def concatData(self, new):
        result = pd.concat([self.reuters_data, new])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def latestPage(self):
        self.existing_urls = self.reuters_data.loc[:, "URL"]

        with alive_bar(title="→ Searching for latest date", bar=None, spinner="dots", force_tty=True) as bar:

            def urls_from_page(page):
                urls = []
                rus = "https://www.reuters.com/news/archive/ukraine?view=page&page=" + str(page) + "&pageSize=10"
                html_text = requests.get(rus).text
                soup = BeautifulSoup(html_text, "lxml")
                headline_list = soup.find("div", class_="column1 col col-10")
                headlines = headline_list.find_all("div", class_="story-content")
                for headline in headlines:
                    page_urls = headline.find_all("a", href=True)
                    urls.append("https://www.reuters.com" + page_urls[0]["href"])
                return urls

            def common_between_lists(a):
                a_set = set(a)
                b_set = set(self.existing_urls)
                if a_set & b_set:
                    return True
                else:
                    return False

            if self.fromScratch():
                print("Reuters.csv not found. Generating...")
                i = 920
            elif not self.fromScratch():
                print("Reuters.csv found!")
                i = 1

            while not common_between_lists(urls_from_page(i)):
                i += 1
                bar()
            print(f"-> Last page scraped: {i+1}")
            self.latestPage = i + 1

    def URLFetcher(self):
        self.urls = []
        with alive_bar(title="→ Fetching URLs in pages (estimate)", bar=None, spinner="dots", force_tty=True) as bar:
            for page in range(1, (self.latestPage) + 1):
                ukr = "https://www.reuters.com/news/archive/ukraine?view=page&page=" + str(page) + "&pageSize=10"
                rus = "https://www.reuters.com/news/archive/russia?view=page&page=" + str(page) + "&pageSize=10"
                tags = [ukr, rus]
                for tag in tags:
                    try:
                        html_text = requests.get(tag).text
                        soup = BeautifulSoup(html_text, "lxml")
                        headline_list = soup.find("div", class_="column1 col col-10")
                        headlines = headline_list.find_all("div", class_="story-content")
                        for headline in headlines:
                            page_urls = headline.find_all("a", href=True)
                            for _ in page_urls:
                                self.urls.append("https://www.reuters.com" + _["href"])
                        bar()
                    except Exception as e:
                        print(f"Error in page {page}: {e}")
                        pass

        unique_urls = list(dict.fromkeys(self.urls))
        # print(f"-> {len(unique_urls)} URLs fetched successfully!")
        self.unique_urls = unique_urls

    def articleFetcher(self):
        bodies = []
        titles = []
        dates = []
        urls = []
        rep = {"Our Standards: The Thomson Reuters Trust Principles.": "", "read more": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title="→ Reuters Scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    title_tags = ["text__text__1FZLe text__dark-grey__3Ml43 text__medium__1kbOh text__heading_2__1K_hh heading__base__2T28j heading__heading_2__3Fcw5"]
                    date_tags = ["date-line__date__23Ge-"]
                    text_tags = ["text__text__1FZLe text__dark-grey__3Ml43 text__regular__2N1Xr text__large__nEccO body__base__22dCE body__large_body__FV5_X article-body__element__2p5pI"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h1", class_=title_tags).text
                    date = soup.find("span", class_=date_tags).text
                    paragraphs = soup.find_all("p", class_=text_tags)
                    body = ""
                    for _ in paragraphs:
                        body += " " + _.text
                    body = replaceAll(body, rep)
                    bodies.append(re.sub(r"^[^-]*-", "", " ".join(body.split())))
                    titles.append(title)
                    dates.append(str(datetime.strptime(date, "%B %d, %Y").date()))
                    urls.append(url)
                    bar()
                except Exception as e:
                    print(f"URL couldn't be parsed: {url} because {e}")
                    pass
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        # print("-> New data fetched successfully!")
        self.new_data = data

    def scraper(self):
        self.fromScratch()
        print("getting latest page")
        self.latestPage()
        print("fetching urls")
        self.URLFetcher()
        print("parsing articles")
        self.articleFetcher()
        data = self.concatData(self.new_data)

        lenAfter = len(data) - len(self.reuters_data)

        if lenAfter == 0:
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to Reuters.csv! Total articles: {len(data)}")

        data.to_csv(REUTERS_DIR, index=True)
        return data


if __name__ == "__main__":
    Guardian().scraper()
    Reuters().scraper()
