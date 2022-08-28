import os
import warnings
import requests
import string
import numpy as np
import nltk
import time
from numpy import linalg as LA
import regex as re
import pandas as pd
from lda import LDA
from datetime import datetime
from bs4 import BeautifulSoup
from alive_progress import alive_bar
from gensim.parsing.preprocessing import remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
from selenium.webdriver.chrome.options import Options
from alive_progress import alive_bar

warnings.simplefilter(action="ignore", category=FutureWarning)
warnings.simplefilter(action="ignore", category=RuntimeWarning)

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
GLOVE_DIR = os.path.join(ROOT_DIR, "glove_data", "results", "vectors.txt")
GUARDIAN_DIR = os.path.join(ROOT_DIR, "data", "Guardian.csv")
REUTERS_DIR = os.path.join(ROOT_DIR, "data", "Reuters.csv")
CNN_DIR = os.path.join(ROOT_DIR, "data", "CNN.csv")
DAILYMAIL_DIR = os.path.join(ROOT_DIR, "data", "DailyMail.csv")


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
            print(f"→ CSV file found with {self.getLen()} articles! Latest article date: {self.getDate()}")
            print("→ Checking articles from latest date onward...")
        else:
            print(f"→ No CSV file found. Creating...")

        lenBefore = self.getLen()
        urls = []
        titles = []
        bodies = []
        dates = []

        with alive_bar(title="→ Guardian: API Request", bar=None, spinner="dots", force_tty=True) as bar:
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

        data.to_csv(GUARDIAN_DIR)
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

        with alive_bar(title="→ Reuters: Searching for latest date", bar=None, spinner="dots", force_tty=True) as bar:

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
                # print("Reuters.csv found!")
                i = 1

            while not common_between_lists(urls_from_page(i)):
                i += 1
                bar()
            # print(f"-> Last page scraped: {i+1}")
            self.latestPage = i + 1

    def URLFetcher(self):
        self.urls = []
        with alive_bar(title="→ Reuters: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
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

        with alive_bar(len(self.unique_urls), title="→ Reuters: Scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
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
        # print("-> New data fetched successfully!")
        self.new_data = data

    def scraper(self):
        self.fromScratch()
        self.latestPage()
        self.URLFetcher()
        self.articleFetcher()
        data = self.concatData(self.new_data)
        lenAfter = len(data) - len(self.reuters_data)
        if lenAfter == 0:
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to Reuters.csv! Total articles: {len(data)}")
        data.to_csv(REUTERS_DIR, index=True)

        return data


class CNN:
    def __init__(self) -> None:
        self.source = "CNN"

    def seleniumParams(self):
        s = Service(ChromeDriverManager(chrome_type=ChromeType.BRAVE, path=ROOT_DIR).install())
        o = webdriver.ChromeOptions()
        o.add_argument("headless")
        self.driver = webdriver.Chrome(service=s, options=o)
        ignored_exceptions = (NoSuchElementException, StaleElementReferenceException)
        self.wait = WebDriverWait(self.driver, 10, ignored_exceptions=ignored_exceptions)

    def fromScratch(self):
        if not os.path.exists(CNN_DIR):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            self.from_scratch = True
        else:
            self.old_data = pd.read_csv(CNN_DIR)
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

        if self.from_scratch == False:
            last_url = self.old_data.iloc[0, 1]
        elif self.from_scratch == True:
            last_url = "https://www.cnn.com/2021/05/11/politics/romania-nato-exercises-russia/index.html"

        self.seleniumParams()
        with alive_bar(title=f"→ {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            for page in range(0, 95):  # 95
                url = "https://edition.cnn.com/search?q=ukraine+russia&from=" + str(page * 50) + "&size=50&page=1&sort=newest&types=article&section="
                title_tag = "//div//a[@class='container__link __link']"
                exc_list = ["/tennis/", "/live-news/", "/opinions/", "/tech/", "/sport/", "/us/", "/football/", "/china/", "/style/", "/business-food/", "/americas/", "/travel/", "/business/"]
                inc_list = ["/2022/", "/2021/"]
                self.driver.get(url)
                try:
                    titles = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, title_tag)))
                    for title in titles:
                        url = title.get_attribute("href")
                        if not any(s in url for s in exc_list) and any(s in url for s in inc_list):
                            self.urls.append(url)
                        if last_url == url:
                            break
                    if last_url == url:
                        break
                except Exception as e:
                    print(f"Error in page {page}: {e}")
                    pass
                bar()
            self.driver.quit()
        self.unique_urls = list(dict.fromkeys(self.urls))
        print(f"→ {len(self.unique_urls)} URLs fetched successfully!")

    def articleScraper(self):
        bodies = []
        titles = []
        dates = []
        urls = []
        rep = {"This story has been updated with additional information.": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"→ {self.source}: Article scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    title_tags = ["pg-headline"]
                    text_tags = ["zn-body__paragraph"]
                    opener_tag = ["zn-body__paragraph speakable"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h1", class_=title_tags).text
                    opener = soup.find("p", class_=opener_tag).text
                    paragraphs = soup.find_all("div", class_=text_tags)
                    body = opener + ""
                    for _ in paragraphs:
                        body += " " + _.text
                    body = replaceAll(body, rep)
                    bodies.append(re.sub(r"^[^\)]*\)", "", " ".join(body.split())))  # Local tag
                    titles.append(title)
                    urls.append(url)
                    dates.append(url[20:][:10].replace("/", "-"))
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
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to {self.source}.csv! Total articles: {len(data)}")
        data.to_csv(CNN_DIR, index=True)

        return data


class DailyMail:
    def __init__(self) -> None:
        self.source = "DailyMail"

    def fromScratch(self):
        if not os.path.exists(DAILYMAIL_DIR):
            self.old_data = pd.DataFrame(columns=["Date", "URL", "Title", "Text"])
            self.from_scratch = True
        else:
            self.old_data = pd.read_csv(DAILYMAIL_DIR)
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

        if self.from_scratch == False:
            last_url = self.old_data.iloc[0, 1]
        elif self.from_scratch == True:
            last_url = "https://www.dailymail.co.uk/news/article-10626865/Boris-plans-face-face-meeting-Biden-emergency-NATO-summit.html"

        with alive_bar(title=f"→ {self.source}: Fetching URLs in pages", bar=None, spinner="dots", force_tty=True) as bar:
            for page in range(0, 5):  # 95
                leading_url = "https://www.dailymail.co.uk"
                url = "https://www.dailymail.co.uk/home/search.html?offset=" + str(page * 50) + "&size=50&sel=site&searchPhrase=ukraine+russia&sort=recent&channel=news&type=article&days=all"
                title_tag = "sch-res-title"
                try:
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    headlines = soup.find_all("h3", class_=title_tag)
                    for headline in headlines:
                        _ = headline.find("a", href=True)
                        url = leading_url + _["href"]
                        self.urls.append(url)
                        if last_url == url:
                            break
                    if last_url == url:
                        break
                except Exception as e:
                    print(f"Error in page {page}: {e}")
                    pass
                bar()
        self.unique_urls = list(dict.fromkeys(self.urls))
        print(f"→ {len(self.unique_urls)} URLs fetched successfully!")

    def articleScraper(self):
        bodies = []
        titles = []
        dates = []
        urls = []
        rep = {"The Mail on Sunday can reveal:": "", "RELATED ARTICLES": "", "Share this article": ""}

        def replaceAll(text, dic):
            for i, j in dic.items():
                text = text.replace(i, j)
            return text

        with alive_bar(len(self.unique_urls), title=f"→ {self.source}: Article scraper", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for url in self.unique_urls:
                try:
                    title_tags = ["pg-headline"]
                    text_tags = ["mol-para-with-font"]
                    date_box_tag = ["article-timestamp article-timestamp-published"]
                    html_text = requests.get(url).text
                    soup = BeautifulSoup(html_text, "lxml")
                    title = soup.find("h2").text
                    date_box = soup.find("span", class_=date_box_tag)
                    date = date_box.find("time")
                    paragraphs = soup.find_all("p", class_=text_tags)
                    body = ""
                    for _ in paragraphs:
                        body += " " + _.text
                    body = replaceAll(body, rep)
                    bodies.append(" ".join(body.split()))
                    titles.append(title)
                    urls.append(url)
                    dates.append(date.get("datetime")[:10])
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
            print(f"→ No new articles found. Total articles: {len(data)}")
        else:
            print(f"→ {lenAfter} new articles saved to {self.source}.csv! Total articles: {len(data)}")
        data.to_csv(DAILYMAIL_DIR, index=True)

        return data


class NTR:
    def __init__(self) -> None:
        self.dataG = pd.read_csv(GUARDIAN_DIR)
        self.dataR = pd.read_csv(REUTERS_DIR)
        self.dataCNN = pd.read_csv(CNN_DIR)
        pass

    def learn_topics(self, dataframe, topicnum, vocabsize, num_iter):

        # Removes stopwords
        texts = dataframe["Text"].tolist()
        texts_no_sw = []
        for text in texts:
            text_no_sw = remove_stopwords(text)
            texts_no_sw.append(text_no_sw)
        texts = texts_no_sw
        CVzer = CountVectorizer(token_pattern=r"(?u)\b[^\W\d]{2,}\b", max_features=vocabsize, lowercase=True)
        doc_vcnts = CVzer.fit_transform(texts)
        vocabulary = CVzer.get_feature_names_out()
        lda_model = LDA(topicnum, n_iter=num_iter, refresh=100)
        doc_topic = lda_model.fit_transform(doc_vcnts)
        topic_word = lda_model.topic_word_

        return doc_topic, topic_word, vocabulary

    def save_topicmodel(self, doc_topic, topic_word, vocabulary, source):

        topicmixture_outpath = os.path.join(ROOT_DIR, "results", source + "TopicMixtures.txt")
        np.savetxt(topicmixture_outpath, doc_topic)
        topic_outpath = os.path.join(ROOT_DIR, "results", source + "Topics.txt")
        np.savetxt(topic_outpath, topic_word)
        vocab_outpath = os.path.join(ROOT_DIR, "results", source + "Vocab.txt")
        with open(vocab_outpath, mode="w", encoding="utf-8") as f:
            for v in vocabulary:
                f.write(v + "\n")

        return topicmixture_outpath, topic_outpath, vocab_outpath

    def KLdivergence_from_probdist_arrays(self, pdists0, pdists1):

        assert pdists0.shape == pdists1.shape, "pdist* shapes must be identical"
        if len(pdists0.shape) == 1:
            KLdivs = (pdists1 * np.log2(pdists1 / pdists0)).sum()
        elif len(pdists0.shape) == 2:
            KLdivs = (pdists1 * np.log2(pdists1 / pdists0)).sum(axis=1)

        return KLdivs

    def novelty_transience_resonance(self, thetas_arr, scale):

        speechstart = scale
        speechend = thetas_arr.shape[0] - scale
        novelties = []
        transiences = []
        resonances = []
        for j in range(speechstart, speechend, 1):
            center_theta = thetas_arr[j]
            after_boxend = j + scale + 1
            before_boxstart = j - scale
            before_theta_arr = thetas_arr[before_boxstart:j]
            beforenum = before_theta_arr.shape[0]
            before_centertheta_arr = np.tile(center_theta, reps=(beforenum, 1))
            after_theta_arr = thetas_arr[j + 1 : after_boxend]
            afternum = after_theta_arr.shape[0]
            after_centertheta_arr = np.tile(center_theta, reps=(afternum, 1))
            before_KLDs = self.KLdivergence_from_probdist_arrays(before_theta_arr, before_centertheta_arr)
            after_KLDs = self.KLdivergence_from_probdist_arrays(after_theta_arr, after_centertheta_arr)
            novelty = np.mean(before_KLDs)
            transience = np.mean(after_KLDs)
            novelties.append(novelty)
            transiences.append(transience)
            resonances.append(novelty - transience)
        for index in range(0, scale):
            transiences.insert(0, 0)
            transiences.append(0)
            novelties.insert(0, 0)
            novelties.append(0)
            resonances.insert(0, 0)
            resonances.append(0)

        return novelties, transiences, resonances

    def save_novel_trans_reson(self, novelties, transiences, resonances, source):

        outpath = ROOT_DIR + "/results/" + source + "NovelTransReson.txt"
        np.savetxt(outpath, np.vstack(zip(novelties, transiences, resonances)))

    def routine(self, period, topicnum, vocabsize, num_iter):

        sources = ["Guardian", "Reuters", "CNN"]
        sets = [self.dataG, self.dataR, self.dataCNN]
        print("")
        for i in range(0, len(sources)):
            data, source = sets[i], sources[i]
            print(f"→ Starting {source} topic modeling (LDA)...")
            doc_topic, topic_word, vocabulary = self.learn_topics(data, topicnum, vocabsize, num_iter)
            topics = []
            for i in range(len(data)):
                topics.append(doc_topic[i].argmax())
            self.save_topicmodel(doc_topic, topic_word, vocabulary, source)
            novelties, transiences, resonances = self.novelty_transience_resonance(doc_topic, period)
            self.save_novel_trans_reson(novelties, transiences, resonances, source)
            ntr_data = data
            ntr_data["Novelty"] = novelties
            ntr_data["Transience"] = novelties
            ntr_data["Resonance"] = resonances
            ntr_data["Topic"] = topics
            ntr_data.to_csv(ROOT_DIR + "/results/" + source + "_results.csv", index=False)
            print("")

        print("→ All LDA data saved.\n")


class Uncertainty:
    def __init__(self) -> None:
        self.dataG = pd.read_csv(os.path.join(ROOT_DIR, "results", "Guardian_results.csv"))
        self.dataR = pd.read_csv(os.path.join(ROOT_DIR, "results", "Reuters_results.csv"))

    def load_glove_model(self, terms):
        common_vectors = []
        with open(os.path.join(GLOVE_DIR), "r", encoding="utf8") as f:
            for line in f:
                if line.split(None, 1)[0] in terms:
                    common_vectors.append(line.replace("\n", ""))

        glove_model = {}
        for line in common_vectors:
            split_line = line.split()
            word = split_line[0]
            embedding = np.array(split_line[1:], dtype=np.float64)
            glove_model[word] = embedding
        return glove_model

    def article_index(self, article_text):

        # dictionaries
        economic_terms = ["economy", "economic"]
        uncertainty_terms = []
        with open(os.path.join(ROOT_DIR, "data", "Uncertainty.txt"), "r") as f:
            for line in f:
                uncertainty_terms.append(line.lower().replace("\n", ""))
        article_vocab = [word.lower() for word in nltk.word_tokenize(article_text) if word.isalpha()]

        common_uncertainty_terms = list(set(article_vocab).intersection(uncertainty_terms))
        common_economic_terms = list(set(article_vocab).intersection(economic_terms))

        if len(common_economic_terms) == 0 or len(common_uncertainty_terms) == 0:
            return 0

        # index
        common_uncertainty_vectors = self.load_glove_model(common_uncertainty_terms)
        common_economic_vectors = self.load_glove_model(common_economic_terms)

        common_uncertainty_matrix = np.array(list(common_uncertainty_vectors.values()))
        common_economic_matrix = np.array(list(common_economic_vectors.values()))

        mean_common_uncertainty_terms = np.mean(common_uncertainty_matrix, axis=0)
        mean_common_economic_terms = np.mean(common_economic_matrix, axis=0)

        index = 1 / LA.norm((mean_common_economic_terms) - (mean_common_uncertainty_terms))

        return index

    def normalize_index(self, dataframe):
        indexes = dataframe.iloc[:, 1].values.tolist()
        largest = max(indexes)
        smallest = min(indexes)
        denom = largest - smallest
        new_indexes = [(x - smallest) / denom for x in indexes]
        dataframe.iloc[:, 1] = new_indexes

        return dataframe

    def dataframe_EU_index(self, dataframe, source):

        indexes = []
        dates = []
        titles = []
        with alive_bar(len(dataframe), title=f"→ Calculating {source} indexes", spinner="dots_waves", bar="smooth", force_tty=True) as bar:
            for i in range(0, len(dataframe)):
                bar()
                index = self.article_index(dataframe.iloc[i, 3])
                indexes.append(index)
                dates.append(dataframe.iloc[i, 0])
                titles.append(dataframe.iloc[i, 2])

        unc_df = pd.DataFrame({"Title": titles, "EU Index": indexes})
        unc_df = self.normalize_index(unc_df)

        return unc_df

    def routine(self):
        sources = ["Guardian", "Reuters"]
        sets = [self.dataG, self.dataR]
        for i in range(0, len(sources)):
            data, source = sets[i], sources[i]
            data_EU_index = self.dataframe_EU_index(data, source)
            data_results = pd.merge(data, data_EU_index, on="Title", how="outer")
            data_results.to_csv(os.path.join(ROOT_DIR, "results", source + "_results.csv"), index=False)
            print("")


if __name__ == "__main__":
    # Guardian().scraper()
    # Reuters().scraper()
    CNN().scraper()
    DailyMail().scraper()
    NTR().routine(period=7, topicnum=30, vocabsize=10000, num_iter=100)
    # Uncertainty().routine()
