# import functions

import os
import re
import math
import pytz
import time

from cs50 import SQL
from datetime import datetime
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, usd

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

# make global list
all_rows =[]

# make list into which we put names of meals ordered
orderedmeals = []

@app.route("/")
def index():
    """Direct to appropriate page"""

    # if user not logged in
    if not session:
        return redirect ("/login")

    # check types
    if session["type"]=="customer":
        return redirect ("/mealsuggestions")
    elif session["type"]=="chef":
        return redirect ("/status")


@app.route("/mealsuggestions")
@login_required
def mealsuggestions():
    """Show meal suggestions to users"""

    # define current user
    current_user = session["user_id"]

    # get time
    timezone = db.execute("SELECT timestamp FROM customers WHERE id=:user_id",
                          user_id=current_user)

    # convert time
    times = timezone[0]['timestamp']
    times = times.replace(':', "")
    times = int(times)

    # check time for breakfast
    if times > 600 and times < 1200:

        # declare meals
        mealtype = "breakfast"

    # check time for lunch
    elif times >= 1200 and times < 1700:

        # declare meals
        mealtype = "lunch"

    # check time for dinner
    else:
        mealtype ="dinner"

    # get mealplan of customer
    mealplan = db.execute("SELECT mealplan FROM customers WHERE id=:user_id",
                          user_id=current_user)

    # get mealplan of customer
    mealplan = mealplan[0]['mealplan']

    # get meals associated with mealplan
    meals = db.execute("SELECT * FROM menu WHERE mealplan=:mealplan AND mealtype=:mealtype",
                       mealplan=mealplan, mealtype=mealtype)

    # ensure all_rows is empty
    if len(all_rows) == 0:

        # use list
        for row in meals:

            # make dictionary
            rowdict = {}

            # insert metrics into dictionary
            rowdict['name'] = row['name']
            rowdict['calories'] = row['calories']
            rowdict['nuts'] = row['nuts']
            rowdict['dairy'] = row['dairy']
            rowdict['image'] = row['image']
            rowdict['price'] = usd(row['price'])
            all_rows.append(rowdict)

    # render appropriate template
    return render_template("mealsuggestions.html", meals=all_rows)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """add meal to cart"""

    # define current user
    current_user = session["user_id"]

    # declare cart
    cart = 0

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # declare names
        names = []

        # start for loop
        for row in all_rows:

            # add name of meals
            names.append(row['name'])

        # for ordered meals
        for name in range(len(names)):

            # if meal is clicked
            if request.form.get(names[name]) != None:

                # get all details of meals
                mealdetails = db.execute("SELECT * FROM menu WHERE name=:name",
                                         name = (names[name]))

                # append into orderedmeals
                orderedmeals.append(mealdetails[0])

        # for loop to insert meals into cart
        for food in range(len(orderedmeals)):

            # insert row into cart table
            db.execute("INSERT INTO customerscart (id, meal, calories, price) VALUES (:user_id, :meal, :calories, :price)",
                       user_id=current_user, meal=orderedmeals[food]['name'], calories=orderedmeals[food]['calories'], price=orderedmeals[food]['price'])

            # define total price of meals in cart
            cart = cart + orderedmeals[food]['price']

        # as long as orderedmeals is positive
        if len(orderedmeals) > 0:

            # render cart template
            return render_template("customercart.html", datas=orderedmeals, cart=usd(cart))

        # if have no oredered meals
        else:
            return apology("must order meal", 403)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("customercart.html", datas=orderedmeals, cart=usd(cart))


