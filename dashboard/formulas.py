import math
from typing import List


def sharpe_std(returns: List[int | float]) -> float | str:
    """
    Calculates the standard deviation for the returns in the dataset.
    Takes both positive and negative data points into account (as per Sharpe ratio method).
    """
    try:
        mean = sum(returns) / len(returns)
        deviations = [float(num) - mean for num in returns]
        deviations_square = [num ** 2 for num in deviations]
        average_deviation = sum(deviations_square) / len(deviations_square)
        return float(math.sqrt(average_deviation))
    except ZeroDivisionError:
        return 0
    except TypeError:
        raise TypeError("Must all be valid numbers, no words allowed")


def sharpe_ratio(portfolio_return: int | float, periodic_returns=List[int | float], risk_free_return: int | float=5.18) -> int | float:
    """
    Calculates the Sharpe ratio, which measures the excess return per unit of risk.
    Fixed bond rate of 4.0 is used as the risk-free return.
    """
    try:
        return (portfolio_return - (risk_free_return * len(periodic_returns))) / sharpe_std(periodic_returns)
    except ZeroDivisionError:
        return 0


def sortino_std(periodic_returns=List[int | float], risk_free_return=int | float) -> int | float:
    """
    Calculates the Sortino standard deviation, considering only negative deviations (downside risk).
    Fixed bond rate of 4.0 is used as the risk-free return.
    """
    try:
        avg_risk_free_return = risk_free_return / len(periodic_returns)
        negative_deviations = [(num - avg_risk_free_return) for num in periodic_returns if (num - avg_risk_free_return) < 0]
        squared_negatives = [num ** 2 for num in negative_deviations]
        return math.sqrt(sum(squared_negatives) / len(squared_negatives))
    except ZeroDivisionError:
        return 0
    except TypeError:
        raise TypeError("Can't have non-numeric characters")


def sortino_ratio(portfolio_return, periodic_returns, risk_free_return=5.18) -> int | float:
    """
    Calculates the Sortino Ratio, which measures the risk-adjusted return considering only downside risk.
    Fixed bond rate of 4.0 is used as the risk-free return.
    """
    try:
        return (portfolio_return - (risk_free_return * len(periodic_returns))) / sortino_std(periodic_returns, risk_free_return)
    except ZeroDivisionError:
        return 0


def beta(portfolio_periodic_return, benchmark_return=None, benchmark_periodic_return=5.18) -> int | float:
    """
    Calculates the Beta of a portfolio relative to a benchmark.
    Beta is a measure of the portfolio's sensitivity to market movements.
    """
    try:
        if not benchmark_return:
            benchmark_return = [benchmark_periodic_return] * len(portfolio_periodic_return)

        portfolio_avg = sum(portfolio_periodic_return) / len(portfolio_periodic_return)
        benchmark_avg = benchmark_return / len(portfolio_periodic_return)

        portfolio_variances = [(item - portfolio_avg) for item in portfolio_periodic_return]

        if benchmark_periodic_return is None:
            benchmark_periodic_return = [benchmark_return] * len(portfolio_periodic_return)

        benchmark_variances = [(item - benchmark_avg) for item in benchmark_periodic_return]

        if len(portfolio_variances) != len(benchmark_variances):
            raise ValueError("The lengths of portfolio and benchmark variances must be the same.")

        period = len(portfolio_variances)
        covariance_list = []
        for i in range(0, len(portfolio_variances)):
            covariance_list.append(portfolio_variances[i] * benchmark_variances[i])

        variance_list = [item ** 2 for item in benchmark_variances]

        covariance = sum(covariance_list) / period
        variance = sum(variance_list) / period

        return covariance / variance
    except ZeroDivisionError:
        return 0
