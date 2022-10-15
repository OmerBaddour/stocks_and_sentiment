def get_current_portfolio(cursor, user_id):
    """
    Takes in user_id, and outputs the user's portfolio.
    """
    get_portfolio = """SELECT
                            STOCK_NAME,
                            TICKER,
                            VOLUME
                        FROM
                            PORTFOLIOS
                        WHERE
                            USER_ID = %s
                     """
    cursor.execute(get_portfolio, (user_id,))
    return list(cursor.fetchall())


def update_portfolio_in_database(cursor, conn, portfolio, user_id):
    """
    Updates the user's portfolio in the database.
    """

    delete_old_portfolio = """DELETE FROM PORTFOLIOS
                              WHERE USER_ID = %s
                           """
    cursor.execute(delete_old_portfolio, (user_id,))

    add_stock_to_portfolio = """INSERT INTO PORTFOLIOS(
                                    USER_ID,
                                    STOCK_NAME,
                                    TICKER,
                                    VOLUME
                                )
                                VALUES(%s, %s, %s, %s)
                            """
    for stock_name, ticker, volume in portfolio:
        cursor.execute(add_stock_to_portfolio, (user_id, stock_name, ticker, volume))

    conn.commit()
    return None
