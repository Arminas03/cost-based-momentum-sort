from datetime import datetime
from utils import extract_data, compute_compound_return
import pandas as pd
import json
import numpy as np
import itertools

rng = np.random.default_rng(1)


def pick_random_day(group: pd.DataFrame, rng):
    """
    Picks random day from 15th until the end of the month
    """
    return group[-15:].sample(n=1, random_state=rng)


def get_half_year_daily_returns(returns):
    """
    Returns a list of daily returns for the last six months
    """
    return list(itertools.chain(*returns[-6:]))


def get_stock_returns(stock_data: pd.DataFrame):
    """
    Gets cumulative stock returns for each permno together with a list
    of daily returns
    """
    return (
        stock_data.groupby(["PERMNO", "month"])[["DlyRet", "quoted_spread", "DlyCap"]]
        .agg(
            cumulative_return=("DlyRet", compute_compound_return),
            day_quoted_spread=(
                "quoted_spread",
                lambda group: pick_random_day(group, rng),
            ),
            daily_returns=("DlyRet", lambda ret: ret.tolist()),
            avg_market_cap=("DlyCap", "mean"),
        )
        .groupby(["PERMNO"])
        .agg(
            cumulative_return=("cumulative_return", compute_compound_return),
            avg_quoted_spread=("day_quoted_spread", "mean"),
            daily_returns=("daily_returns", get_half_year_daily_returns),
            avg_market_cap=("avg_market_cap", "mean"),
        )
    )


def find_momentum_split(
    stock_data: pd.DataFrame, long_split_proportion=0.2, short_split_proportion=0.2
):
    """
    Finds standard momentum strategy long and short legs
    """
    stock_returns = get_stock_returns(stock_data)

    return (
        stock_returns.nlargest(
            int(len(stock_returns) * long_split_proportion), "cumulative_return"
        ),
        stock_returns.nsmallest(
            int(len(stock_returns) * short_split_proportion), "cumulative_return"
        ),
    )


def adjust_momentum_with_costs(long_split, short_split, cost_sensitivity):
    """
    Calculates cost-adjusted returns for each split
    """
    new_long_split = pd.DataFrame(
        {
            "cost_adjusted_return": long_split["cumulative_return"]
            - cost_sensitivity * long_split["avg_quoted_spread"]
        }
    )
    new_long_split["daily_returns"] = long_split["daily_returns"]
    new_long_split["avg_market_cap"] = long_split["avg_market_cap"]

    new_short_split = pd.DataFrame(
        {
            "cost_adjusted_return": short_split["cumulative_return"]
            + cost_sensitivity * short_split["avg_quoted_spread"]
        }
    )
    new_short_split["daily_returns"] = short_split["daily_returns"]
    new_short_split["avg_market_cap"] = short_split["avg_market_cap"]

    return new_long_split, new_short_split


def get_final_splits(data, cost_sensitivity=1, keep_long=0.5, keep_short=0.5):
    """
    Gets final long and short legs based on trading costs
    and input parameters
    """
    new_long_split, new_short_split = adjust_momentum_with_costs(
        *find_momentum_split(data), cost_sensitivity
    )

    return (
        dict(
            new_long_split.nlargest(
                int(len(new_long_split) * keep_long), "cost_adjusted_return"
            )[["cost_adjusted_return", "daily_returns", "avg_market_cap"]].to_dict(
                orient="index"
            )
        ),
        dict(
            new_short_split.nsmallest(
                int(len(new_short_split) * keep_short), "cost_adjusted_return"
            )[["cost_adjusted_return", "daily_returns", "avg_market_cap"]].to_dict(
                orient="index"
            )
        ),
    )


def find_splits_per_date(data, start_year=2019, end_year=2024):
    """
    Finds the two-stage sorting long and short legs
    """
    splits = dict()

    for date in pd.date_range(
        start=datetime(start_year, 12, 31), end=datetime(end_year, 12, 31), freq="ME"
    ):
        print(date)
        long_split, short_split = get_final_splits(
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


def get_two_stage_momentum_splits():
    """
    Returns and extracts to a json file final long and short splits
    for each date of the given period
    """
    with open("final_split.json", "w") as file:
        json.dump(find_splits_per_date(extract_data("2019-2024 v2.csv"), 2019), file)

    return find_splits_per_date(extract_data("2019-2024 v2.csv"), 2019)


if __name__ == "__main__":
    get_two_stage_momentum_splits()
