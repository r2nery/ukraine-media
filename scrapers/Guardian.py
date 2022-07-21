import os
import pandas as pd
import re
from alive_progress import alive_bar
import requests
from bs4 import BeautifulSoup

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(ROOT_DIR)
FILE = "Guardian.csv"
keyG = "fad78733-31a0-4ea7-8823-ba815b578899"


def getLen(FILE):
    if os.path.exists(PARENT_DIR + "/data/" + FILE):
        check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
        return len(check)
    else:
        return 0


def getDate(FILE):
    if os.path.exists(PARENT_DIR + "/data/" + FILE):
    #    check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
    #    return check.iloc[0, 0]
    #else:
        return "2021-02-01"


def numArticlesInPage(json):
    if json["response"]["total"] - json["response"]["startIndex"] >= 200:
        return 200
    else:
        return json["response"]["total"] - json["response"]["startIndex"] + 1


def replaceAll(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


def save(dataF, FILE):
    if os.path.exists(PARENT_DIR + "/data/" + FILE):
        existingData = pd.read_csv(PARENT_DIR + "/data/" + FILE)
        data = pd.concat([existingData, dataF])
        data = data.drop_duplicates(keep="first")
        data.to_csv(PARENT_DIR + "/data/" + FILE, index=False)
        return data
    else:
        dataF.to_csv(PARENT_DIR + "/data/" + FILE, index=False)
        return dataF


def concatData(old, new):
    result = pd.concat([old, new])
    result = result.drop_duplicates(subset=["Text"])
    result = result.set_index("Date")
    result = result.sort_index(ascending=False)
    return result


def guardian(page, tag):
    return requests.get("https://content.guardianapis.com/search?api-key=" + keyG + "&from-date=" + str(getDate(FILE)) + "&type=article" + "&page=" + str(page) + "&tag=world/" + tag + "&order-by=oldest" + "&show-fields=body" + "&page-size=200")


def guardianScraper():

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


    if os.path.exists(PARENT_DIR + "/data/" + FILE):
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
    
    # Instancing a query to fetch basic information
    numPages = guardian(1, "ukraine").json()["response"]["pages"]

    with alive_bar(title="-> Ukraine API Query", unknown="dots_waves", spinner=None, force_tty=True) as bar:

        # Going through all pages available for the query
        for i in range(1, numPages + 1):

            json_guardian = guardian(i, "ukraine").json()

            # Going through all articles in a page
            for j in range(0, numArticlesInPage(json_guardian)):

                if os.path.exists(PARENT_DIR + "/data/" + FILE):
                    old_data = pd.read_csv(PARENT_DIR + "/data/" + FILE)
                    if json_guardian["response"]["results"][j]["webUrl"] == old_data.iloc[-1, 0]:
                        continue

                urls.append(json_guardian["response"]["results"][j]["webUrl"])
                fulldate = json_guardian["response"]["results"][j]["webPublicationDate"]
                dates.append(fulldate[: len(fulldate) - 10])

                title = json_guardian["response"]["results"][j]["webTitle"]
                titles.append(re.sub(r"\|.*$", "", title))  # removing authors from titles

                body = BeautifulSoup(json_guardian["response"]["results"][j]["fields"]["body"], "html.parser").get_text()
                body = replaceAll(body, rep)  # replacing substrings
                bodies.append(re.sub(r"[\t\r\n]", "", body))  # removing line breaks
                bar()

    # Instancing a query to fetch basic information
    numPages = guardian(1, "russia").json()["response"]["pages"]

    with alive_bar(title="-> Russia API Query", unknown="dots_waves", spinner=None, force_tty=True) as bar:

        # Going through all pages available for the query
        for i in range(1, numPages + 1):

            json_guardian = guardian(i, "russia").json()

        # Going through all articles in a page
        for j in range(0, numArticlesInPage(json_guardian)):

            if os.path.exists(PARENT_DIR + "/data/" + FILE):
                old_data = pd.read_csv(PARENT_DIR + "/data/" + FILE)
                if json_guardian["response"]["results"][j]["webUrl"] == old_data.iloc[-1, 0]:
                    continue

            urls.append(json_guardian["response"]["results"][j]["webUrl"])
            fulldate = json_guardian["response"]["results"][j]["webPublicationDate"]
            dates.append(fulldate[: len(fulldate) - 10])

            title = json_guardian["response"]["results"][j]["webTitle"]
            titles.append(re.sub(r"\|.*$", "", title))  # removing authors from titles

            body = BeautifulSoup(json_guardian["response"]["results"][j]["fields"]["body"], "html.parser").get_text()
            body = replaceAll(body, rep)  # replacing substrings
            bodies.append(re.sub(r"[\t\r\n]", "", body))  # removing line breaks
            bar()

    # Transforming fetched info to dataframe
    new_data = pd.DataFrame({"URL": urls, "Date": dates, "Title": titles, "Text": bodies})

    # Saving to csv. Will concat if csv altready exists
    data = concatData(old_data, new_data)
    lenAfter = len(data) - lenBefore

    if lenAfter == 0:
        print(f"-> No new articles found. Total articles: {len(data)}")
    else:
        print(f"-> {lenAfter} new articles saved to {FILE}! Total articles: {len(data)}")

    return data
