import pandas as pd
from utils import compute_compound_return
import json
from utils import extract_data
from two_stage_momentum import get_two_stage_momentum_splits
from garch_rv import *
import math


garch_predictions = dict()
rv_predictions = dict()
daily_returns_list = []


def find_returns_per_mo_stock(data: pd.DataFrame) -> dict:
    """
    Computes compount return for each stock for each month
    """
    return (
        data.groupby(["year", "month", "PERMNO"], sort=False)[["DlyRet"]]
        .agg(cumulative_return=("DlyRet", compute_compound_return))
        .to_dict(orient="index")
    )


def get_value_weights(
    two_stage_output_for_date: dict, scale_factor: float = 1
) -> tuple[dict, dict]:
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


def get_equal_weights(
    two_stage_output_for_date: dict, scale_factor: float = 1
) -> tuple[dict, dict]:
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


def compute_return_for_split(
    split: dict, cum_returns_per_month: dict, year: int, month: int, weights: dict
) -> float:
    """
    compute cumulative return for a given split
    """
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
    two_stage_date_dict: dict,
    cum_returns_per_month: dict,
    year: int,
    month: int,
    long_weights: dict,
    short_weights: dict,
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


def get_total_cost_for_stock(
    permno: str,
    weights: dict,
    prev_weights: dict,
    two_stage_date_dict: dict,
    prev_stock_ret: dict,
) -> float:
    return (
        (
            abs(
                weights[permno] - (prev_weights.get(permno, 0) * (1 + prev_stock_ret))
                if prev_weights
                else weights[permno]
            )
        )
        * two_stage_date_dict[permno]["avg_quoted_spread"]
        / 2
    )


def adjust_for_prev_removed_stocks(
    total_costs: list,
    prev_weights: dict,
    weights: dict,
    cum_returns_per_month: dict,
    prev_quoted_spread: dict,
    year: int,
    month: int,
) -> None:
    for permno, _ in prev_weights.items():
        if permno not in weights.keys():
            total_costs.append(
                abs(
                    prev_weights[permno]
                    * (
                        1
                        + (
                            cum_returns_per_month[(year, month, int(permno))][
                                "cumulative_return"
                            ]
                            if (year, month, int(permno)) in cum_returns_per_month
                            else 0
                        )
                    )
                )
                * prev_quoted_spread[permno]
                / 2
            )


def compute_total_cost_for_date(
    two_stage_date_dict: dict,
    cum_returns_per_month: dict,
    prev_long_quoted_spreads: dict,
    prev_short_quoted_spreads: dict,
    year: int,
    month: int,
    long_weights: dict,
    short_weights: dict,
    prev_long_weights: dict,
    prev_short_weights: dict,
) -> float:
    total_costs = []

    for permno, _ in long_weights.items():
        cumulative_return = (
            cum_returns_per_month[(year, month, int(permno))]["cumulative_return"]
            if (year, month, int(permno)) in cum_returns_per_month
            else 0
        )
        total_costs.append(
            get_total_cost_for_stock(
                permno,
                long_weights,
                prev_long_weights,
                two_stage_date_dict["long_split"],
                cumulative_return,
            )
        )
    for permno, _ in short_weights.items():
        total_costs.append(
            get_total_cost_for_stock(
                permno,
                short_weights,
                prev_short_weights,
                two_stage_date_dict["short_split"],
                cumulative_return,
            )
        )
    if prev_long_weights:
        adjust_for_prev_removed_stocks(
            total_costs,
            prev_long_weights,
            long_weights,
            cum_returns_per_month,
            prev_long_quoted_spreads,
            year,
            month,
        )
    if prev_short_weights:
        adjust_for_prev_removed_stocks(
            total_costs,
            prev_short_weights,
            short_weights,
            cum_returns_per_month,
            prev_short_quoted_spreads,
            year,
            month,
        )

    return sum(total_costs)


def compute_sum_sq_ret(
    two_stage_date_dict: dict, long_weights: dict, short_weights: dict
) -> float:
    """
    Computes sum of squared returns of WML strategy for a half-year period
    """
    # 125 is the typical number of trading days in a 6-month period
    ret_per_day = [0] * 125

    for permno, val in two_stage_date_dict["long_split"].items():
        for j in range(len(val["daily_returns"][-125:])):
            ret_per_day[j] += long_weights[permno] * val["daily_returns"][j]

    for permno, val in two_stage_date_dict["short_split"].items():
        for j in range(len(val["daily_returns"][-125:])):
            ret_per_day[j] -= short_weights[permno] * val["daily_returns"][j]

    return sum([ret**2 for ret in ret_per_day])


def update_daily_returns_list(
    two_stage_date_dict: dict, long_weights: dict, short_weights: dict
) -> None:
    """
    Updates daily ret list
    """
    ret_per_day = [0] * 260
    global daily_returns_list

    for permno, val in two_stage_date_dict["long_split"].items():
        for j in range(len(val["daily_returns"])):
            ret_per_day[j] += long_weights[permno] * val["daily_returns"][j]

    for permno, val in two_stage_date_dict["short_split"].items():
        for j in range(len(val["daily_returns"])):
            ret_per_day[j] -= short_weights[permno] * val["daily_returns"][j]

    while ret_per_day and ret_per_day[-1] == 0:
        ret_per_day.pop()

    daily_returns_list += ret_per_day


