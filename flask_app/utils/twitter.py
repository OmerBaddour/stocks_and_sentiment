import pickle

import pandas as pd
import requests

from .nlp import process_text, vectorize_processed_text

# fetch our pre-trained models and ID to word mappings from memory
twitter_model = pickle.load(open("../models/twitter_logistic_regression.sav", "rb"))
twitter_id_to_word = pickle.load(open("../models/twitter_id_to_word.sav", "rb"))


def score_tweet(retweet_count, quote_count, like_count):
    """
    Return an integer score of a tweet as a function of retweet_count, quote_count, and like_count.
    """
    return int(retweet_count + quote_count + like_count)


def pull_twitter_posts(stock_name, bearer_token):
    """
    Return a DataFrame of recent Twitter Tweets relevant to the inputted stock.
    """

    twitter_search_endpoint = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": "Bearer " + bearer_token}
    parameters = {
        "query": stock_name,
        "tweet.fields": "text,author_id,created_at,public_metrics",
    }

    res = requests.get(twitter_search_endpoint, headers=headers, params=parameters)
    tweets = res.json()
    posts = []

    if "data" in tweets:
        for d in tweets["data"]:
            score = score_tweet(
                d["public_metrics"]["retweet_count"],
                d["public_metrics"]["quote_count"],
                d["public_metrics"]["like_count"],
            )
            posts.append((d["id"], d["text"], score))

    return pd.DataFrame(columns=["id", "text", "score"], data=posts)


def predict_twitter_score(twitter_text):
    """
    Returns an integer which is the predicted future score of the post after the
    majority of people who will see and react to the post have done so.
    """

    processed_text = process_text(twitter_text)
    vectorized_processed_text = vectorize_processed_text(
        processed_text, twitter_id_to_word
    )
    return twitter_model.predict(vectorized_processed_text.reshape(1, -1))[
        0
    ]  # have to reshape since single entry
