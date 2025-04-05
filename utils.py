import pandas as pd


def compute_compound_return(returns):
    """
    Computes compound return given list of simple returns
    """
    final_return = 1
    for r in returns:
        final_return *= 1 + r

    return final_return - 1


def clean_data(data: pd.DataFrame):
    """
    Removes irrelevant or non-informative observations
    """
    data = data.dropna()
    data = data[data["PrimaryExch"] == "N"]
    data = data[~data["DlyRet"].apply(lambda x: isinstance(x, str))]

    return data


def adjust_data_cols(data: pd.DataFrame):
    """
    Adjusts data columns for easier use
    """
    data["DlyCalDt"] = pd.to_datetime(data["DlyCalDt"])
    data["year"] = data["DlyCalDt"].dt.year
    data["month"] = data["DlyCalDt"].dt.month
    data["quoted_spread"] = (
        2 * (data["DlyAsk"] - data["DlyBid"]) / (data["DlyAsk"] + data["DlyBid"])
    )
    data["DlyRet"] = data["DlyRet"].astype("float")


def extract_data(path):
    """
    Reads and prepares data
    """
    data_cleaned = clean_data(pd.read_csv(path))
    adjust_data_cols(data_cleaned)

    return data_cleaned


def main():
    df = extract_data("2019-2024 v2.csv")


if __name__ == "__main__":
    main()
