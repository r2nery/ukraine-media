import os
import time
import warnings
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from requests_html import HTMLSession

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
NYT_DIR = os.path.join(ROOT_DIR, "data", "NYT.csv")


class NYT:
    def __init__(self,amount=100) -> None:
        self.source = "NYT"
        self.dir = NYT_DIR
        self.amount = amount

    def fromScratch(self):
        if not os.path.exists(self.dir):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text", "Comments"])
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

    def URLFetcher(self):
        self.urls = []
        self.last_url_found = False

        if not self.fromScratch():
            last_urls = [i.strip() for i in self.old_data.iloc[0:20, 1]]
        else:
            print(f"-> {self.source}: No CSV file found. Creating...")
            last_urls = []

        with alive_bar(title=f"-> {self.source}: Fetching URLs", bar=None, spinner="dots", force_tty=True) as bar:
            if self.fromScratch():
                begin_dates, sort = ["20191201", "20220425"], "oldest"
            else:
                begin_dates, sort = ["20220425"], "newest"
            for date in begin_dates:
                source = "https://api.nytimes.com/svc/search/v2/articlesearch.json?facet=false&fq=source%3A(%22The%20New%20York%20Times%22)%20AND%20section_name%3A(%22Opinion%22%20%22Politics%22%20%22Foreign%22%20%22U.S%22%20%22World%22)%20AND%20glocations%3A(%22Russia%22%20%22Ukraine%22)%20AND%20document_type%3A(%22article%22)&api-key=DeNQy6aiS8FdkQdIgPmNUcQzohAQ0q6G&sort=" + sort + "&begin_date=" + date + "&fl=web_url&page="
                session = requests.Session()
                for page in range(0, 200*int(self.amount/100)):  # 75
                    time.sleep(6)
                    r = session.get(source + str(page)).json()
                    for i in r["response"]["docs"]:
                        url = i["web_url"]
                        self.urls.append(url)
                        bar()
                        if url in last_urls:
                            break
                    if url in last_urls:
                        break
            self.unique_urls = list(dict.fromkeys(self.urls))

    def articleScraper(self):
        titles, bodies, dates, urls, comments = [], [], [], [], []
        rep = {"": ""}
        # Add your headers here (w/ cookies, beware)
        headers = {
            'authority': 'samizdat-graphql.nytimes.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'cookie': 'nyt-a=mVNEU8LHIMyL3CqI1J5M91; purr-pref-agent=<Go; nyt-purr=cfhheaihhcdlh; purr-cache=<K0<r<C_<Go<S0; nyt-auth-method=sso; nyt-gdpr=0; nyt-geo=BR; SIDNY=CBMSKQiLxbCbBhDiouybBhoSMS0z_9SRUZoBeHymEVzZ0LzLIJfmt0EqAh4BGkCshQzr0WOMpJQagMaVIq86xrNbi96F4WLXoVNxpO1gt23rE110SFoLro9tp41zYvAlOo4A3cVzEzh3Mei4AeoB; b2b_cig_opt=%7B%22isCorpUser%22%3Afalse%7D; edu_cig_opt=%7B%22isEduUser%22%3Afalse%7D; NYT-S=20AN2wCOFeE2IC.lVhGqPGNnB4SxCwKBPQmSRYorA/wpOKJGry8gEja6KdYLBr968WjOoea6bgYnSicFMFA/RSUvnoaI4D/blzkYajtKjZEFisUTTiSpE1vRS2eEiXhkDNnRRI.pDJ.mM81pk.8yAe4uQG8ouYAo.Hj8.hjhXLwUs0^^^^CBMSKQiLxbCbBhDiouybBhoSMS0z_9SRUZoBeHymEVzZ0LzLIJfmt0EqAh4BGkCshQzr0WOMpJQagMaVIq86xrNbi96F4WLXoVNxpO1gt23rE110SFoLro9tp41zYvAlOo4A3cVzEzh3Mei4AeoB; nyt-us=0; nyt-b3-traceid=ce4a861c7c584b88ae91c15bf11bcf11; nyt-jkidd=uid=137229079&lastRequest=1669009672038&activeDays=%5B0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C1%2C1%2C0%2C1%2C1%2C0%2C0%2C1%2C1%2C0%2C0%2C0%2C0%2C0%2C1%2C1%5D&adv=8&a7dv=2&a14dv=6&a21dv=8&lastKnownType=sub&newsStartDate=1667729762&entitlements=AAA+MM+MOW+MSD+MTD; nyt-m=2565FFFB2F75BB42F1D8C360EF2B7F37&ier=i.0&uuid=s.14d4e3f9-aeec-4ef8-9968-956889403b9b&igu=i.1&imu=i.1&s=s.core&e=i.1669903200&rc=i.0&iir=i.0&igd=i.0&iga=i.0&v=i.0&ird=i.0&t=i.2&vr=l.4.0.0.0.0&vp=i.0&fv=i.0&ica=i.0&ifv=i.0&igf=i.0&n=i.2&er=i.1669009672&prt=i.0&iub=i.0&iru=i.1&pr=l.4.0.0.0.0&cav=i.1&iue=i.1&g=i.0&ira=i.0&ft=i.0&imv=i.0; datadome=3w46keycVBP8v--1~PxhEVlF85rgak8JCqlgejFjBEDohTtk7Q0lqGKltAVhMT8eBIksjNsD8ykcFifGFLZpV4WZXgpKsKWYsS9eztNA5AeO_5CZQcQBEs2GIJiwtvxp',
            'nyt-app-type': 'project-vi',
            'nyt-app-version': '0.0.5',
            'nyt-token': 'MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAs+/oUCTBmD/cLdmcecrnBMHiU/pxQCn2DDyaPKUOXxi4p0uUSZQzsuq1pJ1m5z1i0YGPd1U1OeGHAChWtqoxC7bFMCXcwnE1oyui9G1uobgpm1GdhtwkR7ta7akVTcsF8zxiXx7DNXIPd2nIJFH83rmkZueKrC4JVaNzjvD+Z03piLn5bHWU6+w+rA+kyJtGgZNTXKyPh6EC6o5N+rknNMG5+CdTq35p8f99WjFawSvYgP9V64kgckbTbtdJ6YhVP58TnuYgr12urtwnIqWP9KSJ1e5vmgf3tunMqWNm6+AnsqNj8mCLdCuc5cEB74CwUeQcP2HQQmbCddBy2y0mEwIDAQAB',
            'origin': 'https://www.nytimes.com',
            'referer': 'https://www.nytimes.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
        }

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"-> {self.source}: Article scraper", length=20, spinner="dots", bar="smooth", force_tty=True) as bar:
            session = HTMLSession()
            for url in self.unique_urls:
                try:
                    html_text = session.get(url, headers=headers)
                    html_text.html.render()
                    html_text = html_text.text
                    soup = BeautifulSoup(html_text, "lxml")
                    info_json = json.loads(soup.find("script", attrs={"type": "application/ld+json"}).text)
                    title = info_json["headline"]
                    title = " ".join(title.split())
                    date = info_json["datePublished"][:10]
                    paragraphs = soup.select("section > div > div > p")
                    body = ""
                    for i in range(0, len(paragraphs)):
                        body += " " + paragraphs[i].text
                    body = replaceAll(body, rep)
                    body = " ".join(body.split())
                    bodies.append(body)
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