def adjust_weights_with_hedging(
    is_weighting_func_equal: bool,
    long_weights: dict,
    short_weights: dict,
    sigma_model_rv: bool,
    two_stage_date_dict: dict,
    date: str,
    sigma_target: float = 0.12 / math.sqrt(12),
) -> tuple[dict, dict]:
    """
    Adjusts weights with hedging
    """
    global daily_returns_list
    update_daily_returns_list(two_stage_date_dict, long_weights, short_weights)
    sigma_hat = (
        sigma_hat_rv(
            compute_sum_sq_ret(two_stage_date_dict, long_weights, short_weights)
        )
        if sigma_model_rv
        else sigma_hat_garch(daily_returns_list)
    )

    if sigma_model_rv:
        rv_predictions[date] = sigma_hat
    else:
        garch_predictions[date] = sigma_hat

    return (
        get_equal_weights(two_stage_date_dict, sigma_target / sigma_hat)
        if is_weighting_func_equal
        else get_value_weights(two_stage_date_dict, sigma_target / sigma_hat)
    )


def get_final_weights_for_date(
    two_stage_date_dict: dict,
    is_weighting_func_equal: bool,
    hedged: bool,
    sigma_model_rv: bool,
    date: str,
) -> tuple[dict, dict]:
    """
    Get final long and short weights for date
    """
    long_weights, short_weights = (
        get_equal_weights(two_stage_date_dict)
        if is_weighting_func_equal
        else get_value_weights(two_stage_date_dict)
    )

    return (
        adjust_weights_with_hedging(
            is_weighting_func_equal,
            long_weights,
            short_weights,
            sigma_model_rv,
            two_stage_date_dict,
            date,
        )
        if hedged
        else (long_weights, short_weights)
    )


def get_prev_quoted_spreads(two_stage_date_dict: dict) -> dict:
    """
    Get previous quoted bid-ask spreds
    """
    return {
        permno: two_stage_date_dict[permno]["avg_quoted_spread"]
        for permno, _ in two_stage_date_dict.items()
    }


def compute_portfolio_returns(
    is_weighting_func_equal: bool,
    two_stage_output: dict,
    cum_returns_per_month: dict,
    hedged: bool = False,
    sigma_model_rv: bool = True,
) -> dict:
    """
    Computes portfolio total monthly returns of WML
    """
    portfolio_return_per_month = dict()
    prev_long_weights, prev_short_weights = None, None
    prev_long_quoted_spreads, prev_short_quoted_spreads = None, None

    for date, _ in two_stage_output.items():
        two_stage_date_dict = two_stage_output[date]

        long_weights, short_weights = get_final_weights_for_date(
            two_stage_date_dict,
            is_weighting_func_equal,
            hedged,
            sigma_model_rv,
            date,
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

        portfolio_return_per_month[(year, month)]["total_cost"] = (
            compute_total_cost_for_date(
                two_stage_date_dict,
                cum_returns_per_month,
                prev_long_quoted_spreads,
                prev_short_quoted_spreads,
                year,
                month,
                long_weights,
                short_weights,
                prev_long_weights,
                prev_short_weights,
            )
        )

        portfolio_return_per_month[(year, month)]["sum_squared_return"] = (
            compute_sum_sq_ret(two_stage_date_dict, long_weights, short_weights)
        )

        prev_long_weights, prev_short_weights = long_weights, short_weights
        prev_long_quoted_spreads = get_prev_quoted_spreads(
            two_stage_date_dict["long_split"]
        )
        prev_short_quoted_spreads = get_prev_quoted_spreads(
            two_stage_date_dict["short_split"]
        )

    with open(
        f"vol_predictions_{"RV" if sigma_model_rv else "GARCH"}.json", "w"
    ) as file:
        json.dump(rv_predictions if sigma_model_rv else garch_predictions, file)
    return portfolio_return_per_month


def get_equal_and_value_portfolios_return_per_month(
    start_year: int = 2019,
    end_year: int = 2024,
    hedged: bool = False,
    sigma_model_rv: bool = True,
    cost_sensitivity: int = 0,
) -> tuple[dict, dict]:
    """
    Returns portfolio returns for equal and value weighted functions
    """
    two_stage_output = dict()
    with open(
        f"final_split_{start_year}_{end_year}_lambda_{cost_sensitivity}.json"
    ) as json_file:
        two_stage_output = json.load(json_file)

    cum_returns_per_month = find_returns_per_mo_stock(
        extract_data(f"{start_year}-{end_year} v2.csv")
    )

    return (
        (
            compute_portfolio_returns(
                True, two_stage_output, cum_returns_per_month, sigma_model_rv
            )
            if not hedged
            else compute_portfolio_returns(
                True, two_stage_output, cum_returns_per_month, True, sigma_model_rv
            )
        ),
        (
            compute_portfolio_returns(
                False, two_stage_output, cum_returns_per_month, sigma_model_rv
            )
            if not hedged
            else compute_portfolio_returns(
                False, two_stage_output, cum_returns_per_month, True, sigma_model_rv
            )
        ),
    )


if __name__ == "__main__":
    model_names = {
        (False, False): "standard",
        (True, True): "hedged_rv",
        (True, False): "hedged_garch",
    }

    for start_year, end_year in [(1993, 2005), (2005, 2024)]:
        for hedged, sigma_model_rv in model_names:
            returns_equal, returns_value = (
                get_equal_and_value_portfolios_return_per_month(
                    start_year=start_year,
                    end_year=end_year,
                    hedged=hedged,
                    sigma_model_rv=sigma_model_rv,
                )
            )
