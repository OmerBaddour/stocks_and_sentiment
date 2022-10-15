import datetime

import numpy as np
import pandas as pd
import yfinance as yf

from .cache import add_to_cache


def pull_stock_price_history(ticker):
    """
    Returns DataFrame containing the last 30 days worth of price history for the input stock ticker.
    """

    today = datetime.date.today()
    start = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    return yf.download(ticker, start, end)


def aggregated_portfolio(portfolio, cache):
    """
    Returns a Series containing the price movement of the input portfolio over the past 30 days.
    """

    if len(portfolio) == 0:
        # Series of zeroes
        today = datetime.date.today()
        start = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        end = today.strftime("%Y-%m-%d")

        index = pd.date_range(start=start, end=end)
        return pd.Series(data=[0] * len(index), index=index)
    elif len(portfolio) == 1:
        return (
            cache[portfolio[0][1]][1]["Open"] * portfolio[0][2]
        )  # prices times volume
    else:
        df_combined = (cache[portfolio[0][1]][1][["Open"]] * portfolio[0][2]).join(
            cache[portfolio[1][1]][1][["Open"]] * portfolio[1][2], rsuffix="1"
        )

        for i in range(2, len(portfolio[2:]) + 2):
            df_combined = df_combined.join(
                cache[portfolio[i][1]][1][["Open"]], rsuffix=str(i)
            )

        return df_combined.sum(axis=1)


def check_ticker_is_valid(ticker):
    # TODO: should improve check by ensuring that there is a price history
    # INFO: could be nice to do this in forms.py instead https://wtforms.readthedocs.io/en/2.3.x/validators/#custom-validators
    """
    Takes in ticker symbol, and outputs True/False whether it exists on Yahoo! Finance.
    """

    info = yf.Ticker(ticker).info
    if (
        "regularMarketPrice" in info
        and info["regularMarketPrice"] is None
        and "preMarketPrice" in info
        and info["preMarketPrice"] is None
        and "logo_url" in info
        and info["logo_url"] is None
        or info["logo_url"] == ""
    ):
        return False
    else:
        return True


def check_stock_in_portfolio(portfolio, ticker):
    """
    Takes in a portfolio and ticker, and outputs True/False whether the stock exists in the portfolio.
    """
    for entry in portfolio:
        if entry[1] == ticker:
            return True

    return False


def generate_next_portfolio(
    current_portfolio,
    transacted_stock_name,
    transacted_ticker,
    action,
    transacted_quantity,
    cache,
    reddit_client_id,
    reddit_client_secret,
    reddit_user_agent,
    twitter_bearer_token,
):
    """
    Return the current portfolio after taking into account the already verified transaction.
    If buying a new stock, adds it to cache.
    """

    global next_portfolio

    next_portfolio = []

    if action == "buy":

        change_made = False

        for stock_name, ticker, quantity in current_portfolio:
            if ticker == transacted_ticker:
                next_portfolio.append(
                    (stock_name, ticker, quantity + transacted_quantity)
                )
                change_made = True
            else:
                next_portfolio.append((stock_name, ticker, quantity))

        if not change_made:
            # new stock which is not in portfolio
            next_portfolio.append(
                (transacted_stock_name, transacted_ticker, transacted_quantity)
            )
            add_to_cache(
                transacted_stock_name,
                transacted_ticker,
                cache,
                reddit_client_id,
                reddit_client_secret,
                reddit_user_agent,
                twitter_bearer_token,
            )

        return next_portfolio
    else:
        # sell
        for stock_name, ticker, quantity in current_portfolio:
            if ticker == transacted_ticker:
                if quantity - transacted_quantity > 0:
                    next_portfolio.append(
                        (stock_name, ticker, quantity - transacted_quantity)
                    )
                # NOTE: else: selling >= than you own, which requires no work
            else:
                next_portfolio.append((stock_name, ticker, quantity))

        return next_portfolio


def calculate_risks_of_stocks_in_portfolio(portfolio, cache):
    """
    Returns a list of the risk of each stock in the input portfolio.
    The risk of a stock is defined as the standard deviation of underlying stock price model
    as a percentage of the average price for that stock over the last 30 days
    """

    risks = []

    for entry in portfolio:
        entry_price_history = cache[entry[1]][1]  # cache[ticker][price history]

        high_low_diffs = [
            high - low
            for high, low in zip(
                entry_price_history["High"], entry_price_history["Low"]
            )
        ]
        average_difference_highs_and_lows = sum(high_low_diffs) / len(high_low_diffs)
        average_stock_price = entry_price_history["Open"].mean()
        risks.append(average_difference_highs_and_lows * 100 / average_stock_price)

    return risks


