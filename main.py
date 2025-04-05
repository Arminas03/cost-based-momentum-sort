from portfolio_return import get_equal_and_value_portfolios_return_per_month
import pandas as pd


def main():
    model_names = {
        (False, False): "standard",
        (True, True): "hedged_rv",
        (True, False): "hedged_garch",
    }

    for hedged, sigma_model_rv in model_names:
        returns_equal, returns_value = get_equal_and_value_portfolios_return_per_month(
            hedged=hedged, sigma_model_rv=sigma_model_rv
        )

        pd.DataFrame.from_dict(returns_equal, orient="index").rename_axis(
            ["year", "month"]
        ).to_csv(f"ret_cost_{model_names[(hedged, sigma_model_rv)]}_equal.csv")
        pd.DataFrame.from_dict(returns_value, orient="index").rename_axis(
            ["year", "month"]
        ).to_csv(f"ret_cost_{model_names[(hedged, sigma_model_rv)]}_value.csv")

        print(f"Finished {model_names[(hedged, sigma_model_rv)]}")


if __name__ == "__main__":
    main()
