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
    print(data["ShareType"].unique())
    data = data[data["PrimaryExch"] == "N"]
    data = data[~data["DlyRet"].apply(lambda x: isinstance(x, str))]

    data["DlyCalDt"] = pd.to_datetime(data["DlyCalDt"])
    data["year"] = data["DlyCalDt"].dt.year
    data["month"] = data["DlyCalDt"].dt.month
    data["quoted_spread"] = (
        2 * (data["DlyAsk"] - data["DlyBid"]) / (data["DlyAsk"] + data["DlyBid"])
    )
    data["DlyRet"] = data["DlyRet"].astype("float")

    return data


def main():
    df = extract_data("2019-2024 v2.csv")
    df = df.dropna()


if __name__ == "__main__":
    load_dotenv()
    main()
