import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, url_for
from flaskext.mysql import MySQL

from forms import ConfirmTransactionForm, LoginForm, SignUpForm, TransactionForm
from utils.cache import (
    add_all_to_cache,
    add_to_cache_init,
    generate_cache_with_predictions,
)
from utils.database import get_current_portfolio, update_portfolio_in_database
from utils.finance import (
    aggregated_portfolio,
    calculate_portfolio_risk,
    check_portfolio_risk,
    check_stock_in_portfolio,
    check_ticker_is_valid,
    generate_next_portfolio,
)
from utils.utils import check_rationality, generate_image_bytes

load_dotenv()

app = Flask(__name__)
mysql = MySQL()
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

# https://stackoverflow.com/questions/9845102/using-mysql-in-flask
app.config["MYSQL_DATABASE_USER"] = os.getenv("MYSQL_DATABASE_USER")
app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_DATABASE_PASSWORD")
app.config["MYSQL_DATABASE_HOST"] = os.getenv("MYSQL_DATABASE_HOST")
app.config["MYSQL_DATABASE_DB"] = os.getenv("MYSQL_DATABASE_DB")
mysql.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()

# store current user information, such as id and first name
current_user = dict()

# {ticker: (sentiment score from Reddit posts and Tweets, last month's price data)}
# {string: (int, DataFrame)}
cache = dict()


# store current transaction information for confirmation
# [[stock_name, ticker, quantity]]
current_portfolio = []
next_portfolio = []


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


@app.route("/")
def base():
    return redirect(url_for("login"))


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        find_user = """SELECT
                           USER_ID,
                           FIRST_NAME,
                           LAST_NAME,
                           TOLERANCE_FOR_RISK
                       FROM
                           USERS
                       WHERE
                           EMAIL = %s
                           AND PASSWORD = %s
                    """

        cursor.execute(find_user, (form.email.data, form.password.data))
        user_data = cursor.fetchall()
        if user_data:
            current_user["id"] = user_data[0][0]
            current_user["first_name"] = user_data[0][1]
            current_user["last_name"] = user_data[0][2]
            current_user["tolerance_for_risk"] = user_data[0][3]
            return redirect(url_for("home"))
        else:
            flash("Login unsuccessful. Please check username and password", "danger")

    return render_template("login.html", form=form)


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


@app.route("/sign_up", methods=["GET", "POST"])
def sign_up():
    form = SignUpForm()

    if form.validate_on_submit():
        create_user = """INSERT INTO USERS(
                             FIRST_NAME,
                             LAST_NAME,
                             EMAIL,
                             PASSWORD,
                             TOLERANCE_FOR_RISK
                         )
                         VALUES(%s, %s, %s, %s, %s)
                      """

        try:
            cursor.execute(
                create_user,
                (
                    form.first_name.data,
                    form.last_name.data,
                    form.email.data,
                    form.password.data,
                    form.tolerance_for_risk.data,
                ),
            )
        except:
            flash("Sign up unsuccessful. Please enter a unique email.", "danger")
            return render_template("sign_up.html", form=form)

        conn.commit()
        return redirect(url_for("login"))

    return render_template("sign_up.html", form=form)


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


@app.route("/home", methods=["GET", "POST"])
def home():

    global current_portfolio

    # fetch user portfolio
    fetch_user_portfolio = """SELECT
                                  STOCK_NAME,
                                  TICKER,
                                  VOLUME
                              FROM
                                  PORTFOLIOS
                              WHERE
                                  USER_ID = %s
                           """
    cursor.execute(fetch_user_portfolio, (current_user["id"],))
    current_portfolio = cursor.fetchall()

    # populate cache
    for _stock_name, ticker, _volume in current_portfolio:
        add_to_cache_init(ticker, cache)

    # generate Series of all stocks in portfolio
    series_aggregated = aggregated_portfolio(current_portfolio, cache)

    image_data = generate_image_bytes(series_aggregated)

    return render_template(
        "home.html",
        first_name=current_user["first_name"],
        portfolio_history_img_html=image_data,
    )


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


