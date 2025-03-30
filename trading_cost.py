import pandas as pd


def pick_random_day(group, rng):
    """
    Picks random day
    """
    return group[-15:].sample(n=1, random_state=rng)


def calculate_avg_spread_1y(data_one_day):
    """
    Trading cost function that returns 12 month average trading cost for each stock at time t
    """
    return (data_one_day["ASK"] - data_one_day["BID"]) / (
        (data_one_day["ASK"] + data_one_day["BID"]) / 2
    ).mean()


# def quoted_spread(data: pd.DataFrame, permno):
#     """
#     Finds quoted bid ask spread
#     """
#     # TODO: fix randomness in pick_random_day
#     return calculate_avg_spread_1y(
#         data[(data["date"].dt.day.between(15, 31)) & (data["PERMNO"] == permno)].apply(
#             pick_random_day
#         )
#     )


def quoted_spread(quoted_spread):
    return 0.1


def main():
    pass
    # stock_id = 10026
    # time_t = "2021-12-31"
    # avg_spread = calculate_avg_spread_1y(data_one_day, stock, time)
    # print(
    #     f"1-year average quoted spread for stock {stock_id} at time {time_t}: {avg_spread:.6f}"
    # )


if __name__ == "__main__":
    main()
