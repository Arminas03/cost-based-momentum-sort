from post_run_analysis.quoted_bid_ask_analysis import get_quoted_bid_ask_spread_analysis
from post_run_analysis.strategy_performance_analysis import (
    get_strategy_performance_analysis,
)
from post_run_analysis.trading_cost_analysis import run_trading_cost_analysis
from post_run_analysis.volatility_prediction_analysis import (
    run_volatility_prediction_analysis,
)


def main():
    """
    Select the analysis to run
    """
    print("Quoted bid-ask spread analysis")
    get_quoted_bid_ask_spread_analysis()

    print("Strategy performance analysis")
    get_strategy_performance_analysis()

    print("Trading cost analysis")
    run_trading_cost_analysis()

    print("Volatility prediction analysis")
    run_volatility_prediction_analysis()


if __name__ == "__main__":
    main()
