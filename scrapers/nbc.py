import os
import warnings
import requests
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
NBC_DIR = os.path.join(ROOT_DIR, "data", "NBC.csv")

class NBC:
    def __init__(self) -> None:
        self.source = "NBC"
        self.dir = NBC_DIR

    def seleniumParams(self):
        s = Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE, path=ROOT_DIR).install())
        o = webdriver.ChromeOptions()
        o.add_argument("headless")
        self.driver = webdriver.Chrome(service=s, options=o)
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)
        self.wait = WebDriverWait(self.driver, 30, ignored_exceptions=ignored_exceptions)

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

    def URLFetcher(self):
        self.urls = []
        self.dates = []
        self.seleniumParams()

        if self.from_scratch == False:
            last_url = self.old_data.iloc[0, 1]
        elif self.from_scratch == True:
            last_url = [""]
            print(f"-> {self.source}: No CSV file found. Creating...")

        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            source = "https://www.nbcnews.com/world/russia-ukraine-news"
            title_tag = "//div[@class='wide-tease-item__info-wrapper flex-grow-1-m']/a"
            button_tag = "//button[@class='animated-ghost-button animated-ghost-button--normal styles_button__khb8K']"
            inc_list = ["nbcnews"]
            self.driver.get(source)
            for i in range(0, 7):
                # time.sleep(1)
                titles = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, title_tag)))
                for title in titles[-20:]:
                    url = title.get_attribute("href")
                    if any(s in url for s in inc_list):
                        self.urls.append(url)
                        self.unique_urls = list(dict.fromkeys(self.urls))
                    if url == last_url:
                        break
                if url == last_url:
                    break
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                self.wait.until(EC.element_to_be_clickable((By.XPATH, button_tag))).click()
                bar()
            titles = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, title_tag)))
            for title in titles[-20:]:
                url = title.get_attribute("href")
                if any(s in url for s in inc_list):
                    self.urls.append(url)
                    self.unique_urls = list(dict.fromkeys(self.urls))
                    print(f"{len(self.unique_urls)}/{len(self.urls)}")
        self.driver.quit()

    def articleScraper(self):
        bodies = []
        titles = []
        dates = []
        urls = []
        rep = {}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    article_tag = ["article-body__content"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("title").text
                    date = soup.find("time")
                    date = date["datetime"]
                    date = date[:10]
                    article = soup.find("div", class_=article_tag)
                    paragraphs = article.find_all("p")
                    body = ""
                    for i in range(0, len(paragraphs)):
                        body += " " + paragraphs[i].text
                    body = replaceAll(body, rep)
                    bodies.append(" ".join(body.split()))
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
        self.fromScratch()
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