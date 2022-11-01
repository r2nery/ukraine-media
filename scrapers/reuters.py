import os
import warnings
import requests
import regex as re
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
REUTERS_DIR = os.path.join(ROOT_DIR, "data", "Reuters.csv")

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

        with alive_bar(title="-> Reuters: Searching for latest date", bar=None, spinner="dots", force_tty=True) as bar:

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
                i = 920
                print(f"-> Reuters: No CSV file found. Creating...")
            elif not self.fromScratch():
                i = 1

            while not common_between_lists(urls_from_page(i)):
                i += 1
                bar()
            self.latestPage = i + 1

    def URLFetcher(self):
        self.urls = []
        with alive_bar(title="-> Reuters: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
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

        with alive_bar(len(self.unique_urls), title="-> Reuters: Scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
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
                    # print(f"URL couldn't be parsed: {url} because {e}")
                    pass
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})
        self.new_data = data

    def scraper(self):
        self.fromScratch()
        self.latestPage()
        self.URLFetcher()
        self.articleFetcher()
        data = self.concatData(self.new_data)
        lenAfter = len(data) - len(self.reuters_data)
        if lenAfter == 0:
            print(f"-> No new articles found. Total articles: {len(data)}")
        else:
            print(f"-> {lenAfter} new articles saved to Reuters.csv! Total articles: {len(data)}")
        data.to_csv(REUTERS_DIR, index=True)

        return data