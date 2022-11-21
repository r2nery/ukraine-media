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
DAILYMAIL_DIR = os.path.join(ROOT_DIR, "data", "DailyMail.csv")

class DailyMail:
    def __init__(self, amount=100) -> None:
        self.source = "DailyMail"
        self.dir = DAILYMAIL_DIR
        self.amount = amount

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text", "Comments"])
            print(f"-> {self.source}: No CSV file found. Creating...")
            return True
        else:
            self.old_data = pd.read_csv(self.dir)
            return False

    def concatData(self):
        result = pd.concat([self.old_data, self.new_data])
        result = result.dropna()
        result = result.drop_duplicates(subset=["Text"])
        result = result.set_index("Date")
        result = result.sort_index(ascending=False)
        return result
        
        
    def convert_str_to_number(self,x):
        if "k" in list(x):
            k=x[:-1]
            if "." in list(x):
                before = re.sub(r"(?<=\.).*","",x)
                after = re.sub(r"(.*?)\.","",k)     
                total_stars = str(before[:-1]) + str(int(after)*100)
            else:
                total_stars = int(x[:-1]) * 1000
        else: 
            total_stars = x
        return int(total_stars)

    def URLFetcher(self):
        self.urls = []
        self.dates = []

        if not self.fromScratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            last_urls = "https://www.dailymail.co.uk/news/article-7699743/Senator-Ron-Johnson-writes-no-recollection-Trump-telling-delegation-work-Rudy.html"

        with alive_bar(title=f"-> {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            session = requests.Session()
            for page in range(0, int(165*self.amount/100)):  # 165
                leading_url = "https://www.dailymail.co.uk"
                source = "https://www.dailymail.co.uk/home/search.html?offset=" + str(page * 50) + "&size=50&sel=site&searchPhrase=ukraine+russia&sort=recent&channel=news&type=article&days=all"
                title_tag = "sch-res-title"
                try:
                    html_text = session.get(source).text
                    soup = BeautifulSoup(html_text, "lxml")
                    headlines = soup.find_all("h3", class_=title_tag)
                    for headline in headlines:
                        _ = headline.find("a", href=True)
                        url = leading_url + _["href"]
                        self.urls.append(url)
                        bar()
                        if url in last_urls:
                            break
                    if url in last_urls:
                        break
                except Exception as e:
                    print(f"Error in page {page}: {e}")
                    pass
        self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        bodies, titles, dates, urls, comments = [], [], [], [], []
        rep = {"The Mail on Sunday can reveal:": "", "RELATED ARTICLES": "", "Share this article": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = requests.Session()
            for url in self.unique_urls:
                try:
                    if len(urls) % 20 == 0:
                        session = requests.Session()
                    text_tags = ["mol-para-with-font"]
                    date_box_tag = ["article-timestamp article-timestamp-published"]
                    comment_count_tag = "#articleIconLinksContainer > a > p.count-number"
                    html_text = session.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h2").text
                    date_box = soup.find("span", class_=date_box_tag)
                    date = date_box.find("time")
                    comment_count = soup.select_one(comment_count_tag).text.strip()
                    if comment_count is not None:
                        comment_count = self.convert_str_to_number(comment_count)
                    else:
                        comment_count = ""
                    paragraphs = soup.find_all("p", class_=text_tags)
                    body = ""
                    for _ in paragraphs:
                        body += " " + _.text
                    body = replaceAll(body, rep)
                    bodies.append(" ".join(body.split()))
                    titles.append(title)
                    urls.append(url)
                    dates.append(date.get("datetime")[:10])
                    comments.append(comment_count)
                    bar()
                except Exception as e:
                    print(f"URL couldn't be scraped: {url} because {e}")
                    pass
        data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies, "Comments":comments})
        self.new_data = data

    def scraper(self):
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