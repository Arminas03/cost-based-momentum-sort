from datetime import datetime, timedelta
from prep_data import extract_data
import pandas as pd
import json
from trading_cost import quoted_spread


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
        stock_data.groupby(["PERMNO"])["RET"].apply(compute_return).sort_values()
    )

    return (
        stock_returns[-int(len(stock_returns) * long_split_proportion) :],
        stock_returns[: int(len(stock_returns) * short_split_proportion)],
    )


def adjust_momentum_with_costs(
    data, date, cost_sensitivity=1, keep_long=0.5, keep_short=0.5
):
    """
    Adjusts initial momentum sort with trading costs, resorts
    """
    data_curr = data[
        (data["date"] <= date) & (data["date"] > date - pd.DateOffset(years=1))
    ]

    long_split, short_split = find_momentum_split(data_curr)

    for permno, _ in long_split.items():
        long_split.loc[permno] -= cost_sensitivity * quoted_spread(data_curr, permno)
    for permno, _ in short_split.items():
        short_split.loc[permno] += cost_sensitivity * quoted_spread(data_curr, permno)

    return (
        dict(long_split.sort_values()[-int(len(long_split) * keep_long) :]),
        dict(short_split.sort_values()[: int(len(short_split) * keep_short)]),
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
        long_split, short_split = adjust_momentum_with_costs(data, date)
        splits[str(date.to_pydatetime().date())] = {
            "long_split": list(long_split.keys()),
            "short_split": list(short_split.keys()),
        }

    return splits


def main():
    with open("final_split.json", "w") as file:
        json.dump(find_splits_per_date(extract_data("2019-2024_data.csv")), file)


if __name__ == "__main__":
    main()
