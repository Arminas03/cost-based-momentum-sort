import pandas as pd
from utils import compute_compound_return
import json
from utils import extract_data
from two_stage_momentum import get_two_stage_momentum_splits
from garch_rv import *


def find_returns_per_mo_stock(data: pd.DataFrame):
    """
    Computes compount return for each stock for each month
    """
    return (
        data.groupby(["year", "month", "PERMNO"])[["DlyRet"]]
        .agg(cumulative_return=("DlyRet", compute_compound_return))
        .to_dict(orient="index")
    )


def get_value_weights(two_stage_output_for_date, scale_factor=1):
    """
    Returns weights for standard value-weighted portfolio
    """
    sum_long_caps = sum(
        [
            val["avg_market_cap"]
            for _, val in two_stage_output_for_date["long_split"].items()
        ]
    )
    sum_short_caps = sum(
        [
            val["avg_market_cap"]
            for _, val in two_stage_output_for_date["short_split"].items()
        ]
    )

    return (
        {
            permno: scale_factor * val["avg_market_cap"] / sum_long_caps
            for permno, val in two_stage_output_for_date["long_split"].items()
        },
        {
            permno: -scale_factor * val["avg_market_cap"] / sum_short_caps
            for permno, val in two_stage_output_for_date["short_split"].items()
        },
    )


def get_equal_weights(two_stage_output_for_date, scale_factor=1):
    """
    Returns weights for standard equal-weighted portfolio
    """
    len_long_stocks = len(two_stage_output_for_date["long_split"].keys())
    len_short_stocks = len(two_stage_output_for_date["short_split"].keys())

    return (
        {
            permno: scale_factor / len_long_stocks
            for permno, _ in two_stage_output_for_date["long_split"].items()
        },
        {
            permno: -scale_factor / len_short_stocks
            for permno, _ in two_stage_output_for_date["short_split"].items()
        },
    )


def compute_return_for_split(split, cum_returns_per_month, year, month, weights):
    """
    compute cumulative return for a given split
    """
    # TODO: fix delisted stock returns
    total_balance = 0

    for permno, _ in split.items():
        total_balance += (
            (
                cum_returns_per_month[(year, month, int(permno))]["cumulative_return"]
                * weights[permno]
            )
            if (year, month, int(permno)) in cum_returns_per_month
            else 0
        )

    return total_balance


def compute_total_return_for_date(
    two_stage_date_dict, cum_returns_per_month, year, month, long_weights, short_weights
):
    """
    Computes total return for each split and combines them
    """
    return compute_return_for_split(
        two_stage_date_dict["long_split"],
        cum_returns_per_month,
        year,
        month,
        long_weights,
    ) + compute_return_for_split(
        two_stage_date_dict["short_split"],
        cum_returns_per_month,
        year,
        month,
        short_weights,
    )


def compute_sum_sq_ret(two_stage_date_dict, long_weights, short_weights):
    """
    Computes sum of squared returns of WML strategy for a half-year period
    """
    # 150 is a strong upper bound on the trading days in a 6-month period
    ret_per_day = [0] * 150

    for permno, val in two_stage_date_dict["long_split"].items():
        for j in range(len(val["daily_returns"])):
            ret_per_day[j] += long_weights[permno] * val["daily_returns"][j]

    for permno, val in two_stage_date_dict["short_split"].items():
        for j in range(len(val["daily_returns"])):
            ret_per_day[j] -= short_weights[permno] * val["daily_returns"][j]

    return sum([ret**2 for ret in ret_per_day])


def adjust_weights_with_hedging(
    is_weighing_func_equal,
    long_weights,
    short_weights,
    sigma_model_rv,
    two_stage_date_dict,
    cum_returns_per_month,
    sigma_target=0.12,
):
    sigma_hat = (
        sigma_hat_rv(
            compute_sum_sq_ret(two_stage_date_dict, long_weights, short_weights)
        )
        if sigma_model_rv
        else sigma_hat_garch(cum_returns_per_month)
    )

    return (
        get_equal_weights(two_stage_date_dict, sigma_target / sigma_hat)
        if is_weighing_func_equal
        else get_value_weights(two_stage_date_dict, sigma_target / sigma_hat)
    )


def get_final_weights_for_date(
    two_stage_date_dict,
    cum_returns_per_month,
    is_weighing_func_equal,
    hedged,
    sigma_model,
):
    long_weights, short_weights = (
        get_equal_weights(two_stage_date_dict)
        if is_weighing_func_equal
        else get_value_weights(two_stage_date_dict)
    )

    return (
        adjust_weights_with_hedging(
            is_weighing_func_equal,
            long_weights,
            short_weights,
            sigma_model,
            two_stage_date_dict,
            cum_returns_per_month,
        )
        if hedged
        else (long_weights, short_weights)
    )


def compute_portfolio_returns(
    is_weighing_func_equal,
    two_stage_output,
    cum_returns_per_month,
    hedged=False,
    sigma_model="",
):
    """
    Computes portfolio total monthly returns of WML
    """
    portfolio_return_per_month = dict()

    for date, _ in two_stage_output.items():
        print(date)
        two_stage_date_dict = two_stage_output[date]

        long_weights, short_weights = get_final_weights_for_date(
            two_stage_date_dict,
            cum_returns_per_month,
            is_weighing_func_equal,
            hedged,
            sigma_model,
        )

        year, month, _ = date.split("-")
        year, month = (
            (int(year), int(month) + 1) if int(month) < 12 else (int(year) + 1, 1)
        )

        portfolio_return_per_month[(year, month)] = dict()

        portfolio_return_per_month[(year, month)]["total_return"] = (
            compute_total_return_for_date(
                two_stage_date_dict,
                cum_returns_per_month,
                year,
                month,
                long_weights,
                short_weights,
            )
        )

        portfolio_return_per_month[(year, month)]["sum_squared_return"] = (
            compute_sum_sq_ret(two_stage_date_dict, long_weights, short_weights)
        )

    return portfolio_return_per_month


def get_equal_and_value_portfolios_return_per_month(hedged=False, sigma_model_rv=True):
    """
    Can either take input from get_two_stage_momentum_splits directly, or
    use the json output from two_stage_momentum.py. Returns portfolio returns
    for equal and value weighted functions
    """
    # two_stage_output = get_two_stage_momentum_splits()
    two_stage_output = dict()
    with open("final_split.json") as json_file:
        two_stage_output = json.load(json_file)

    cum_returns_per_month = find_returns_per_mo_stock(extract_data("2019-2024 v2.csv"))

    return (
        (
            compute_portfolio_returns(True, two_stage_output, cum_returns_per_month)
            if not hedged
            else compute_portfolio_returns(
                True, two_stage_output, cum_returns_per_month, True, sigma_model_rv
            )
        ),
        (
            compute_portfolio_returns(False, two_stage_output, cum_returns_per_month)
            if not hedged
            else compute_portfolio_returns(
                False, two_stage_output, cum_returns_per_month, True, sigma_model_rv
            )
        ),
    )


if __name__ == "__main__":
    pass