@app.route("/do_transaction", methods=["GET", "POST"])
def do_transaction():

    global current_portfolio, next_portfolio

    form = TransactionForm()

    if form.validate_on_submit():
        if check_ticker_is_valid(form.ticker.data):
            if check_rationality(form.current_mood.data):
                if check_rationality(form.reasoning.data):
                    current_portfolio = get_current_portfolio(
                        cursor, current_user["id"]
                    )
                    add_all_to_cache(
                        current_portfolio,
                        cache,
                        os.getenv("REDDIT_CLIENT_ID"),
                        os.getenv("REDDIT_CLIENT_SECRET"),
                        os.getenv("REDDIT_USER_AGENT"),
                        os.getenv("TWITTER_BEARER_TOKEN"),
                    )

                    if form.buy.data:
                        next_portfolio = generate_next_portfolio(
                            current_portfolio,
                            form.stock_name.data,
                            form.ticker.data,
                            "buy",
                            form.quantity.data,
                            cache,
                            os.getenv("REDDIT_CLIENT_ID"),
                            os.getenv("REDDIT_CLIENT_SECRET"),
                            os.getenv("REDDIT_USER_AGENT"),
                            os.getenv("TWITTER_BEARER_TOKEN"),
                        )
                    if form.sell.data:
                        if check_stock_in_portfolio(
                            current_portfolio, form.ticker.data
                        ):
                            next_portfolio = generate_next_portfolio(
                                current_portfolio,
                                form.stock_name.data,
                                form.ticker.data,
                                "sell",
                                form.quantity.data,
                                cache,
                                os.getenv("REDDIT_CLIENT_ID"),
                                os.getenv("REDDIT_CLIENT_SECRET"),
                                os.getenv("REDDIT_USER_AGENT"),
                                os.getenv("TWITTER_BEARER_TOKEN"),
                            )

                    if check_portfolio_risk(
                        calculate_portfolio_risk(
                            current_portfolio,
                            cache,
                            os.getenv("REDDIT_CLIENT_ID"),
                            os.getenv("REDDIT_CLIENT_SECRET"),
                            os.getenv("REDDIT_USER_AGENT"),
                            os.getenv("TWITTER_BEARER_TOKEN"),
                        ),
                        current_user["tolerance_for_risk"],
                    ):
                        return redirect(url_for("confirm_transaction"))

                    else:
                        flash(
                            "The risk of your portfolio after this transaction would be greater than your tolerance for risk.",
                            "danger",
                        )
                        return render_template("do_transaction.html", form=form)
                else:
                    flash(
                        "Your reasoning is not neutral enough to be rational.", "danger"
                    )
                    return render_template("do_transaction.html", form=form)
            else:
                flash(
                    "Your mood is not neutral enough for you to act rationally.",
                    "danger",
                )
                return render_template("do_transaction.html", form=form)
        else:
            flash("Invalid ticker symbol.", "danger")
            return render_template("do_transaction.html", form=form)

    return render_template("do_transaction.html", form=form)


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------


@app.route("/confirm_transaction", methods=["GET", "POST"])
def confirm_transaction():
    form = ConfirmTransactionForm()

    # generate cache_with_predictions
    cache_with_predictions = generate_cache_with_predictions(cache)

    aggregated_current_portfolio = aggregated_portfolio(
        current_portfolio, cache_with_predictions
    )
    current_portfolio_image = generate_image_bytes(aggregated_current_portfolio)

    aggregated_next_portfolio = aggregated_portfolio(
        next_portfolio, cache_with_predictions
    )
    next_portfolio_image = generate_image_bytes(aggregated_next_portfolio)

    if form.validate_on_submit():
        if form.confirm.data:
            update_portfolio_in_database(
                cursor, conn, next_portfolio, current_user["id"]
            )
            flash("Successfully updated portfolio!", "success")
            return redirect(url_for("home"))
        if form.abort.data:
            flash("Transaction aborted.", "success")
            return redirect(url_for("home"))

    return render_template(
        "confirm_transaction.html",
        form=form,
        current_portfolio_image=current_portfolio_image,
        next_portfolio_image=next_portfolio_image,
    )


# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
