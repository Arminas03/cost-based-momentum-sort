import pandas as pd
import json
import math
from utils import STRATEGIES, WEIGHTINGS, LAMBDAS
import scipy.stats as stats


def get_test_statistic(
    num_periods: int,
    strategy1_mean: float,
    strategy2_mean: float,
    strategy1_var: float,
    strategy2_var: float,
):
    return (
        math.sqrt(num_periods)
        * (strategy1_mean - strategy2_mean)
        / math.sqrt(strategy1_var + strategy2_var)
    )


def get_test_results(test_statistic: float, significance_level: float = 0.05) -> dict:
    p_value = float(2 * (1 - stats.norm.cdf(test_statistic)))
    return {
        "test_statistic": test_statistic,
        "p-value": p_value,
        "conclusion": "reject" if p_value < significance_level else "not reject",
    }


def combination_analysis(
    strategy_performances: dict, strategy: str, weighting: str
) -> None:
    combination_dict = {
        lbda: strategy_performances[lbda][strategy][weighting] for lbda in LAMBDAS
    }

    for lbda in LAMBDAS[1:]:
        combination_dict[lbda]["monthly_gross_return"]


def outperformance_analysis(strategy_performances: dict):
    for strategy in STRATEGIES:
        for weighting in WEIGHTINGS:
            combination_analysis(strategy_performances, strategy, weighting)


def main():
    with open("strategy_performances.json", "r") as file:
        strategy_performances = json.load(file)
    print(strategy_performances)


if __name__ == "__main__":
    main()
