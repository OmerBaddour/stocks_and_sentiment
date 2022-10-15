import base64
from io import BytesIO

from matplotlib.figure import Figure
from textblob import TextBlob


def generate_image_bytes(series):
    """
    Generates a Figure using the Series, and returns the bytes for the image.
    The bytes can be used to display the image in HTML code.
    # https://matplotlib.org/devdocs/gallery/user_interfaces/web_application_server_sgskip.html
    """

    # create Figure
    fig = Figure()
    ax = fig.subplots()
    ax.plot(series)
    ax.set_ylabel("Price")
    ax.tick_params(labelrotation=23)

    # save Figure to a temporary buffer
    buf = BytesIO()
    fig.savefig(buf, format="png")

    # return bytes
    return base64.b64encode(buf.getbuffer()).decode("ascii")


def check_rationality(data):
    """
    Returns whether the magnitude of the sentiment of the input string is sufficiently low.
    """
    return abs(TextBlob(data).sentiment.polarity) < 0.4
