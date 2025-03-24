import os
from dotenv import load_dotenv
import pandas as pd
import wrds
from decimal import Decimal


def query_data(db):
    df = db.raw_sql(
        """
            select
                permno, ticker, yyyymmdd, dlycaldt, dlyprevprc, dlyvol,
                dlyclose, dlybid, dlyask
            from crsp.wrds_dsfv2_query
            where yyyymmdd >= 20240101
        """
    )

    print(df)


def extract_data(path):
    # TODO: issue, we lose 8mil out of 13mil data after dropna and removing str instances
    data = pd.read_csv(path)
    data = data.dropna()
    data = data[data["PERMNO"] < 12000]
    data = data[~data["RET"].apply(lambda x: isinstance(x, str))]

    data["date"] = pd.to_datetime(data["date"])
    data["RET"] = data["RET"].astype("float")

    return data


def main():
    df = extract_data("2019-2024_data.csv")
    df = df.dropna()


if __name__ == "__main__":
    load_dotenv()
    main()