@app.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    """checkout cart"""

    # define current user
    current_user = session["user_id"]

    # declare cartmeals
    cartmeals = []

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # declare names
        names = []

        # get location of all chefs
        chef = db.execute("SELECT cheflat, cheflong, id, name FROM chefs")

        # get location of customer
        customer = db.execute("SELECT customerlat, customerlong, id FROM customers WHERE id=:user_id",
                              user_id=current_user)

        # start for loop for each row
        for row in orderedmeals:

            # add name of meals
            names.append(row['name'])

        # for ordered meals
        for name in range(len(names)):

            # if checkout is clicked
            if request.form.get("checkout") != None:

                # get all details of meals
                mealdetails = db.execute("SELECT * FROM customerscart WHERE meal=:name",
                                         name = names[name])

                # append into cartmeals
                cartmeals.append(mealdetails[0])

        # for loop for all meals
        for food in range(len(cartmeals)):

            # function which finds distance of chef to user
            def distance(chefs):
                latitude = ((chefs["cheflat"]-customer[0]["customerlat"])**2)
                longitude = ((chefs["cheflong"]-customer[0]["customerlong"])**2)
                return(math.sqrt(latitude + longitude))

            # sort chefs by distance to customer
            all_chefs=sorted(chef, key=distance)

            # declare chefmeals list
            chefmeals = []

            # add chef to chefmeals
            chefmeals.append(all_chefs[0])

            # update chefs orders
            db.execute("INSERT INTO chefsorders (id, customerid, meal, price, calories, status) VALUES (:chefid, :customerid, :meal, :price, :calories, :status)",
                       chefid=all_chefs[0]["id"], customerid=customer[0]["id"], meal=cartmeals[food]['meal'], price=cartmeals[food]['price'], calories=cartmeals[food]['calories'], status="incomplete")

            # insert transaction into customer history
            db.execute("INSERT INTO customershistory (id, meal, price, chef, status) VALUES (:user_id, :meal, :price, :chef, :status)",
                       user_id=current_user, meal=cartmeals[food]['meal'], price=cartmeals[food]['price'], chef=all_chefs[0]['name'], status="incomplete")

        # clear cart
        db.execute("DELETE FROM customerscart WHERE id=:user_id",
                   user_id=current_user)

        # flash message
        flash('Bought!')

        # as long as orderedmeals is positive
        if len(cartmeals) > 0:

            # define length
            length = len(cartmeals)

            # render cart template
            return render_template("ordered.html", cartmeals=cartmeals, chefmeals=chefmeals, length=length)

        # if have no oredered meals
        else:
            return apology("must order meal", 403)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("ordered.html", data=cartmeals)



