from arch import arch_model
import pandas as pd
import numpy as np


def sigma_hat_rv(sum_sq_ret):
    return np.sqrt(sum_sq_ret * 21 / 126)


def sigma_hat_garch(daily_returns: list):
    model = arch_model(
        daily_returns[-500:],
        mean="Zero",
        vol="Garch",
        p=1,
        q=1,
        dist="normal",
        rescale=False,
    )
    fitted_model = model.fit(disp="off")

    forecast = fitted_model.forecast(horizon=1)
    next_period_var = forecast.variance.iloc[-1, 0]
    next_period_vol = np.sqrt(next_period_var) * np.sqrt(21)

    return next_period_vol
