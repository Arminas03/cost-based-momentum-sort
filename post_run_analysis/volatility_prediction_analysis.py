import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt


def get_volatility_predictions(path: str) -> pd.Series:
    """
    Takes volatility predictions from the output files
    """
    with open(path, "r") as file:
        vol_predictions = pd.Series(json.load(file))
        vol_predictions.index = (
            pd.to_datetime(vol_predictions.index).to_period("M").to_timestamp()
        ) + pd.DateOffset(months=1)
        vol_predictions = vol_predictions[
            (~vol_predictions.index.duplicated(keep="first"))
            & (vol_predictions.index < pd.to_datetime("2025-01-01"))
        ]

        return vol_predictions


def get_sample_vol_series(path: str) -> pd.Series:
    """
    Gets data sample volatility
    """
    sum_sq_ret = pd.read_csv(path)[["year", "month", "sum_squared_return"]]
    sum_sq_ret["date"] = pd.to_datetime(
        dict(year=sum_sq_ret["year"], month=sum_sq_ret["month"], day=1)
    )
    sum_sq_ret = sum_sq_ret.set_index("date")

    return np.sqrt(sum_sq_ret["sum_squared_return"]) / np.sqrt(12)


def get_true_volatilities(path_first_sample: str, path_second_sample: str) -> pd.Series:
    """
    Gets true volatilities
    """
    return pd.concat(
        [
            get_sample_vol_series(path_first_sample),
            get_sample_vol_series(path_second_sample),
        ]
    )


def plot_vol_predictions(
    garch_predictions: pd.Series,
    rv_predictions: pd.Series,
    true_volatilities: pd.Series,
) -> None:
    """
    Plots volatility predictions for both models and the true volatilities
    """
    plt.figure(figsize=(12, 8))

    plt.plot(garch_predictions, label="GARCH Predictions", color="orange")
    plt.plot(rv_predictions, label="RV Predictions", color="red")
    plt.plot(true_volatilities, label="True volatilities", color="black")

    plt.xlabel("Date")
    plt.ylabel("Volatility")
    plt.legend()
    plt.tight_layout()
    plt.show()


def get_mse(model_predictions: pd.Series, true_values: pd.Series) -> float:
    """
    Computes MSE
    """
    return ((model_predictions - true_values) ** 2).mean()


def get_mse_analysis(
    garch_predictions: pd.Series, rv_predictions: pd.Series, true_values: pd.Series
) -> None:
    """
    Prints out the MSEs of GARCH and RV predictions
    """
    print(f"GARCH MSE: {get_mse(garch_predictions, true_values)}")
    print(f"RV MSE: {get_mse(rv_predictions, true_values)}")


def run_volatility_prediction_analysis() -> None:
    """
    Runs analysis of GARCH and RV predictions
    """
    garch_predictions = get_volatility_predictions("vol_predictions_GARCH.json")
    rv_predictions = get_volatility_predictions("vol_predictions_RV.json")
    true_rv = get_true_volatilities(
        "ret_cost_standard_value_1993_2005_lambda_0.csv",
        "ret_cost_standard_value_2005_2024_lambda_0.csv",
    )

    plot_vol_predictions(garch_predictions, rv_predictions, true_rv)
    get_mse_analysis(garch_predictions, rv_predictions, true_rv)


if __name__ == "__main__":
    run_volatility_prediction_analysis()
