from datetime import datetime
from utils import extract_data, compute_compound_return
import pandas as pd
import json
import numpy as np
import itertools


rng = np.random.default_rng(1)


def pick_random_day(group: pd.Series) -> float:
    """
    Picks random day from 15th until the end of the month
    """
    return group[-15:].sample(n=1, random_state=rng)


def get_year_daily_returns(returns: pd.Series) -> list:
    """
    Returns a list of daily returns for the last year
    """
    return list(itertools.chain(*returns))


def get_stock_returns(stock_data: pd.DataFrame) -> dict:
    """
    Gets cumulative stock returns for each permno together with a list
    of daily returns
    """
    return (
        stock_data.groupby(["PERMNO", "month"], sort=False)[
            ["DlyRet", "quoted_spread", "DlyCap"]
        ]
        .agg(
            cumulative_return=("DlyRet", compute_compound_return),
            day_quoted_spread=(
                "quoted_spread",
                lambda group: pick_random_day(group),
            ),
            daily_returns=("DlyRet", lambda ret: ret.tolist()),
            avg_market_cap=("DlyCap", "mean"),
        )
        .groupby(["PERMNO"], sort=False)
        .agg(
            cumulative_return=("cumulative_return", compute_compound_return),
            avg_quoted_spread=("day_quoted_spread", "mean"),
            daily_returns=("daily_returns", get_year_daily_returns),
            avg_market_cap=("avg_market_cap", "mean"),
        )
    )


def find_momentum_split(
    stock_data: pd.DataFrame,
    long_split_proportion: float = 0.2,
    short_split_proportion: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
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


def adjust_momentum_with_costs(
    long_split: pd.DataFrame, short_split: pd.DataFrame, cost_sensitivity: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
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
    new_long_split["avg_quoted_spread"] = long_split["avg_quoted_spread"]

    new_short_split = pd.DataFrame(
        {
            "cost_adjusted_return": short_split["cumulative_return"]
            + cost_sensitivity * short_split["avg_quoted_spread"]
        }
    )
    new_short_split["daily_returns"] = short_split["daily_returns"]
    new_short_split["avg_market_cap"] = short_split["avg_market_cap"]
    new_short_split["avg_quoted_spread"] = short_split["avg_quoted_spread"]

    return new_long_split, new_short_split


def get_final_splits(
    data: pd.DataFrame,
    cost_sensitivity: int,
    keep_long: float = 0.5,
    keep_short: float = 0.5,
) -> tuple[dict, dict]:
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
            )[
                [
                    "cost_adjusted_return",
                    "daily_returns",
                    "avg_market_cap",
                    "avg_quoted_spread",
                ]
            ].to_dict(
                orient="index"
            )
        ),
        dict(
            new_short_split.nsmallest(
                int(len(new_short_split) * keep_short), "cost_adjusted_return"
            )[
                [
                    "cost_adjusted_return",
                    "daily_returns",
                    "avg_market_cap",
                    "avg_quoted_spread",
                ]
            ].to_dict(
                orient="index"
            )
        ),
    )


def find_splits_per_date(
    data: pd.DataFrame, start_year: int, end_year: int, cost_sensitivity: int
) -> dict:
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
            ],
            cost_sensitivity=cost_sensitivity,
        )

        splits[str(date.to_pydatetime().date())] = {
            "long_split": long_split,
            "short_split": short_split,
        }

    return splits


def get_two_stage_momentum_splits(
    start_year: int = 2019, end_year: int = 2024, cost_sensitivity: int = 0
) -> dict:
    """
    Returns and extracts to a json file final long and short splits
    for each date of the given period
    """
    splits_per_date = find_splits_per_date(
        extract_data(f"{start_year}-{end_year} v2.csv"),
        start_year,
        end_year,
        cost_sensitivity=cost_sensitivity,
    )
    with open(
        f"final_split_{start_year}_{end_year}_lambda_{cost_sensitivity}.json", "w"
    ) as file:
        json.dump(splits_per_date, file)

    return splits_per_date


if __name__ == "__main__":
    for split in [(1993, 2005), (2005, 2024)]:
        get_two_stage_momentum_splits(*split)