def calculate_portfolio_weights(portfolio, cache):
    """
    Returns a list of the normalized weights of each stock in the input portfolio.
    Raw weight is defined as the last opening price * quantity owned for a stock.
    """

    portfolio_weights = []

    for entry in portfolio:
        entry_price_history = cache[entry[1]][1]  # cache[ticker][price history]

        portfolio_weights.append(entry_price_history.iloc[-1]["Open"] * entry[2])

    # normalize portfolio weights
    sum_portfolio_weights = sum(portfolio_weights)
    if sum_portfolio_weights != 0:
        portfolio_weights = [x / sum_portfolio_weights for x in portfolio_weights]

    return portfolio_weights


def calculate_portfolio_risk(
    portfolio,
    cache,
    reddit_client_id,
    reddit_client_secret,
    reddit_user_agent,
    twitter_bearer_token,
):
    """
    Return the portfolio's risk, which is defined to be the weighted average of the average
    difference in High, Low for the last month, as a percentage of average stock price for the last month.
    Note that portfolio can be any list of tuples of the form (stock_name, ticker, volume)
    """

    # for stock in portfolio whose ticker symbol is not in cache, call add_to_cache()
    for entry in portfolio:
        if entry[1] not in cache:
            add_to_cache(
                entry[0],
                entry[1],
                cache,
                reddit_client_id,
                reddit_client_secret,
                reddit_user_agent,
                twitter_bearer_token,
            )

    # risks = [average difference in High and Low for stock 0 * 100 / average price of stock 0, ...]
    # = [standard deviation of underlying stock price model as a percentage of the average price for stock 0, ...]
    #
    # portfolio_weights = [last opening price * quantity owned for stock 0, ...]
    risks = calculate_risks_of_stocks_in_portfolio(portfolio, cache)
    portfolio_weights = calculate_portfolio_weights(portfolio, cache)

    # compute sum of risk of each stock * weight
    # = portfolio risk
    return sum([risk * weight for risk, weight in zip(risks, portfolio_weights)])


def check_portfolio_risk(portfolio_risk, tolerance_for_risk):
    """
    Return True if the input portfolio's risk is less than the input tolerance for risk, and False otherwise.
    Checks whether portfolio_risk <= 3*tolerance_for_risk
    Which is to say:
        - for a tolerance_for_risk of 1, weighted average standard deviation is less than 3*1% = 3% of portfolio's value
        - for a tolerance_for_risk of 4, weighted average standard deviation is less than 3*4% = 12% of portfolio's value
        - for a tolerance_for_risk of 5, the user is willing to lose all money, so no risk is too high.
    """

    return True if tolerance_for_risk == 5 else portfolio_risk <= 3 * tolerance_for_risk


def predict_stock_next_week(ticker, cache):
    """
    Return a DataFrame containing the price movement of the input stock over the past and future week (predicted).
    """

    aggregate_sentiment, df_stock_prices = cache[ticker]
    df_future_stock_prices = df_stock_prices.copy()

    mean_volume = df_stock_prices["Volume"].mean()
    try:
        sentiment_scaled_by_volume = (
            aggregate_sentiment * 100_000 / mean_volume if mean_volume != 0 else 0
        )
    except:
        # weird bug fix
        sentiment_scaled_by_volume = 0

    # main distribution: normal random variable with
    #     - a mean of the previous Open
    #     - a standard deviation of the average difference between High and Low for each day
    high_low_diffs = [
        high - low for high, low in zip(df_stock_prices["High"], df_stock_prices["Low"])
    ]
    normal_std = sum(high_low_diffs) / len(high_low_diffs)

    # sentiment noise: uniform random variable of sentiment scaled by volume
    uniform_low, uniform_high = (
        (0, sentiment_scaled_by_volume)
        if sentiment_scaled_by_volume > 0
        else (sentiment_scaled_by_volume, 0)
    )

    df_future_stock_prices.drop(
        columns=["High", "Low", "Close", "Adj Close", "Volume"], inplace=True
    )

    for i in range(7):
        previous = df_future_stock_prices.iloc[-1]
        date = pd.to_datetime(
            previous.name + datetime.timedelta(days=1), format="%Y-%m-%d"
        )
        new_row = pd.DataFrame(
            [
                [
                    max(
                        0,
                        np.random.normal(previous["Open"], normal_std)
                        + np.random.uniform(low=uniform_low, high=uniform_high),
                    )
                ]
            ],
            columns=["Open"],
            index=[date],
        )
        df_future_stock_prices = pd.concat(
            [df_future_stock_prices, pd.DataFrame(new_row)], ignore_index=False
        )

    return df_future_stock_prices.iloc[-14:]
