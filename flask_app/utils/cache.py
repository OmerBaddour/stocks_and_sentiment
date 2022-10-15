import pandas as pd
from textblob import TextBlob

from .reddit import predict_reddit_score, pull_reddit_posts
from .twitter import predict_twitter_score, pull_twitter_posts


def add_to_cache_init(ticker, cache):
    """
    Add API-intensive information to cache for the input ticker and stock_name.
    Use this modified version of add_to_cache() for login, to save time.
    Note: only use after validating the Ticker with utils.finance.check_ticker_is_valid()
    """

    # avoid circular import
    from .finance import pull_stock_price_history

    cache[ticker] = ("not done", pull_stock_price_history(ticker))


def add_to_cache(
    stock_name,
    ticker,
    cache,
    reddit_client_id,
    reddit_client_secret,
    reddit_user_agent,
    twitter_bearer_token,
):
    """
    Add API-intensive information to cache for the input ticker and stock_name.
    Note: only use after validating the Ticker with check_ticker_is_valid()
    """

    # avoid circular import
    from .finance import pull_stock_price_history

    if ticker not in cache or cache[ticker][0] == "not done":
        # pull Reddit posts and Tweets
        df_reddit_posts = pull_reddit_posts(
            stock_name,
            reddit_client_id,
            reddit_client_secret,
            reddit_user_agent,
        )
        df_twitter_posts = pull_twitter_posts(stock_name, twitter_bearer_token)

        # predict future scores
        df_reddit_posts["predicted_score"] = df_reddit_posts["text"].apply(
            lambda x: predict_reddit_score(x)
        )
        df_twitter_posts["predicted_score"] = df_twitter_posts["text"].apply(
            lambda x: predict_twitter_score(x)
        )

        # store in combined DataFrame
        df_reddit_and_twitter_posts = pd.concat([df_reddit_posts, df_twitter_posts])

        # calculate sentiment scores
        df_reddit_and_twitter_posts["sentiment_score"] = df_reddit_and_twitter_posts[
            "text"
        ].apply(lambda x: TextBlob(x).sentiment.polarity)

        # calculate total predicted unexpressed sentiment
        total_predicted_unexpressed_sentiment = 0
        for _, r in df_reddit_and_twitter_posts.iterrows():
            total_predicted_unexpressed_sentiment += (
                max(0, r["predicted_score"] - r["score"]) * r["sentiment_score"]
            )

        # if not already pulled last month's price data
        if ticker not in cache:
            # pull last month's price data
            df_stock_price_history = pull_stock_price_history(ticker)
            # add to cache
            cache[ticker] = (
                total_predicted_unexpressed_sentiment,
                df_stock_price_history,
            )
        else:
            # add sentiment to cache, and re-use already pulled price data
            cache[ticker] = (total_predicted_unexpressed_sentiment, cache[ticker][1])


def add_all_to_cache(
    current_portfolio,
    cache,
    reddit_client_id,
    reddit_client_secret,
    reddit_user_agent,
    twitter_bearer_token,
):
    """
    Try adding all stocks in the input portfolio to cache.
    """

    for stock_name, ticker, _quantity in current_portfolio:
        add_to_cache(
            stock_name,
            ticker,
            cache,
            reddit_client_id,
            reddit_client_secret,
            reddit_user_agent,
            twitter_bearer_token,
        )

    return None


def generate_cache_with_predictions(cache):
    """
    Returns a new cache to have 7 day price predictions for each stock in the input cache.
    """

    # mitigate circular import
    from .finance import predict_stock_next_week

    cache_with_predictions = dict()

    for ticker, entry in cache.items():
        entry = list(entry)
        cache_with_predictions[ticker] = (
            entry[0],
            predict_stock_next_week(ticker, cache),
        )

    return cache_with_predictions
