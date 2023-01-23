import pandas as pd
import regex as re
import os
from scrapers.ap import AP_DIR
from scrapers.fox import FOX_DIR
from scrapers.cnn import CNN_DIR
from scrapers.abc import ABC_DIR
from scrapers.cbs import CBS_DIR
from scrapers.nyt import NYT_DIR
from scrapers.mirror import MIRROR_DIR
from scrapers.reuters import REUTERS_DIR
from scrapers.express import EXPRESS_DIR
from scrapers.guardian import GUARDIAN_DIR
from scrapers.dailymail import DAILYMAIL_DIR

from scipy.stats import pearsonr, spearmanr

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))


def unite_sources():

    total = 0
    data = [pd.read_csv(i) for i in globals().values() if str(i).endswith(".csv")]
    sources = [str(re.sub(r"^(.*data)(\W+)", "", i[:-4])) for i in globals().values() if str(i).endswith(".csv")]
    result = pd.DataFrame(columns=["Source", "Date", "URL", "Title", "Text"])
    print("-> Current Dataset:")
    for i, j in zip(data, sources):
        if j == "All":
            continue
        i["Source"] = j
        print(f"{j}: {len(i)} Articles")
        total += len(i)
        result = pd.concat([result, i])
    result = result.drop_duplicates(subset=["Text"])
    result = result.set_index("Date")
    result = result.sort_index(ascending=False)
    result.to_csv(os.path.join(ROOT_DIR, "data", "All.csv"), index=True)
    print(f"-> Saved CSV with {total} articles.\n")


