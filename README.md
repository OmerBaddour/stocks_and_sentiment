# stocks_and_sentiment

Flask web app that boosts the rationality of its users when buying and selling stocks.

## Project Overview

The overall purpose of this project is to use emotions to aid investing decisions. The project has two key components.

The first component predicts a stock price's movement for the next week. Sentiment analysis is performed on data scraped from Twitter and Reddit about a publicly traded stock of interest, in order to get an idea of how people feel about the stock. This analysis is combined with stock market data (Yahoo! Finance) to generate a prediction of the stock price's short-term movement.

The second component is designed to aid an investor's rationality. Each investor makes an account, which stores their basic personal information, tolerance for risk and current portfolio. Whenever the investor wishes to make a transaction, they must input their reasoning and current mood. Sentiment analysis is done on these inputs to determine whether the investor is in the right emotional headspace to make a sound decision. Furthermore, the investor is presented with graphics of their porfolio's projected movement with and without accounting for the transaction in question (where this projected movement is based on sentiment analysis of relevant Twitter and Reddit data). Lastly, the risk of their portfolio with the transaction is computed, and compared to their tolerance for risk (stored on their profile). All of these analyses are output to the investor to boost their rationality and emotional awareness before they make their final decision.

## Project Details

By walking through a full user journey, we can gain a better understanding of the project details.

#### Account Creation

A user begins by creating an account, which involves all the usual stuff (email, password), as well as their risk tolerance. Risk tolerance is an integer between 1 and 5 inclusive, where 1 means "losing this money impacts my living standard", and 5 means "I am happy to lose all of this money". Signing up results in a record being added to the `USERS` table in the MySQL database.

The user is redirected to the home page, where they'll log in with their credentials.

#### Performing a Transaction

The user will perform a transaction to purchase stock in a company of interest.

In the general case, this entails conducting risk and sentiment analysis on each company in the user's portfolio and the company of interest, so it can be determined whether:

1. The user's portfolio after the transaction will be too risky given their tolerance for risk
2. Sentiment-based price predictions across the user's portfolio can be made

However, in this case of making a first purchase, the user's portfolio is empty, so content is only pulled for the company of interest.

Accordingly, price information for the company of interest is pulled for the past 30 days. The risk of the stock is defined as the average difference between the high and low for each day as a percentage of the average opening price. For example, if the average difference between the high and low over the 30 day period is 10 USD, and the average opening price over the 30 day period is 200 USD, the risk is $\frac{\$10}{\$200} \times 100 = 5$.

If this number is less than the user's risk tolerance multiplied by a constant, the transaction continues. Otherwise it is aborted due to an insufficient risk tolerance. Note that in the case of a non-empty portfolio, a weighted average risk across all positions is used.

Assuming the company of interest has a risk level within the tolerance of the user, sentiment analysis begins with the fetching of 10 relevant Twitter Tweets. A popularity score for each Tweet is computed, as a function of the number of likes and retweets the Tweet has. The current top ([hot](https://www.reddit.com/r/explainlikeimfive/comments/1u0q4s/eli5_difference_between_best_hot_and_top_on_reddit/)) 10 Reddit posts from three investing subreddits, and (at most) three subreddits relevant to the stock of interest are fetched. Reddit posts are already scored for popularity -- the only additional work to be done is filtering for posts that contain the name of the company of interest.

Here is where it gets interesting. The price of the stock has already been affected by expressed opinions. To make predictions about the future stock price, we are interested in _unexpressed_ opinions. To do this, future popularity scores for all relevant Twitter and Reddit posts are computed according to linear logistic models (see [this notebook](https://github.com/OmerBaddour/stocks_and_sentiment/blob/master/useful_notebooks/machine_learning_model_creation.ipynb)). Posts where where the predicted future popularity score is greater than the current score are filtered. The sentiment of these remaining posts are computed with [TextBlob](https://textblob.readthedocs.io/en/dev/quickstart.html#sentiment-analysis). Finally the weighted sum of $(future\ popularity\ score - current\ popularity\ score) \times sentiment\ score$ is computed, to arrive at an overall sentiment that is yet to be expressed towards the company of interest, that in theory will be reflected in the future company stock price.

Next, the 30 day price information for the company of interest (that was fetched earlier from Yahoo! Finance for risk analysis) is used alongside the overall unexpressed sentiment people have towards the company of interest to generate two distributions that are sampled from and combined to yield projected stock prices for the next week in an iterative manner.

To predict tomorrow's stock price, a normal distribution is constructed that has a mean of the most recent open stock price, and a standard deviation of the mean difference between the daily highs and lows of the stock over the 30 days. We also build a uniform distribution which has at least one bound of 0. The other bound is the overall sentiment people have towards the company of interest multiplied by a constant and divided by the average volume of traded stock for the past month. Each distribution is sampled from, and the sum of the numbers equals tomorrow's stock price.

To calculate the day after tomorrow's stock price, the mean of the normal distribution is adjusted to be tomorrow's predicted stock price. We then sample from this new normal distribution and the uniform and sum.

This process of adjusting the mean of the normal distribution to be the previous day's predicted stock price, sampling, and summing, is repeated 7 times, to result in price predictions for 7 days.

Finally, a plot of the last week's price movement, and the generated week of future price movement are displayed to the user. The user can then confirm or abort the transaction. The `PORTFOLIOS` table in the MySQL database is updated accordingly. The user then returns home, where they see the 30 day price history of their current portfolio.

The best resource for understanding this process is [milestone_notebooks/milestone_2.ipynb](https://github.com/OmerBaddour/stocks_and_sentiment/blob/master/milestone_notebooks/milestone_2.ipynb). It showcases this entire user journey with the relevant code snippets.

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

## Project Future

Some features/revamps I would love to implement:

- A much prettier frontend
- An informative loading animation for transactions, as the backend with a cache-miss takes ~30 seconds to run
- Optimize the runtime of the backend by parallelizing all HTTP requests with threads
- Optimize the number of cache hits by storing cache data for the current day in MySQL
- Password hashing + salting
- Hosting the web app publicly on the Internet
  - Would want to first implement API rate limiting per account and IP address
- Parametrizing the number of Reddit/Twitter posts that are used in the stock sentiment analysis, and allowing the user to control this on the frontend
- Adding a "How it works" page
- Portfolio initialization upon sign up, with an indicator of whether the sign up risk tolerance is too low for the initial portfolio
- Refactor the code by creating objects for all of the common structures (e.g. portfolio entries) and using self-annotating dot notation (rather than lists and indexes)
- Refactor the database code in `flask_app/app.py` into `flask_app/utils/database.py`

## Useful Resources

- [Flask tutorials](https://www.youtube.com/playlist?list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH)
