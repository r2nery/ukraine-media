import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import math
from alive_progress import alive_bar
from utilities import *


def NYTScraper():
    ## Global definitions

    # NYT API key
    keyNYT = "BwemetlgrQFLmyML7BqSZqCjYgMvyANE"

    # Directories
    FILE = "NYT.csv"
    mkDir()

    # Query setup function
    def NYT(page):
        return requests.get(
            "https://api.nytimes.com/svc/search/v2/articlesearch.json?&api-key="
            + keyNYT
            + "&begin_date="
            + str(getDate(FILE))
            + "&sort=oldest"
            + "&fl=web_url%2Cheadline%2Cword_count%2Csnippet%2Clead_paragraph%2Cpub_date%2Ctype_of_material%2Cdocument_type"
            + "&fq=type_of_material%3A(%22News%22)&page="
            + str(page)
            + "&q=ukraine"
        )

    ## Scraper

    # Instancing a query to fetch basic information
    numArticles = NYT(1).json()["response"]["meta"]["hits"]
    numPages = math.ceil(numArticles / 10)

    if fileExists(FILE):
        print(f"-> CSV file found with {getLen(FILE)} articles! Latest article date: {getDate(FILE)}")
        print("-> Checking articles from latest date onward...")
    else:
        print(f"-> No CSV file found. Creating...")

    lenBefore = getLen(FILE)

    # Instancing
    urls = []
    titles = []
    bodies = []
    dates = []
    snippets = []

    # Loops
    with alive_bar(title="-> API Query", unknown="dots_waves", spinner=None, force_tty=True) as bar:

        # Going through all pages available for the query
        for i in range(0, min(200, numPages)):

            time.sleep(6)  # NYT request limit
            json_NYT = NYT(i).json()

            # Going through all articles in a page
            for j in range(0, numArticlesInPage(json_NYT, FILE)):

                urls.append(json_NYT["response"]["docs"][j]["web_url"])
                dates.append(json_NYT["response"]["docs"][j]["pub_date"])

                titles.append(json_NYT["response"]["docs"][j]["headline"]["main"])
                # titles.append(re.sub(r"\|.*$", "", title)) # removing authors from titles

                body = BeautifulSoup(json_NYT["response"]["docs"][j]["lead_paragraph"], "html.parser").get_text()
                # body = replaceAll(body, rep)  # replacing substrings
                body = re.sub(r"^[^—]+—\s*", "", body)
                bodies.append(re.sub(r"[\t\r\n]", "", body))  # removing line breaks

                # snippet = BeautifulSoup(json_NYT["response"]["docs"][j]["snippet"], "html.parser").get_text()
                # snippets.append(re.sub(r"^[^—]+—\s*", "", snippet))
                bar()

    # Transforming fetched info to dataframe
    data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})

    # Removing NaNs
    data = data.dropna(subset=["Text"])

    # Saving to csv. Will concat if csv altready exists
    data = saveCSV(data, FILE)

    lenAfter = len(data) - lenBefore

    if lenAfter == 0:
        print(f"-> No new articles found. Total articles: {len(data)}")
    else:
        print(f"-> {lenAfter} new articles saved to {FILE}! Total articles: {len(data)}")


def guardianScraper():
    ## Global definitions

    # The Guardian API key
    keyG = "fad78733-31a0-4ea7-8823-ba815b578899"

    # Directories
    FILE = "Guardian.csv"
    mkDir()

    # Query setup function
    def guardian(page):
        return requests.get("https://content.guardianapis.com/search?api-key=" + keyG + "&from-date=" + str(getDate(FILE)) + "&type=article" + "&page=" + str(page) + "&tag=world/ukraine" + "&order-by=oldest" + "&show-fields=body" + "&page-size=200")

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

    # Instancing a query to fetch basic information
    numPages = guardian(1).json()["response"]["pages"]

    if fileExists(FILE):
        print(f"-> CSV file found with {getLen(FILE)} articles! Latest article date: {getDate(FILE)}")
        print("-> Checking articles from latest date onward...")
    else:
        print(f"-> No CSV file found. Creating...")

    lenBefore = getLen(FILE)

    # Instancing
    urls = []
    titles = []
    bodies = []
    dates = []

    # Loops
    with alive_bar(title="-> API Query", unknown="dots_waves", spinner=None, force_tty=True) as bar:

        # Going through all pages available for the query
        for i in range(1, numPages + 1):

            json_guardian = guardian(i).json()

            # Going through all articles in a page
            for j in range(0, numArticlesInPage(json_guardian, FILE)):

                existingData = readCSV(FILE)
                if json_guardian["response"]["results"][j]["webUrl"] == existingData.iloc[-1, 0]:
                    continue

                urls.append(json_guardian["response"]["results"][j]["webUrl"])
                dates.append(json_guardian["response"]["results"][j]["webPublicationDate"])

                title = json_guardian["response"]["results"][j]["webTitle"]
                titles.append(re.sub(r"\|.*$", "", title))  # removing authors from titles

                body = BeautifulSoup(json_guardian["response"]["results"][j]["fields"]["body"], "html.parser").get_text()
                body = replaceAll(body, rep)  # replacing substrings
                bodies.append(re.sub(r"[\t\r\n]", "", body))  # removing line breaks
                bar()

    # Transforming fetched info to dataframe
    data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})

    # Removing NaNs
    data = data.dropna(subset=["Text"])

    # Saving to csv. Will concat if csv altready exists
    data = saveCSV(data, FILE)
    lenAfter = len(data) - lenBefore

    if lenAfter == 0:
        print(f"-> No new articles found. Total articles: {len(data)}")
    else:
        print(f"-> {lenAfter} new articles saved to {FILE}! Total articles: {len(data)}")

    return
