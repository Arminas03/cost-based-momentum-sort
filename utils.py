import pandas as pd
from typing import Union


HEDGING = ["standard", "hedged_rv", "hedged_garch"]
WEIGHTINGS = ["equal", "value"]
LAMBDAS = ["0", "1", "6", "12"]


def compute_compound_return(returns: Union[list, pd.Series]) -> float:
    """
    Computes compound return given list of simple returns
    """
    final_return = 1
    for r in returns:
        final_return *= 1 + r

    return final_return - 1


def clean_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Removes irrelevant or non-informative observations
    """
    data = data.dropna()
    data = data[
        (data["ShareType"] == "NS")
        & (data["SecurityType"] == "EQTY")
        & (data["SecuritySubType"] == "COM")
        & (data["USIncFlg"] == "Y")
        & (data["IssuerType"].isin(["ACOR", "CORP"]))
        & (data["PrimaryExch"].isin(["N", "Q", "A"]))
        & (data["ConditionalType"].isin(["RW", "NW"]))
        & (data["TradingStatusFlg"] == "A")
    ]
    data = data[~data["DlyRet"].apply(lambda x: isinstance(x, str))]

    return data


def adjust_data_cols(data: pd.DataFrame) -> None:
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


def extract_data(path: str) -> pd.DataFrame:
    """
    Reads and prepares data
    """
    data_cleaned = clean_data(pd.read_csv(path))[
        [
            "PERMNO",
            "DlyCalDt",
            "DlyRet",
            "DlyPrc",
            "DlyAsk",
            "DlyBid",
            "DlyCap",
        ]
    ]
    adjust_data_cols(data_cleaned)

    return data_cleaned


if __name__ == "__main__":
    pass
