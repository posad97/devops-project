import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
import mysql.connector
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Contact Tiingo API to fetch stock data
    try:
        api_key = os.environ.get("API_KEY")
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {api_key}'
        }
        iex_url = f"https://api.tiingo.com/iex/{urllib.parse.quote_plus(symbol)}"
        metadata_url = f"https://api.tiingo.com/tiingo/daily/{urllib.parse.quote_plus(symbol)}"
        response_iex = requests.get(iex_url, headers=headers)
        response_metadata = requests.get(metadata_url, headers=headers)
        response_iex.raise_for_status()
        response_metadata.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        ticker_iex = response_iex.json()[0]
        ticker_metadata = response_metadata.json()

        return {
            "name": ticker_metadata["name"],
            "price": float(ticker_iex["last"]),
            "symbol": ticker_iex["ticker"]
        }
    except (KeyError, TypeError, ValueError):
        return None


#  DB interaction routine
def db_execute(query, data=None):

    conn = None
    cursor = None
    result = None
    
    try:
        conn = mysql.connector.connect(
            host = os.environ.get("DB_HOSTNAME"),      # Name of the MySQL container
            user = os.environ.get("DB_USER"),      # MySQL user
            password = os.environ.get("DB_PASSWORD"),  # Root password
            database = os.environ.get("DB_NAME")     # Database name
        )

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, data)

        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            result = rows
            
        else:
            conn.commit()
            result = None

    except mysql.connector.Error as err:
        print(f"Error: {err}") # Log the error and handle the exception appropriately

        if conn:
            conn.rollback()  # Rollback in case of error during transaction

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return result


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
