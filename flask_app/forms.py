from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Regexp, EqualTo, NumberRange


class SignUpForm(FlaskForm):
    first_name = StringField("First Name",
                             validators=[DataRequired(), Regexp(regex="[a-zA-Z-]{2,}")]
                            )
    last_name = StringField("Last Name",
                             validators=[DataRequired(), Regexp(regex="[a-zA-Z-]{2,}")]
                           )
    email = StringField("Email",
                        validators=[DataRequired(), Regexp(regex="[a-zA-Z0-9.-_]+@[a-zA-Z0-9.-_]+\.[a-zA-Z]{2,}")]
                       )
    password = PasswordField("Password",
                             validators=[DataRequired()]
                            )
    confirm_password = PasswordField("Confirm Password",
                                     validators=[DataRequired(), EqualTo("password")]
                                    )
    tolerance_for_risk = IntegerField("Tolerance for Risk",
                                      validators=[DataRequired(), NumberRange(min=1, max=5)]
                                     )
    submit = SubmitField("Sign Up")


class LoginForm(FlaskForm):
    email = StringField("Email",
                        validators=[DataRequired(), Regexp(regex="[a-zA-Z0-9.-_]+@[a-zA-Z0-9.-_]+\.[a-zA-Z]{2,}")]
                       )
    password = PasswordField("Password",
                             validators=[DataRequired()]
                            )
    submit = SubmitField("Login")


class TransactionForm(FlaskForm):
    stock_name = StringField("Stock name",
                             validators=[DataRequired()]
                            )
    ticker = StringField("Ticker",
                         validators=[DataRequired()]
                        )
    quantity = IntegerField("Quantity",
                           validators=[DataRequired(), NumberRange(min=1)]
                          )
    current_mood = StringField("Current mood",
                               validators=[DataRequired()]
                              )
    reasoning = StringField("Reasoning",
                            validators=[DataRequired()]
                           )
    buy = SubmitField("Buy")
    sell = SubmitField("Sell")


class ConfirmTransactionForm(FlaskForm):
    confirm = SubmitField("Confirm")
    abort = SubmitField("Abort")
