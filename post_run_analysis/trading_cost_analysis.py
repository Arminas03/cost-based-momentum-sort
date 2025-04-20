import pandas as pd
import matplotlib.pyplot as plt
from utils import HEDGING, WEIGHTINGS


def print_cost_statistics(
    costs_df: pd.DataFrame, strategy: str, weighting: str
) -> None:
    """
    Prints cost statistics
    """
    print("--------------------------------------------")
    print(f"{strategy}, {weighting}:")
    print(f"Average cost:\n{costs_df.mean()}\nstandard_deviation:\n{costs_df.std()}")


def plot_trading_costs(costs_df: pd.DataFrame, plot_title: str) -> None:
    """
    Plots trading cost series
    """
    plt.figure(figsize=(12, 8))

    plt.plot(costs_df["0"], label="λ = 0", marker="", color="blue")
    plt.plot(costs_df["1"], label="λ = 1", marker="", color="red")
    plt.plot(costs_df["6"], label="λ = 6", marker="", color="black")
    plt.plot(costs_df["12"], label="λ = 12", marker="", color="green")

    plt.xlabel("Date")
    plt.ylabel("Trading costs")
    plt.title(plot_title)
    plt.legend()
    plt.grid()
    plt.show()


def analyse_costs_for_lambdas(
    costs_df: pd.DataFrame, strategy: str, weighting: str
) -> None:
    """
    Analyses costs for different cost-sensitivty parameter configurations
    """
    curr_df = costs_df.loc[
        :,
        [col for col in costs_df.columns if col[1] == strategy and col[2] == weighting],
    ]

    curr_df.columns = ["0", "1", "6", "12"]

    plot_trading_costs(curr_df, f"{strategy}, {weighting}")
    print_cost_statistics(curr_df, strategy, weighting)


def construct_df(file_path: str) -> pd.DataFrame:
    """
    Constructs dataframe suitable for the cost analysis
    """
    df = pd.read_csv(file_path, header=None)

    df = df.loc[:, df.iloc[3] != "gross_return"]

    dates = list(df.iloc[4:, 0])
    df = df.drop(0, axis=1)
    models = [(df[col].iloc[0], df[col].iloc[1], df[col].iloc[2]) for col in df.columns]

    df = df.iloc[4:]
    df.columns = models
    df.index = pd.to_datetime(dates).to_period("M").to_timestamp()
    df = df.astype(float)

    return df


def run_trading_cost_analysis() -> None:
    costs_per_strategy = construct_df("ret_cost_ts.csv")

    for strat in HEDGING:
        for weighting in WEIGHTINGS:
            analyse_costs_for_lambdas(costs_per_strategy, strat, weighting)


if __name__ == "__main__":
    run_trading_cost_analysis()
