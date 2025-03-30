from datetime import datetime
from prep_data import extract_data
import pandas as pd
import json
from trading_cost import quoted_spread, pick_random_day
import numpy as np
import itertools

rng = np.random.default_rng(1)


def compute_return(returns):
    """
    Computes compound return given list of simple returns
    """
    final_return = 1
    for r in returns:
        final_return *= 1 + r

    return final_return - 1


def get_half_year_daily_returns(returns):
    return list(itertools.chain(*returns[-6:]))


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
            daily_returns=("DlyRet", lambda ret: ret.tolist()),
        )
        .groupby(["PERMNO"])
        .agg(
            returns=("returns", compute_return),
            avg_quoted_spread=("day_quoted_spread", "mean"),
            daily_returns=("daily_returns", get_half_year_daily_returns),
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
    Adjusts initial momentum sort with trading costs
    """

    long_split, short_split = find_momentum_split(data)

    new_long_split = pd.DataFrame(
        {
            "returns": long_split["returns"]
            - cost_sensitivity * long_split["avg_quoted_spread"]
        }
    )
    new_long_split["daily_returns"] = long_split["daily_returns"]

    new_short_split = pd.DataFrame(
        {
            "returns": short_split["returns"]
            - cost_sensitivity * short_split["avg_quoted_spread"]
        }
    )
    new_short_split["daily_returns"] = short_split["daily_returns"]

    return (
        dict(
            new_long_split.nlargest(int(len(long_split) * keep_long), "returns")[
                ["returns", "daily_returns"]
            ].to_dict(orient="index")
        ),
        dict(
            new_short_split.nsmallest(int(len(short_split) * keep_short), "returns")[
                ["returns", "daily_returns"]
            ].to_dict(orient="index")
        ),
    )


def find_splits_per_date(data):
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
            ]
        )

        splits[str(date.to_pydatetime().date())] = {
            "long_split": long_split,
            "short_split": short_split,
        }

    return splits


def main():
    with open("final_split.json", "w") as file:
        json.dump(find_splits_per_date(extract_data("2019-2024 v2.csv")), file)


if __name__ == "__main__":
    main()
