import pandas as pd
import os
import regex as re
import requests
from alive_progress import alive_bar
from bs4 import BeautifulSoup


ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
PARENT_DIR = os.path.dirname(ROOT_DIR)
GUARDIAN_DIR = os.path.join(ROOT_DIR, "/data/", "Guardian.csv")
REUTERS_DIR = os.path.join(ROOT_DIR, "/data/", "Reuters.csv")



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

    def numArticlesInPage(json):
        if json["response"]["total"] - json["response"]["startIndex"] >= 200:
            return 200
        else:
            return json["response"]["total"] - json["response"]["startIndex"] + 1

    def replaceAll(text, dic):
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

    def concatData(old, new):
        result = pd.concat([old, new])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    def guardian(self, page, tag):
        return requests.get("https://content.guardianapis.com/search?api-key=" + self.keyG + "&from-date=" + str(self.getDate()) + "&type=article" + "&page=" + str(page) + "&tag=world/" + tag + "&order-by=oldest" + "&show-fields=body" + "&page-size=200")

    def guardianScraper(self):

        os.makedirs(PARENT_DIR + "/data", exist_ok=True)

        # Query setup function

        # Dict of undesirable substrings
        rep = {
            "Sign up to First Edition, our free daily newsletter – every weekday morning at 7am": "",
            "Sign up to First Edition, our free daily newsletter – every weekday at 7am BST": "",
            "Sign up to receive Guardian Australia’s fortnightly Rural Network email newsletter": "",
            "Sign up for the Rural Network email newsletter Join the Rural Network group on Facebook to be part of the community": "",
            "Sign up to the daily Business Today email or follow Guardian Business on Twitter at @BusinessDesk": "",
            "Photograph:": "",
            "Related:": "",
        }

        ## Scraper

        if os.path.exists(GUARDIAN_DIR):
            print(f"-> CSV file found with {self.getLen(self.file)} articles! Latest article date: {self.getDate()}")
            print("-> Checking articles from latest date onward...")
        else:
            print(f"-> No CSV file found. Creating...")

        lenBefore = self.getLen(self.file)

        # Instancing
        urls = []
        titles = []
        bodies = []
        dates = []

        # Loops

        with alive_bar(title="→ Guardian API Request", unknown="dots_waves", spinner=None, force_tty=True) as bar:

            # Instancing a query to fetch basic information
            numPages = self.guardian(1, "ukraine").json()["response"]["pages"]

            # Going through all pages available for the query
            for i in range(1, numPages + 1):

                json_guardian = self.guardian(i, "ukraine").json()

                # Going through all articles in a page
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

            # Instancing a query to fetch basic information
            numPages = self.guardian(1, "russia").json()["response"]["pages"]

            # Going through all pages available for the query
            for i in range(1, numPages + 1):

                json_guardian = self.guardian(i, "russia").json()

                # Going through all articles in a page
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

        # Transforming fetched info to dataframe
        new_data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})

        # Saving to csv. Will concat if csv altready exists
        data = self.concatData(old_data, new_data)
        lenAfter = len(data) - lenBefore

        if lenAfter == 0:
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to {self.file}! Total articles: {len(data)}")

        return data

    #######

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.dirname(ROOT_DIR)
    FILE = "Reuters.csv"
    # This code is mostly meant to update the database, and won't build one from scratch

    def concatData(old, new):
        result = pd.concat([old, new])
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result

    class latestPage:
        def __init__(self, reuters_data):
            self.reuters_data = reuters_data
            self.existing_urls = self.reuters_data.loc[:, "URL"]

        def urls_from_page(self, page):
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

        def common_between_lists(self, a, b):
            a_set = set(a)
            b_set = set(b)
            if a_set & b_set:
                return True
            else:
                return False

        def fetch(self):
            i = 1
            while not self.common_between_lists(self.urls_from_page(i), self.existing_urls):
                i += 1
            # print(f"-> Last page scraped: {i+1}")
            return i + 1

    class URLFetcher:
        def __init__(self, num_pages):
            self.urls = []
            self.num_pages = num_pages

        def fetch(self):
            for page in range(1, (self.num_pages) + 1):
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
                    except Exception as e:
                        print(f"Error in page {page}: {e}")
                        pass
            unique_urls = list(dict.fromkeys(self.urls))
            # print(f"-> {len(unique_urls)} URLs fetched successfully!")
            return unique_urls

    class articleFetcher:
        def __init__(self, unique_urls):
            self.unique_urls = unique_urls
            self.bodies = []
            self.titles = []
            self.dates = []
            self.urls = []
            self.rep = {"Our Standards: The Thomson Reuters Trust Principles.": "", "read more": ""}

        def replaceAll(self, text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        def fetch(self):
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
                        body = self.replaceAll(body, self.rep)
                        self.bodies.append(re.sub(r"^[^-]*-", "", " ".join(body.split())))
                        self.titles.append(title)
                        self.dates.append(str(datetime.strptime(date, "%B %d, %Y").date()))
                        self.urls.append(url)
                        bar()
                    except Exception as e:
                        # print(f"URL couldn't be parsed: {url} because {e}")
                        pass

            data = pd.DataFrame({"URL": self.urls, "Date": self.dates, "Title": self.titles, "Text": self.bodies})
            # print("-> New data fetched successfully!")
            return data

    def reutersScraper():
        old_data = pd.read_csv(PARENT_DIR + "/data/Reuters.csv")
        pages = latestPage(old_data).fetch()
        urls = URLFetcher(pages).fetch()
        new_data = articleFetcher(urls).fetch()
        data = concatData(old_data, new_data)

        lenAfter = len(data) - len(old_data)

        if lenAfter == 0:
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to {FILE}! Total articles: {len(data)}")

        return data


if __name__ == "__main__":
    pass
