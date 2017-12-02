# Hi Vojta--History, Index, and Sell are (at varying degrees of being) unfinished. Just wanted to give you a heads up!
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure responses aren't cached
if app.config["DEBUG"]:
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
db = SQL("sqlite:///userdata.db")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    # Save how much cash the user has and save "total" which can be updated in the forloop
    cash = db.execute("SELECT cash FROM users WHERE id = :user_id",
                      user_id=session["user_id"])
    total = cash[0]["cash"]

    # Group together and sum stocks of the same symbol
    stocks = db.execute("SELECT stock, SUM(number_of_stocks) AS number_of_stocks FROM bought WHERE user_id = :id GROUP BY stock HAVING SUM(number_of_stocks)>0",
                        id=session["user_id"])

    # Create a for loop that iterates through and writes the stock, its price, its name, and the total amount of cash
    for stock in stocks:
        quote = lookup(stock["stock"])
        stock["price"] = quote["price"]
        stock["name"] = quote["name"]
        total += stock["number_of_stocks"] * stock["price"]

    return render_template("index.html")


@app.route("/words", methods=["GET", "POST"])
@login_required
def buy():

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("Title"):
            return apology("must provide title", 403)

        # Save variables to put into SQL
        title = request.form.get("Title")
        entry = request.form.get("Entry")

        # OKAY it's time to write this into something....
        db.execute("INSERT INTO diary (user_id, title, body) VALUES (:user_id, :title, :entry)",
                       user_id=session["user_id"], title=request.form.get("Title"), body=request.form.get("Entry")

        return render_template("diary.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("words.html")


# I'm so sorry Vojta, I was at Yale for a conference this weekend and had a midterm Monday and couldn't finish this section.
@app.route("/history")
@login_required
#def history():
    #"""Show history of transactions"""
   # return apology("TODO")


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
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        quote = lookup(request.form.get("symbol"))

        # If quote is not a real stock, return apology
        if not quote:
            return apology("This stock is not valid")

        # If quote does return something, show that price on the page
        price = quote["price"]
        name = quote["name"]
        return render_template("quoted.html", price1=usd(price), name1=name)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure password 2 was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide password twice", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match!", 400)

        # Hash password so it's not in the database
        hash = generate_password_hash(request.form.get("password"))

        # Compare what the user typed in for "username" with the usernames in the database
        result = db.execute("SELECT username FROM users WHERE username = :username",
                            username=request.form.get("username"))

        # If it already is there, print error
        if result:
            return apology("username is already taken", 400)

        # Insert information into the table
        user_name = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)",
                               username=request.form.get("username"), hash=hash)

        # Remember which user has logged in
        session["user_id"] = user_name

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

# I mostly copied the code from "Buy," leaving comments for things that I should do


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        if not request.form.get("symbol"):
            return apology("must provide symbol", 400)

        # Ensure share was submitted
        elif not request.form.get("shares"):
            return apology("must provide share", 400)

        share = request.form.get("shares")
        if not share.isdigit():
            return apology("must be a positive whole number", 400)

        quote = lookup(request.form.get("symbol"))

        # If symbol is not a real stock, return apology
        if not quote:
            return apology("This stock is not valid")

        shares = int(request.form.get("shares"))

        # If we don't have the amount of requested stock to sell, return apology
        # Else if we do, sell it! Insert another line into the table, but with negative numbers.
        # Return to index
        # If the amount of bought stocks for a certain stock is equal the same number of sold stocks for that same stock, delete it from the table so it does not appear in history!

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("words.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
