import json
from prep_data import extract_data
import pandas as pd
from two_stage_momentum import compute_return


def find_returns_per_mo_stock(data: pd.DataFrame):
    return (
        data.groupby(["year", "month", "PERMNO"])[["DlyRet"]]
        .agg(cumulative_return=("DlyRet", compute_return))
        .to_dict(orient="index")
    )


def value_weights(two_stage_output_for_date):
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
            permno: val["avg_market_cap"] / sum_long_caps
            for permno, val in two_stage_output_for_date["long_split"].items()
        },
        {
            permno: -val["avg_market_cap"] / sum_short_caps
            for permno, val in two_stage_output_for_date["short_split"].items()
        },
    )


def equal_weights(two_stage_output_for_date):
    len_long_stocks = len(two_stage_output_for_date["long_split"].keys())
    len_short_stocks = len(two_stage_output_for_date["short_split"].keys())

    return (
        {
            permno: 1 / len_long_stocks
            for permno, _ in two_stage_output_for_date["long_split"].items()
        },
        {
            permno: -1 / len_short_stocks
            for permno, _ in two_stage_output_for_date["short_split"].items()
        },
    )


def compute_return_for_split(split, cum_returns_per_month, year, month, weights):
    total_balance = 0

    for permno, _ in split.items():
        # TODO: fix skipping delisted stocks
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
    # 150 is a strong upper bound on the trading days in a 6-month period
    ret_per_day = [0] * 150

    for permno, val in two_stage_date_dict["long_split"].items():
        for j in range(len(val["daily_returns"])):
            ret_per_day[j] += long_weights[permno] * val["daily_returns"][j]

    for permno, val in two_stage_date_dict["short_split"].items():
        for j in range(len(val["daily_returns"])):
            ret_per_day[j] -= short_weights[permno] * val["daily_returns"][j]

    return sum([ret**2 for ret in ret_per_day])


def compute_portfolio_returns(weight_function, two_stage_output, cum_returns_per_month):
    portfolio_return_per_month = dict()

    for date, _ in two_stage_output.items():
        two_stage_date_dict = two_stage_output[date]
        long_weights, short_weights = weight_function(two_stage_date_dict)

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


def main():
    two_stage_output = dict()
    cum_returns_per_month = find_returns_per_mo_stock(extract_data("2019-2024 v2.csv"))

    with open("final_split.json") as json_file:
        two_stage_output = json.load(json_file)

    portfolio_return_per_month_equal = compute_portfolio_returns(
        equal_weights, two_stage_output, cum_returns_per_month
    )
    portfolio_return_per_month_value = compute_portfolio_returns(
        value_weights, two_stage_output, cum_returns_per_month
    )

    print(portfolio_return_per_month_equal)


if __name__ == "__main__":
    main()
