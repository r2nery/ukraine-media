from alive_progress import alive_bar
import pandas as pd
from bs4 import BeautifulSoup
import requests
import regex as re
from datetime import datetime
import os

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
        #print(f"-> Last page scraped: {i+1}")
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
        #print(f"-> {len(unique_urls)} URLs fetched successfully!")
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
        #print("-> New data fetched successfully!")
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
