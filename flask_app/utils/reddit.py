import pickle

import pandas as pd
import praw

from .nlp import process_text, vectorize_processed_text

# fetch our pre-trained models and ID to word mappings from memory
reddit_model = pickle.load(open("../models/reddit_logistic_regression.sav", "rb"))
reddit_id_to_word = pickle.load(open("../models/reddit_id_to_word.sav", "rb"))


def pull_reddit_posts(stock_name, client_id, client_secret, user_agent):
    """
    Return a DataFrame of recent Reddit posts relevant to the inputted stock.
    """

    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

    subreddits = [
        reddit.subreddit("Trading"),
        reddit.subreddit("investing"),
        reddit.subreddit("stocks"),
    ]
    subreddits_for_coi = reddit.subreddits.search_by_name(stock_name)
    if subreddits_for_coi:
        subreddits.extend(subreddits_for_coi[: min(len(subreddits_for_coi), 3)])

    posts = []

    for subreddit in subreddits:
        for submission in subreddit.hot(limit=10):
            text = submission.title + "\n" + submission.selftext
            if stock_name in text:
                posts.append((submission.id, text, submission.score))

    return pd.DataFrame(columns=["id", "text", "score"], data=posts)


def predict_reddit_score(reddit_text):
    """
    Returns an integer which is the predicted future score of the post after the
    majority of people who will see and react to the post have done so.
    """

    processed_text = process_text(reddit_text)
    vectorized_processed_text = vectorize_processed_text(
        processed_text, reddit_id_to_word
    )
    return reddit_model.predict(vectorized_processed_text.reshape(1, -1))[
        0
    ]  # have to reshape since single entry
