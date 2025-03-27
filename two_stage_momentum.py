from datetime import datetime
from prep_data import extract_data
import pandas as pd
import json
from trading_cost import quoted_spread, pick_random_day
import numpy as np

rng = np.random.default_rng(1)


def compute_return(returns):
    """
    Computes compound return given list of simple returns
    """
    final_return = 1
    for r in returns:
        final_return *= 1 + r

    return final_return - 1


def find_momentum_split(
    stock_data: pd.DataFrame, long_split_proportion=0.2, short_split_proportion=0.2
):
    """
    Finds momentum strategy long and short legs
    """
    stock_returns = (
        stock_data.groupby(["PERMNO", "month"])[["DlyRet", "quoted_spread"]]
        .agg(
            returns=("DlyRet", compute_return),
            day_quoted_spread=(
                "quoted_spread",
                lambda group: pick_random_day(group, rng),
            ),
        )
        .groupby(["PERMNO"])
        .agg(
            returns=("returns", compute_return),
            avg_quoted_spread=("day_quoted_spread", "mean"),
        )
    )

    return (
        stock_returns.nlargest(
            int(len(stock_returns) * long_split_proportion), "returns"
        ),
        stock_returns.nsmallest(
            int(len(stock_returns) * short_split_proportion), "returns"
        ),
    )


def adjust_momentum_with_costs(data, cost_sensitivity=1, keep_long=0.5, keep_short=0.5):
    """
    Adjusts initial momentum sort with trading costs, resorts
    """

    long_split, short_split = find_momentum_split(data)

    return (
        dict(
            (
                long_split["returns"]
                - cost_sensitivity * long_split["avg_quoted_spread"]
            ).nlargest(int(len(long_split) * keep_long))
        ),
        dict(
            (
                short_split["returns"]
                + cost_sensitivity * short_split["avg_quoted_spread"]
            ).nlargest(int(len(short_split) * keep_short))
        ),
    )


def find_splits_per_date(data):
    # TODO: optimise
    """ "
    Finds the two-stage sorting long and short legs
    """
    splits = dict()

    for date in pd.date_range(
        start=datetime(2019, 12, 31), end=datetime(2024, 12, 31), freq="ME"
    ):
        print(date)
        long_split, short_split = adjust_momentum_with_costs(
            data[
                (data["DlyCalDt"] <= date)
                & (data["DlyCalDt"] > date - pd.DateOffset(years=1))
            ],
            date,
        )
        splits[str(date.to_pydatetime().date())] = {
            "long_split": list(long_split.keys()),
            "short_split": list(short_split.keys()),
        }

    return splits


def main():
    with open("final_split.json", "w") as file:
        json.dump(find_splits_per_date(extract_data("2019-2024 v2.csv")), file)


if __name__ == "__main__":
    main()
