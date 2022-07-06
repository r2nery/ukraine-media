import pandas as pd
import os
import re

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(ROOT_DIR)


def mkDir():
    os.makedirs(PARENT_DIR + "/data", exist_ok=True)


# Function that checks if a file exists
def fileExists(FILE):
    return os.path.exists(PARENT_DIR + "/data/" + FILE)


# Function that returns a file
def getFile(FILE):
    return pd.read_csv(PARENT_DIR + "/data/" + FILE)


# Function that checks latest data parsed, if any. If none, defaults to 20220201
def getDate(FILE):
    if FILE == "NYT.csv":
        if fileExists(FILE):
            check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
            return re.match(r"^[^T]*", check.iloc[-1, 1]).group(0).replace("-", "")
        else:
            return "20220201"
    if FILE == "Guardian.csv":
        if fileExists(FILE):
            check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
            return re.match(r"^[^T]*", check.iloc[-1, 1]).group(0)
        else:
            return "2022-02-01"


# Function that returns length of existing dataset
def getLen(FILE):
    if fileExists(FILE):
        check = pd.read_csv(PARENT_DIR + "/data/" + FILE)
        return len(check)
    else:
        return 0


# Function that returns the number of articles in the current API query page
def numArticlesInPage(json, FILE):
    if FILE == "Guardian.csv":
        if json["response"]["total"] - json["response"]["startIndex"] >= 200:
            return 200
        else:
            return json["response"]["total"] - json["response"]["startIndex"] + 1
    elif FILE == "NYT.csv":
        if json["response"]["meta"]["hits"] - json["response"]["meta"]["offset"] >= 10:
            return 10
        else:
            return json["response"]["meta"]["hits"] - json["response"]["meta"]["offset"]


# Function that clears text of a dict of substrings
def replaceAll(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


# Saving function
def save(dataF, FILE):
    if fileExists(FILE):
        existingData = pd.read_csv(PARENT_DIR + "/data/" + FILE)
        data = pd.concat([existingData, dataF])
        data = data.drop_duplicates(keep="first")
        data.to_csv(PARENT_DIR + "/data/" + FILE, index=False)
        return data
    else:
        dataF.to_csv(PARENT_DIR + "/data/" + FILE, index=False)
        return dataF