import pandas as pd
import matplotlib.pyplot as plt


def print_cost_statistics(
    costs_df: pd.DataFrame, strategy: str, weighting: str
) -> None:
    print("--------------------------------------------")
    print(f"{strategy}, {weighting}:")
    print(f"Average cost:\n{costs_df.mean()}\nstandard_deviation:\n{costs_df.std()}")


def plot_trading_costs(costs_df: pd.DataFrame, plot_title: str) -> None:
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
    curr_df = costs_df.loc[
        :,
        [col for col in costs_df.columns if col[1] == strategy and col[2] == weighting],
    ]

    curr_df.columns = ["0", "1", "6", "12"]

    plot_trading_costs(curr_df, f"{strategy}, {weighting}")
    print_cost_statistics(curr_df, strategy, weighting)


def construct_df(file_path: str) -> pd.DataFrame:
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


def main():
    costs_per_strategy = construct_df("ret_cost_ts.csv")

    for strat in ["standard", "hedged_rv", "hedged_garch"]:
        for weighting in ["equal", "value"]:
            analyse_costs_for_lambdas(costs_per_strategy, strat, weighting)


if __name__ == "__main__":
    main()
