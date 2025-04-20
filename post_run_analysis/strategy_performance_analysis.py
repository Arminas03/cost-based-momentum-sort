import json
import math
from utils import HEDGING, WEIGHTINGS, LAMBDAS
import scipy.stats as stats


def get_test_statistic(
    strategy1_mean: float,
    strategy2_mean: float,
    strategy1_var: float,
    strategy2_var: float,
    num_periods: int = 360,
) -> float:
    """
    Returns the test statistic for the test of
    significant outperformance
    """
    return (
        math.sqrt(num_periods)
        * (strategy1_mean - strategy2_mean)
        / math.sqrt(strategy1_var + strategy2_var)
    )


def get_test_results(test_statistic: float, significance_level: float = 0.05) -> dict:
    """
    Returns the test result
    """
    p_value = 2 * (1 - stats.norm.cdf(abs(test_statistic)))
    return {
        "test_statistic": test_statistic,
        "p-value": p_value,
        "conclusion": "reject" if p_value < significance_level else "not reject",
    }


def perform_significance_test(
    two_stage_lbda_results: dict, lbda_zero_results: dict, ret_type: str
) -> str:
    """
    Performs significance test (derived in the paper)
    """
    mean_ret_string = f"monthly_{ret_type}_return"
    std_ret_string = f"monthly_{ret_type}_return_std"

    results = get_test_results(
        get_test_statistic(
            two_stage_lbda_results[mean_ret_string],
            lbda_zero_results[mean_ret_string],
            two_stage_lbda_results[std_ret_string] ** 2,
            lbda_zero_results[std_ret_string] ** 2,
        )
    )

    return (
        f"With test-statistic {results["test_statistic"]} "
        + f"and a p-value of {results["p-value"]}, "
        + f"{results["conclusion"]} the null"
    )


def combination_analysis(
    strategy_performances: dict, strategy: str, weighting: str, evaluate_against: str
) -> None:
    """
    Analyses given strategy, weighting combination
    """
    print("=========================================================")
    print(f"{strategy}, {weighting}")
    print("---------------------------------------------")
    combination_dict = {
        lbda: strategy_performances[lbda][strategy][weighting] for lbda in LAMBDAS
    }

    for lbda in LAMBDAS[1:]:
        print("......................................")
        print(f"lambda = {lbda}")
        print("......................................")
        print("Gross:")
        print(
            perform_significance_test(
                combination_dict[lbda], combination_dict[evaluate_against], "gross"
            )
        )
        print("Net:")
        print(
            perform_significance_test(
                combination_dict[lbda], combination_dict[evaluate_against], "net"
            )
        )


def outperformance_analysis(strategy_performances: dict):
    for hedging in HEDGING:
        for weighting in WEIGHTINGS:
            combination_analysis(strategy_performances, hedging, weighting, "0")


def get_strategy_performance_analysis():
    with open("strategy_performances.json", "r") as file:
        outperformance_analysis(json.load(file))


if __name__ == "__main__":
    get_strategy_performance_analysis()
