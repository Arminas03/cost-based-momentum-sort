from utils import extract_data
import pandas as pd
import matplotlib.pyplot as plt


def get_avg_quoted_bid_asks(data_file: str) -> pd.Series:
    data = extract_data(data_file)

    return data.groupby(["year", "month"])[["quoted_spread"]].agg(
        quoted_spread=("quoted_spread", "mean")
    )["quoted_spread"]


def plot_quoted_spread_series(
    quoted_spread_series: pd.Series,
    plot_title: str,
    plot_x_label: str,
    plot_y_label: str,
) -> None:
    plt.figure(figsize=(12, 8))

    plt.plot(
        quoted_spread_series.index,
        quoted_spread_series.values,
        marker="o",
        color="b",
    )
    plt.title(plot_title)
    plt.xlabel(plot_x_label)
    plt.ylabel(plot_y_label)

    plt.show()


def get_quoted_bid_ask_spread_analysis() -> None:
    avg_quoted_bid_asks: pd.Series = pd.concat(
        [
            get_avg_quoted_bid_asks("1993-2005 v2.csv"),
            get_avg_quoted_bid_asks("2005-2024 v2.csv"),
        ]
    )

    avg_quoted_bid_asks = avg_quoted_bid_asks[
        ~avg_quoted_bid_asks.index.duplicated(keep="last")
    ]
    avg_quoted_bid_asks.index = pd.to_datetime(
        [f"{year}-{month:02d}" for year, month in avg_quoted_bid_asks.index]
    )

    plot_quoted_spread_series(
        avg_quoted_bid_asks,
        "Quoted bid-ask spread progression",
        "Year",
        "Average quoted bid-ask spread across all stocks",
    )


def main():
    get_quoted_bid_ask_spread_analysis()


if __name__ == "__main__":
    main()
