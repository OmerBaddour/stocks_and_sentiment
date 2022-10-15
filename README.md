# stocks_and_sentiment

Flask web app that boosts the rationality of its users when buying and selling stocks.

## Project Overview

The overall purpose of this project is to use emotions to aid investing decisions. The project has two key components.

The first component predicts a stock price's movement for the next week. Sentiment analysis is performed on data scraped from Twitter and Reddit about a publicly traded stock of interest, in order to get an idea of how people feel about the stock. This analysis is combined with stock market data (Yahoo! Finance) to generate a prediction of the stock price's short-term movement.

The second component is designed to aid an investor's rationality. Each investor makes an account in our system, which stores their basic personal information, tolerance for risk and current portfolio. Whenever the investor wishes to make a transaction, they must input their reasoning and current mood. Sentiment analysis is done on these inputs to determine whether the investor is in the right emotional headspace to make a sound decision. Furthermore, the investor is presented with graphics of their porfolio's projected movement with and without accounting for the transaction in question (where this projected movement is based on sentiment analysis of relevant Twitter and Reddit data). Lastly, the risk of their portfolio with the transaction is computed, and compared to their tolerance for risk (stored on their profile). All of these analyses are output to the investor to boost their rationality and emotional awareness before they make their final decision.

## Project Details

This notebook serves as a simple proof of concept. It begins with the creation of a user in our database, complete with their risk tolerance and current portfolio. Risk tolerance is an integer between 1 and 5 inclusive, where 1 means "losing this money impacts my living standard", and 5 means "I am happy to lose all of this money". We go through the process of purchasing a stock of interest.

For all stocks in the users portfolio and the stock of interest, we fetch 10 relevant Twitter Tweets. We compute a popularity score for each Tweet by using the number of likes and retweets the Tweet has. We then fetch the top 10 Reddit posts from three investing subreddits, and (at most) three subreddits relevant to each stock. The data is then aggregated into a DataFrame. We compute the sentiment of each post, and the overall sentiment that people have towards the company of interest.

Next, we scrape some statistics about the last month of the company's stock price from Yahoo! Finance, and plot the price movement over this time period. I use these statistics, and the overall sentiment people have towards the company of interest, to generate two distributions that are sampled from and combined to yield projected stock prices for the next week. The base distribution is a normal distribution, that has a mean of the last open stock price, and a standard deviation of the mean difference between the daily highs and lows of the stock over the previous month. The distribution is complemented by a uniform distribution which has at least one bound of 0. The other bound is the overall sentiment people have towards the company of interest scaled by a constant, divided by the average volume of traded stock for the past month. I then plot the last week's price movement, and a generated week of future price movement, by summing the values of the two above distributions.

The best resource for understanding this project is [milestone_notebooks/milestone_2.ipynb](https://github.com/OmerBaddour/stocks_and_sentiment/blob/master/milestone_notebooks/milestone_2.ipynb). It showcases the creation of a new user account, and the completion of one transaction.

## Project Status

The project can be hosted locally according to the below [initialization](#initialization) and [recurring usage](#recurring-usage) instructions. It is not currently hosted live on the Internet.

## Initialization

```
$ git clone https://github.com/OmerBaddour/stocks_and_sentiment.git
$ cd stocks_and_sentiment
$ python -m venv venv_stocks_and_sentiment
$ pip install -r requirements
$ cd flask_app
$ export FLASK_APP=app.py
```

Create a `.env` file with credentials for:

- FLASK_SECRET_KEY
- MYSQL_DATABASE_USER
- MYSQL_DATABASE_PASSWORD
- MYSQL_DATABASE_HOST
- MYSQL_DATABASE_DB
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- REDDIT_USER_AGENT
- TWITTER_BEARER_TOKEN

These credentials correspond to an [AWS MySQL database](https://aws.amazon.com/rds/mysql/), a [Reddit API](https://www.reddit.com/dev/api/) account, and a [Twitter API](https://developer.twitter.com/en/docs/twitter-api) account. You should create your own for each of these services to host the web app locally.

To initialize the database, see `useful_notebooks/mysql_aws_initialization_and_experimentation.ipynb`.

Finally, host the web app on your local machine:

```
$ flask run
```

## Recurring Usage

```
$ cd flask_app
$ export FLASK_APP=app.py
$ flask run
```

## Useful Resources

- [Flask Tutorials](https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH)
