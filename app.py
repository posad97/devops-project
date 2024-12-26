import os

from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, db_execute, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Make sure environment variables are set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

if not os.environ.get("MYSQL_HOSTNAME"):
    raise RuntimeError("MYSQL_HOSTNAME not set")

if not os.environ.get("MYSQL_USER"):
    raise RuntimeError("MYSQL_USER not set")

if not os.environ.get("MYSQL_ROOT_PASSWORD"):
    raise RuntimeError("MYSQL_ROOT_PASSWORD not set")

if not os.environ.get("MYSQL_DATABASE"):
    raise RuntimeError("MYSQL_DATABASE not set")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    # Query database for all stocks current user has
    rows = db_execute("SELECT symbol, name, shares FROM stocks WHERE user_id = %s", (session["user_id"],))

    # Query database for the current cash user has
    user_cash = float(db_execute("SELECT cash FROM users WHERE id = %s", (session["user_id"],))[0]['cash'])

    # Define the variable to calculate shares dividends
    shares_dividends = 0

    # Iterate over each row for the query response
    for row in rows:

        # Get ticker from row output
        ticker = row['symbol']

        # Fetch ticker data from API
        ticker_data = lookup(ticker)

        # Check the current stock price
        cur_price = ticker_data["price"]

        # Calculate the dividends based on the current price
        row['total'] = row['shares'] * cur_price
        row['price'] = cur_price

        # Update the total dividents from stocks value
        shares_dividends += row['shares'] * cur_price

    # Calculate the summary cash user has: dividends from stock + cash
    user_total_cash = user_cash + shares_dividends

    # Return the page populated with the information about the stocks, dividends and cash
    return render_template("index.html", rows=rows, user_cash=user_cash, user_total_cash=user_total_cash)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Checks for valid user input
        if not request.form.get("symbol"):
            return apology("Symbol field should not be blank", 400)
        
        # Assign the ticker variable to the symbol provided by user
        ticker = request.form.get("symbol")

        # Fetch ticker data from API
        ticker_data = lookup(ticker)

        # If fetch from API failed - return an apology with the response status code
        if ticker_data["status_code"] != 200:
            return apology("Symbol does not exist", ticker_data["status_code"])
        
        # Variable stores the number of shares user wants to buy
        shares_to_buy = request.form.get("shares")

        # Ensure amount of shares provided by user is a valid number
        if not shares_to_buy.isdigit():
            return apology("Shares must be whole number", 400)

        if float(shares_to_buy) % 1 != 0:
            return apology("Shares must be whole number", 400)

        if int(shares_to_buy) < 1:
            return apology("Please provide a valid quantity", 400)

        # Variable stores current stock price fetched from API
        price = ticker_data['price']

        # Variable stores company name fetched from API
        company_name = ticker_data['name']

        # Query the database for the current cash user has
        rows = db_execute("SELECT cash FROM users WHERE id = %s", (session["user_id"],))

        # And assign it to variable
        user_cash = rows[0]["cash"]

        # Total price for the number of shares user wants to buy
        total_shares_price = price * float(shares_to_buy)

        # Check if user has enough cash to buy this amount of shares
        if user_cash < total_shares_price:

            # Return apology if not
            return apology("Not enough money", 400)

        # Update the user's cash in the database decreasing it by the price of shares baught
        db_execute("UPDATE users SET cash = cash - %s WHERE id = %s", (total_shares_price, session["user_id"],))

        # Query the DB with symbol of shares baught
        rows = db_execute("SELECT * FROM stocks WHERE symbol = %s AND user_id = %s", (ticker, session["user_id"],))

        # If user doesn't have shares of this company, insert the info into the table
        if len(rows) == 0:
            db_execute("INSERT INTO stocks (user_id, symbol, name, shares) VALUES(%s, %s, %s, %s)",
                       (session["user_id"], ticker, company_name, shares_to_buy,))

        # If user already has stocks of this company, just update the shares amount in the table
        else:
            db_execute("UPDATE stocks SET shares = shares + %s WHERE symbol = %s AND user_id = %s",
                       (shares_to_buy, ticker, session["user_id"],))

        # Update the history table with the performed transaction information
        db_execute("INSERT INTO history (user_id, symbol, name, shares, price, operation) VALUES(%s, %s, %s, %s, %s, %s)",
                   (session["user_id"], ticker, company_name, shares_to_buy, price, "purchase",))

        # Redirect to root
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    # Query DB for all history of transaction performed by the user
    rows = db_execute("SELECT * FROM history WHERE user_id = %s", (session["user_id"],))

    # Return a page with populated transaction information
    return render_template("history.html", rows=rows)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        
        # Assign user's credentials to the respective variables
        username = request.form.get("username")
        password = request.form.get("password")

        # Query database for username
        rows = db_execute("SELECT * FROM users WHERE username = %s", (username,))

        #  Ensure user exists
        if len(rows) != 1:
            return apology("invalid username and/or password", 400)

        # Variable stores the hash of the user's password
        password_hash = rows[0]["hash"]

        # Ensure password is correct
        if not check_password_hash(password_hash, password):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":

        # Checks for valid user input
        if not request.form.get("symbol"):
            return apology("Please provide symbol", 400)
        
        # Assign the ticker variable to the symbol provided by user
        ticker = request.form.get("symbol")

        # Fetch ticker data from API
        ticker_data = lookup(ticker)

        # If fetch from API failed - return an apology with the response status code
        if ticker_data["status_code"] != 200:
            return apology("Symbol does not exist", ticker_data["status_code"])

        # Returns the page with populated information about the company stocks price
        return render_template("quoted.html", company=ticker_data)

    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Checks if username field is blank
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Checks if password field is blank
        if not request.form.get("password"):
            return apology("must provide password", 400)

        # Checks if passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)
        
        # Assign user's credentials to the respective variables
        username = request.form.get("username")
        password = request.form.get("password")

        # Query the DB for a username entered
        rows = db_execute("SELECT * FROM users WHERE username = %s", (username,))

        # Check if user already exists
        if len(rows) == 1:
            return apology("username already exists", 400)
        
        password_hash = generate_password_hash(password)

        # Insert username and password hash into DB
        db_execute("INSERT INTO users (username, hash) VALUES(%s,%s)", (username, password_hash,))

        # Redirect to root
        return redirect("/register")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        # Check if symbol field is blank
        if not request.form.get("symbol"):
            return apology("Must provide symbol", 400)
        
        # Check if stock number provided is positive and not 0
        if int(request.form.get("shares")) < 1:
            return apology("Please provide a valid number of shares", 400)
        
        # Assign the ticker variable to the symbol provided by user
        ticker = request.form.get("symbol")

        # Variable stores the number of shares user wants to buy
        shares_to_sell = int(request.form.get("shares"))

        # Query the DB for specific stocks inputed by user
        rows = db_execute("SELECT * FROM stocks WHERE symbol = %s AND user_id = %s", (ticker, session["user_id"],))

        # Variable stores amount of shares posessed by user
        user_shares = rows[0]['shares']

        # Checks if user has specific stocks
        if len(rows) != 1:
            return apology("You don't have these stocks", 400)

        # Checks if user has less shares than they want to sell
        if user_shares < shares_to_sell:
            return apology("You have less shares than the number provided", 400)
        
        # Fetch ticker data from API
        ticker_data = lookup(ticker)

        # If fetch from API failed - return an apology with the response status code
        if ticker_data["status_code"] != 200:
            return apology("Symbol does not exist", ticker_data["status_code"])

        # Variable stores current stock price fetched from API
        price = ticker_data['price']

        # Variable stores company name fetched from API
        company_name = ticker_data['name']

        # Reflect transaction in the history table
        db_execute("INSERT INTO history (user_id, symbol, name, shares, price, operation) VALUES(%s, %s, %s, %s, %s, %s)", (session["user_id"], ticker, company_name, shares_to_sell, price, "sell",))

        # Update user's cash with dividents from selling stocks
        db_execute("UPDATE users SET cash = cash + %s WHERE id = %s", (price * float(shares_to_sell), session["user_id"],))

        # If user sold all the stocks they had for a current company delete the
        # entry for this company from the table
        if user_shares - shares_to_sell == 0:
            db_execute("DELETE FROM stocks WHERE symbol = %s AND user_id = %s", (ticker, session["user_id"],))

        # Otherwise just decrease the number of stocks by the number sold
        else:
            db_execute("UPDATE stocks SET shares = shares - %s WHERE symbol = %s AND user_id = %s",
                       (shares_to_sell, ticker, session["user_id"],))

        # Redirect to root
        return redirect("/")

    else:
        rows = db_execute("SELECT DISTINCT symbol FROM stocks WHERE user_id = %s", (session["user_id"],))
        return render_template("sell.html", rows=rows)


@app.route("/charge", methods=["GET", "POST"])
@login_required
def charge():
    if request.method == "POST":

        # Checks if field is empty
        if not request.form.get("amount"):
            return apology("must provide amount", 400)
        
        money_to_charge = float(request.form.get("amount"))

        # Checks id amount of money is 0 or negative
        if money_to_charge < 1:
            return apology("must provide valid amount", 400)

        # Update user's cash with charged amount
        db_execute("UPDATE users SET cash = cash + %s WHERE id = %s", (money_to_charge, session["user_id"],))

        # Redirect to root
        return redirect("/")
    else:
        return render_template("charge.html")