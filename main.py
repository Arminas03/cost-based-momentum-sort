from portfolio_return import get_equal_and_value_portfolios_return_per_month


def main():
    returns_equal, returns_value = get_equal_and_value_portfolios_return_per_month(
        hedged=True, sigma_model_rv=True
    )

    print(returns_equal)


if __name__ == "__main__":
    main()
