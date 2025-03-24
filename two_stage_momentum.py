from datetime import datetime
from prep_data import extract_data
import pandas as pd


def compute_return(returns):
    final_return = 1
    for r in returns:
        final_return *= 1 + r

    return final_return - 1


def find_initial_momentum_split(
    stock_data, long_split_proportion=0.2, short_split_proportion=0.2
):
    stock_returns = (
        stock_data[stock_data["date"] < datetime(2020, 1, 1)]
        .groupby(["PERMNO"])["RET"]
        .apply(compute_return)
        .sort_values()
    )

    return (
        stock_returns[-int(len(stock_returns) * long_split_proportion) :],
        stock_returns[: int(len(stock_returns) * short_split_proportion)],
    )


def cost_func(permno):
    # TODO: implement/import
    return 0.1


def adjust_momentum_with_costs(
    long_split: pd.Series,
    short_split: pd.Series,
    cost_sensitivity=1,
    keep_long=0.5,
    keep_short=0.5,
):
    for permno, _ in long_split.items():
        long_split.loc[permno] -= cost_sensitivity * cost_func(permno)
    for permno, _ in short_split.items():
        short_split.loc[permno] += cost_sensitivity * cost_func(permno)

    return (
        long_split.sort_values()[-int(len(long_split) * keep_long) :],
        short_split.sort_values()[: int(len(short_split) * keep_short)],
    )


def main():
    long_split, short_split = adjust_momentum_with_costs(
        *find_initial_momentum_split(extract_data("2019-2024_data.csv"))
    )

    print(long_split)
    print(short_split)


if __name__ == "__main__":
    main()
