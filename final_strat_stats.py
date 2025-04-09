import pandas as pd
from collections import defaultdict
import json


STRATEGY_COMPOSITIONS = [
    (strat, weight)
    for strat in ["standard", "hedged_rv", "hedged_garch"]
    for weight in ["equal", "value"]
]


def evaluate_strategy_performance(lbda, strategy, weight):
    final_return, final_cost = 0, 0

    for start_year, end_year in [(1969, 1985), (1985, 2005), (2005, 2024)]:
        strategy_results = pd.read_csv(
            f"lambda_{lbda}_res/ret_cost_{strategy}_{weight}_{start_year}_{end_year}.csv"
        )

        if strategy_results.iloc[-1]["year"] > end_year:
            strategy_results = strategy_results.iloc[:-1]

        final_return += strategy_results["total_return"].sum()
        final_cost += strategy_results["total_cost"].sum()

    return final_return, final_cost


def main():
    strategy_agg_results = defaultdict(lambda: defaultdict(dict))
    for lbda in [0, 1, 6, 12]:
        for strategy, weight in STRATEGY_COMPOSITIONS:
            strat_return, strat_cost = evaluate_strategy_performance(
                lbda, strategy, weight
            )
            strategy_agg_results[lbda][strategy][weight] = {
                "return": strat_return,
                "cost": strat_cost,
            }

    with open("strategy_performances.json", "w") as file:
        json.dump(strategy_agg_results, file)


if __name__ == "__main__":
    main()
