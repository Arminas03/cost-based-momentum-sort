from portfolio_return import get_equal_and_value_portfolios_return_per_month
from two_stage_momentum import get_two_stage_momentum_splits
from final_strat_stats import get_final_strategy_stats
import pandas as pd


def run_two_stage_momentum_sorting():
    """
    Runs the two-stage momentum sort
    """
    for cost_sensitivity in [0, 1, 6, 12]:
        print(f"running cost sensitivity equal to {cost_sensitivity}")
        for split in [(1993, 2005), (2005, 2024)]:
            get_two_stage_momentum_splits(*split, cost_sensitivity=cost_sensitivity)


def create_csvs(
    model_names,
    hedged,
    sigma_model_rv,
    returns_equal,
    returns_value,
    start_year,
    end_year,
    cost_sensitivity,
):
    pd.DataFrame.from_dict(returns_equal, orient="index").rename_axis(
        ["year", "month"]
    ).to_csv(
        f"ret_cost_{model_names[(hedged, sigma_model_rv)]}_equal_{start_year}_{end_year}_lambda_{cost_sensitivity}.csv"
    )
    pd.DataFrame.from_dict(returns_value, orient="index").rename_axis(
        ["year", "month"]
    ).to_csv(
        f"ret_cost_{model_names[(hedged, sigma_model_rv)]}_value_{start_year}_{end_year}_lambda_{cost_sensitivity}.csv"
    )

    print(
        f"Finished {model_names[(hedged, sigma_model_rv)]} for lambda = {cost_sensitivity}"
    )


def run_portfolio_return():
    """
    Runs portfolio return for each strategy
    """
    model_names = {
        (False, False): "standard",
        (True, True): "hedged_rv",
        (True, False): "hedged_garch",
    }
    for cost_sensitivity in [0, 1, 6, 12]:
        print(f"running cost sensitivity equal to {cost_sensitivity}")
        for start_year, end_year in [(1993, 2005), (2005, 2024)]:
            for hedged, sigma_model_rv in model_names:
                args = {
                    "start_year": start_year,
                    "end_year": end_year,
                    "hedged": hedged,
                    "sigma_model_rv": sigma_model_rv,
                    "cost_sensitivity": cost_sensitivity,
                }
                returns_equal, returns_value = (
                    get_equal_and_value_portfolios_return_per_month(**args)
                )

                create_csvs(
                    **args,
                    model_names=model_names,
                    returns_equal=returns_equal,
                    returns_value=returns_value,
                )


def main() -> None:
    print("running two-stage momentum sorting...")
    run_two_stage_momentum_sorting()
    print("finished running two-stage momentum sorting")

    print("running portfolio return...")
    run_portfolio_return()
    print("finished running portfolio return")

    print("running final strategy statistics...")
    get_final_strategy_stats()
    print("finished running final strategy statistics")


if __name__ == "__main__":
    main()
