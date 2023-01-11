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


def correlate(dir, source, resample, pval, correlation, compare):
    events = pd.read_csv(os.path.join(ROOT_DIR, "data", "Ukraine_Black_Sea_2020_2022_Nov18.csv"), parse_dates=["EVENT_DATE"])
    events = events[["EVENT_DATE", "EVENT_TYPE", "FATALITIES"]].rename(columns={"EVENT_DATE": "Date", "EVENT_TYPE": "Count", "FATALITIES": "Fatalities"})  # pegando somente colunas relevantes
    events = events.set_index("Date")  # convertendo coluna de datas pra datetime e setando indice
    events = events.resample(resample).agg({"Count": "count", "Fatalities": "sum"})  # resample: contagem de eventos, soma de fatalidades

    results = pd.read_csv(os.path.join(dir, f"{source}_Results.csv"), parse_dates=["Date"], index_col=["Date"])
    results = results[["Resonance", "Novelty", "Transience"]]
    results = results.sort_index()
    results = results.loc["2018-01-01":"2022-11-18"]  # Matching other dataframe
    results = results.resample(resample).sum()
    results[["Count", "Fatalities"]] = events[["Count", "Fatalities"]].copy()
    results = results.loc["2020-01-01":"2022-11-16"]

    s_fatalities, s_fatalities_p = spearmanr(results["Fatalities"], results["Resonance"])
    p_fatalities, p_fatalities_p = pearsonr(results["Fatalities"], results["Resonance"])
    s_events, s_events_p = spearmanr(results["Count"], results["Resonance"])
    p_events, p_events_p = pearsonr(results["Count"], results["Resonance"])

    if correlation == "pearson":
        print("Pearson")
        if p_fatalities_p <= pval and compare == "fat":
            print(f"{source} (R X F) Pearson: {p_fatalities:.4f} p-value: {p_fatalities_p:.4f}")
        if p_events_p <= pval and compare == "eve":
            print(f"{source} (R X CE) Pearson: {p_events:.4f} p-value: {p_events_p:.4f}")

    if correlation == "spearman":
        print("Spearman")
        if s_fatalities_p <= pval and compare == "fat":
            print(f"{source} (R X F) Spearman: {s_fatalities:.4f} p-value: {s_fatalities_p:.4f}")
        if s_events_p <= pval and compare == "eve":
            print(f"{source} (R X CE) Spearman: {s_events:.4f} p-value: {s_events_p:.4f}")
