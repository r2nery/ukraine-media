from ap import AP
from fox import Fox
from cnn import CNN
from abc import ABC
from cbs import CBS
from nyt import NYT
from mirror import Mirror
from reuters import Reuters
from express import Express
from guardian import Guardian
from dailymail import DailyMail
import pandas as pd
import os
import pyarrow as pa
import pyarrow.parquet as pq

ROOT_DIR = os.path.dirname(os.path.abspath("__file__"))
DATA_DIR = os.path.join(ROOT_DIR, "data")


def unite_sources():
    total = 0
    sources = [i[:-4] for i in os.listdir(os.path.join(DATA_DIR, "raw")) if str(i).endswith(".csv")]
    result = pd.DataFrame(columns=["Source", "Date", "URL", "Title", "Text"])
    print("-> Dataset Sizes:")
    for source in sources:
        data = pd.read_csv(os.path.join(DATA_DIR, "raw", f"{source}.csv"))
        data["Source"] = source
        print(f"{source}: {len(data)} Articles")
        total += len(data)
        result = pd.concat([result, data])
    result = result.drop_duplicates(subset=["Text"])
    result = result.set_index("Date")
    result = result.sort_index(ascending=False)
    result.to_csv(os.path.join(DATA_DIR, "raw", "All.csv"), index=True)
    print(f"-> Saved CSV with {total} articles.\n")


def csv_to_parquet():
    print("-> Converting CSV to Parquet...")
    df = pd.read_csv(os.path.join(DATA_DIR, "raw", "All.csv"))
    table = pa.Table.from_pandas(df)
    pq.write_table(
        table,
        os.path.join(DATA_DIR, "raw", "All.parquet"),
        compression="brotli",
        compression_level=11,
    )
    print(f"-> Saved Parquet with {len(df)} articles.")


if __name__ == "__main__":

    # NYT().scraper()
    # CNN().scraper()
    # Guardian().scraper()
    # Fox().scraper()
    # Reuters().scraper()
    # AP().scraper()
    # CBS().scraper()
    # ABC().scraper()
    # Express().scraper()
    # Mirror().scraper()
    # DailyMail().scraper()
    # unite_sources()
    # csv_to_parquet()

    pass
