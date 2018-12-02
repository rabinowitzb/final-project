import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import math

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///hambre.db")

# Meal suggestions for users
@app.route("/mealsuggestions")
@login_required
def index():
    """Show meal suggestions to users"""

    # Obtain all the information in histories, and for the # of stocks have that column be equal to the total number of stocks per specific user and symbol
    suggestions = db.execute("SELECT *, SUM(stocks) FROM histories WHERE id = :user_id GROUP BY symbol", user_id=session["user_id"])


        return render_template("index.html", rows=stocks, pocketcash=usd(pocketcash), sumcash=usd(sumcash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Check if the stock information is valid
        if not request.form.get("symbol"):
            return apology("Input symbol")

        elif not request.form.get("shares"):
            return apology("Input shares")

        # Obtain the current information of the inputted stock
        correctsymbol = lookup(request.form.get("symbol"))

        if not correctsymbol:
            return apology("Please enter a correct stock symbol")

        # Check if the value of shares is an int
        elif not request.form.get("shares").isdigit():
            return apology("Please enter a positive integer for the number of stocks you wish to buy")

        # Check if the user has inputted a positive number of stocks
        elif int(request.form.get("shares")) <= 0:
            return apology("Please enter a positive integer for the number of stocks you wish to buy")

        else:
            numshares = int(request.form.get("shares"))
            # Obtain the user's current amount of liquid/pocket cash
            usercash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
            usercash_two = usercash[0]['cash']
            # Calculate the total amount of money the user has for a particular stock
            totalcost = numshares * correctsymbol['price']
            # Make sure the user can only obtain a stock they can afford
            if totalcost > usercash_two:
                return apology("You can only buy a stock(s) that you can afford")

            if totalcost <= usercash_two:
                # Update the user's cash and create a new entry for the stock
                newcash = usercash_two - totalcost
                db.execute("INSERT INTO histories (id, symbol, stocks, price) VALUES (:user_id, :symbol, :stocks, :price)", user_id=session["user_id"], symbol=request.form.get("symbol"),
                           stocks=request.form.get("shares"), price=correctsymbol['price'])
                db.execute("UPDATE users SET cash = :newcash WHERE id = :user_id", newcash=newcash, user_id=session["user_id"])
                return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    # Obtain the username
    username = request.args.get("username")
    # Check if the username exists
    rows = db.execute("SELECT * FROM users WHERE username = :username", username=username)
    if rows:
        return jsonify(False)
    return jsonify(True)


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Obtain the symbol, number of stocks, price, and timestamp when bought and store the information in a variable
    stacks = db.execute("SELECT symbol, stocks, price, timestamp FROM histories WHERE id = :user_id", user_id=session['user_id'])
    # Input the information on the page per given input
    for stack in stacks:
        return render_template("history.html", stacks=stacks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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

    # If the request is to go to the page, send user to page
    if request.method == "GET":
        return render_template("quote.html")

    else:
        # If the user inputs a valid stock symbol, show the current price. Otherwise, tell them to input a valid input
        symbol = request.form.get("symbol")
        quote = lookup(symbol)

        if quote != None:
            return render_template("quoted.html", quote=quote)

        else:
            return apology("Please only enter correct valid stock symbols")


@app.route("/customerregistration", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        password = request.form.get("password")
        username = request.form.get("username")
        mealplan = request.form.get("mealplan")
        cash = request.form.get("cash")

        if not cash:
            return apology("Please enter the amount of cash ")

        if not username:
            return apology("Missing username!")

        if not password or not confirmation:
            return apology("Missing password and/or password confirmation!")

        if password != confirmation:
            return apology("Make sure password and confirmation match!")

        if password.isalpha() and len(password) <= 2:
            return apology("Password must contain some non-letter symbols and be longer than 2 characters")

        hash = generate_password_hash(password)

        # longitude = geolocation[0]
        # latitude = geolocation[1]

        result = db.execute("INSERT INTO customers (username , name, password, cash, mealplan) VALUES (:username , :name, :password, :cash, mealplan)",
                            username=username, name=name, password=hash, cash= cash, mealplan=mealplan)

        if not result:
            return apology("Database already has that username")

        session["user_id"] = result

        return redirect("/mealsuggestions")

    else:
        return render_template("customerregistration.html")

@app.route("/chefregistration", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        username = request.form.get("username")
        geolocation = request.form.get("geolocation").split(",")

        if not geolocation:
            return apology("Missing geolocation!")

        if not username:
            return apology("Missing username!")

        if not password or not confirmation:
            return apology("Missing password and/or password confirmation!")

        if password != confirmation:
            return apology("Make sure password and confirmation match!")

        if password.isalpha() and len(password) <= 2:
            return apology("Password must contain some non-letter symbols and be longer than 2 characters")

        longitude = geolocation[0]
        latitude = geolocation[1]


        hash = generate_password_hash(password)
        result = db.execute("INSERT INTO chefs (username , name, password, longitude, latitude) VALUES (:username , :name, :password, :longitude, :latitude)",
                            username=username, name=name, password=hash)

        if not result:
            return apology("Database already has that username")

        session["user_id"] = result

        return redirect("/chef")

    else:
        return render_template("chefregister.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        symbol = request.form.get("symbol")
        numshares = int(request.form.get("shares"))
        cash = db.execute("SELECT cash FROM users WHERE id = :user_id", user_id=session["user_id"])
        money = cash[0]['cash']
        correctsymbol = lookup(symbol)

        # If the input isn't valid, give error message
        if not correctsymbol:
            return apology("Please enter a correct symbol")

        if not numshares:
            return apology("Please enter # of shares")

        if not numshares > 0:
            return apology("Please enter positive integer")

        else:
            # Check to see if the stock is one which the user actually has. Also that the quantity is not greater than what the user has
            shares = db.execute("SELECT SUM(stocks) FROM histories WHERE id = :user_id AND symbol = :symbol",
                                user_id=session["user_id"], symbol=request.form.get('symbol'))

            if not shares[0]['SUM(stocks)']:
                return apology("You can only sell a stock you own")

            elif numshares > shares[0]['SUM(stocks)']:
                return apology("YOu can't sell more stocks than you own")

            else:
                moneyupdate = money + numshares * correctsymbol['price']
                # Insert the sell into histories
                db.execute("INSERT INTO histories (id, stocks, price, symbol) VALUES (:user_id, :stocks, :price, :symbol)",
                           user_id=session["user_id"], stocks=-1 * numshares, price=correctsymbol['price'], symbol=request.form.get('symbol'))
                # Update the liquid/pocket cash the user has
                db.execute("UPDATE users SET cash = :moneyupdate WHERE id = :user_id",
                           moneyupdate=moneyupdate, user_id=session["user_id"])
                return redirect("/")

    else:
        options = db.execute("SELECT symbol FROM histories WHERE id = :user_id", user_id=session["user_id"])
        # Create a set to ensure there are no duplicates
        options_two = set()
        for i in options:
            options_two.add(i['symbol'])
        return render_template("sell.html", options_two=options_two)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
