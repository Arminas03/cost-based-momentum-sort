import pandas as pd
from collections import defaultdict
import json
from utils import compute_compound_return


STRATEGY_COMPOSITIONS = [
    (strat, weight)
    for strat in ["standard", "hedged_rv", "hedged_garch"]
    for weight in ["equal", "value"]
]


def evaluate_strategy_performance(lbda, strategy, weight):
    gross_return_list, net_return_list, cost_list = [], [], []

    for start_year, end_year in [(1969, 1985), (1985, 2005), (2005, 2024)]:
        strategy_results = pd.read_csv(
            f"lambda_{lbda}_res/ret_cost_{strategy}_{weight}_{start_year}_{end_year}.csv"
        )

        if strategy_results.iloc[-1]["year"] > end_year:
            strategy_results = strategy_results.iloc[:-1]

        gross_return_list += list(strategy_results["total_return"])
        net_return_list += list(
            strategy_results["total_return"] - strategy_results["total_cost"]
        )

        cost_list += list(strategy_results["total_cost"])

    print(net_return_list)
    gross_return = compute_compound_return(gross_return_list)
    net_return = compute_compound_return(net_return_list)

    return gross_return, net_return, gross_return_list, cost_list


def main():
    time_series_results = defaultdict()
    strategy_agg_results = defaultdict(lambda: defaultdict(dict))
    for lbda in [0, 1, 6, 12]:
        for strategy, weight in STRATEGY_COMPOSITIONS:
            strat_return, strat_net_return, gross_returns, costs = (
                evaluate_strategy_performance(lbda, strategy, weight)
            )
            strategy_agg_results[lbda][strategy][weight] = {
                "gross_return": strat_return,
                "net_return": strat_net_return,
            }
            time_series_results[(lbda, strategy, weight, "gross_return")] = (
                gross_returns
            )
            time_series_results[(lbda, strategy, weight, "costs")] = costs

    with open("strategy_performances.json", "w") as file:
        json.dump(strategy_agg_results, file)
    pd.DataFrame(time_series_results).to_csv("ret_cost_ts.csv", index=True, header=True)


if __name__ == "__main__":
    main()