@app.route("/customerhistory")
@login_required
def customerhistory():
    """Show history of customer's meals"""

    # define current user
    current_user = session["user_id"]

    # query database for all rows that correspond to the user
    data = db.execute("SELECT * FROM customershistory WHERE id=:user_id",
                      user_id=current_user)

    # if there is no history then return apology
    if len(data) == 0:
        return apology("Sorry, there is no transaction history!")

    # if there is history, display database
    else:
        return render_template("customerhistory.html", data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log users in"""

    # Forget any user_id
    session.clear()

    # Chef reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # define username
        username = request.form.get("username")

        # define password
        password = request.form.get("password")

        # define latitude
        latitude = request.form.get("latitude")

        # define longitude
        longitude = request.form.get("longitude")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 403)

        # Ensure latitude was submitted
        elif not latitude:
            return apology("must provide latitude, as a decimal", 403)

        # Ensure longitude was submitted
        elif not longitude:
            return apology("must provide longitude, as a decimal", 403)

        # Query customers for username
        rows = db.execute("SELECT * FROM customers WHERE username=:username",
                          username=request.form.get("username"))

        # Query chefs for username
        checks = db.execute("SELECT * FROM chefs WHERE username=:username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 and len(checks) != 1 and not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Update databases and redirect to appropriate pages
        if len(rows) == 1:
            result = db.execute("UPDATE customers SET customerlat=:latitude, customerlong=:longitude WHERE username=:username",
                                username=request.form.get("username"), latitude=latitude, longitude=longitude)
            # set proper type
            session["type"] = "customer"

            # Remember which customer has logged in
            session["user_id"] = rows[0]["id"]

            return redirect("/mealsuggestions")
        else:
            other = db.execute("UPDATE chefs SET cheflat=:latitude, cheflong=:longitude WHERE username=:username",
                               username=request.form.get("username"), latitude=latitude, longitude=longitude)
            # set proper type
            session["type"] = "chef"

            # Remember which chef has logged in
            session["user_id"] = checks[0]["id"]

            return redirect("/status")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect chef
    return redirect("/")


@app.route("/chefregister", methods=["GET", "POST"])
def chefregister():
    """Register chef"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # define name
        name = request.form.get("name")

        # define username
        username = request.form.get("username")

        # define password
        password = request.form.get("password")

        # define confirmation
        confirmation = request.form.get("confirmation")

        # define latitude
        latitude = request.form.get("latitude")

        # define longitude
        longitude = request.form.get("longitude")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure password has at least one number in it
        elif not re.search("[0-9]", password):
            return apology("password must have at least one number", 400)

        # Ensure password was retyped
        elif not confirmation:
            return apology("must retype correct password", 400)

        # Ensure password was retyped correctly
        elif password != confirmation:
            return apology("must retype correct password", 400)

        # Ensure latitude was submitted
        elif not latitude:
            return apology("must provide latitude, as a decimal", 400)

        # Ensure longitude was submitted
        elif not longitude:
            return apology("must provide longitude, as a decimal", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM customers WHERE username=:username",
                          username=username)

        # Query database for username
        checks = db.execute("SELECT * FROM chefs WHERE username=:username",
                          username=username)

        # Ensure username can exist
        if len(rows) != 0 or len(checks) != 0:
            return apology("username not available!", 400)

        # hash password
        hash_password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # stores user info into database
        result = db.execute("INSERT INTO chefs (username, name, password, cheflat, cheflong) VALUES (:username, :name, :password, :cheflat, :cheflong)",
                            username=username, name=name, password=hash_password, cheflat=latitude, cheflong=longitude)

        # remember which user has logged in
        session["user_id"] = result

        # user is a chef
        session["type"] = "chef"

        # flash message
        flash('Registered!')

        # Redirect user to status
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("chefregister.html")


@app.route("/customerregister", methods=["GET", "POST"])
def customerregister():
    """Register customer"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # define name
        name = request.form.get("name")

        # define username
        username = request.form.get("username")

        # define password
        password = request.form.get("password")

        # define confirmation
        confirmation = request.form.get("confirmation")

        # define mealplan
        mealplan = request.form.get("mealplan")

        # define timezone
        timezones = request.form.get("timezone")

        # define creditcard
        creditcard = request.form.get("creditcard")

        # define latitude
        latitude = request.form.get("latitude")

        # define longitude
        longitude = request.form.get("longitude")

        # Ensure username was submitted
        if not username:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not password:
            return apology("must provide password", 400)

        # Ensure password has at least one number in it
        elif not re.search("[0-9]", password):
            return apology("password must have at least one number", 400)

        # Ensure password was retyped
        elif not confirmation:
            return apology("must retype correct password", 400)

        # Ensure password was retyped correctly
        elif password != confirmation:
            return apology("must retype correct password", 400)

        # Ensure credit card is 16 digits
        elif len(creditcard) != 16:
            return apology("credit card must be 16 digits", 400)

        # Ensure latitude was submitted
        elif not latitude:
            return apology("must provide latitude, as a decimal", 400)

        # Ensure longitude was submitted
        elif not longitude:
            return apology("must provide longitude, as a decimal", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM customers WHERE username=:username",
                          username=request.form.get("username"))

        # Query database for username
        checks = db.execute("SELECT * FROM chefs WHERE username=:username",
                            username=request.form.get("username"))

        # Ensure username can exist
        if len(rows) != 0 or len(checks) != 0:
            return apology("username not available!", 400)

        # hash password
        hash_password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # hash creditcard
        hash_creditcard = generate_password_hash(request.form.get("creditcard"), method='pbkdf2:sha256', salt_length=8)


        # set timezone and local time
        tz = pytz.timezone(timezones)
        localtime = datetime.now(tz).strftime('%H:%M')


        # stores username into database
        result = db.execute("INSERT INTO customers (username, name, password, creditcard, mealplan, customerlat, customerlong, timestamp) VALUES (:username, :name, :password, :creditcard, :mealplan, :customerlat, :customerlong, :timestamp)",
                            username=username, name=name, password=hash_password, creditcard=hash_creditcard, mealplan=mealplan, customerlat=latitude, customerlong=longitude, timestamp=localtime)

        # remember which user has logged in
        session["user_id"] = result

        # user is a customer
        session["type"] = "customer"

        # flash message
        flash('Registered!')

        # Redirect user to mealsuggestions
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("customerregister.html")


@app.route("/cheforders", methods=["GET"])
@login_required
def cheforders():
    """view all chef orders"""

    # define current user
    current_user = session["user_id"]

    # select all chef orders
    orders = db.execute("SELECT * FROM chefsorders WHERE id=:user_id",
                        user_id=current_user)

    # render template of chef orders
    return render_template("cheforders.html", data=orders)


@app.route("/status", methods=["GET", "POST"])
@login_required
def status():
    """changes status of meal"""

    # define current user
    current_user = session["user_id"]

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # for all parameters in cheforders
        for meal in request.form.getlist("mealid"):

            # if meal is clicked
            if request.form.getlist("mealid") != None:

                # define meal_name
                meal_name=db.execute("SELECT * FROM chefsorders")

                # update chefsorders with status
                db.execute("UPDATE chefsorders SET status=:status_new WHERE mealid=:mealid",
                           mealid=meal, status_new="complete")

                # update customershistory with status
                db.execute("UPDATE customershistory SET status=:status_new WHERE mealid=:mealid",
                           mealid=meal, status_new="complete")

    # define total revenue chef has made
    total = db.execute("SELECT SUM(price) FROM chefsorders WHERE id=:user_id AND status=:status",
                       user_id=current_user, status="complete")

    # query for chefsorders meals
    chefsmeals = db.execute("SELECT * FROM chefsorders WHERE id=:user_id",
                            user_id=current_user)

    # if chefmeals is positive
    if total[0]["SUM(price)"]:

        # redirect to chefsorders page
        return render_template("cheforders.html", data=chefsmeals, total=usd(total[0]["SUM(price)"]))

    else:
        # redirect to chefsorders page
        return render_template("cheforders.html", data=chefsmeals, total="0")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

