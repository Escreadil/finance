import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")



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
    n = db.execute("SELECT username FROM users WHERE id is ?", session.get("user_id"))
    for l in n:
        for k, v in l.items():
            name = v
    c = db.execute("SELECT cash FROM users WHERE username is ?", name)
    for l in c:
        for k,v in l.items():
            cash = round(v)
    try:
        all = db.execute("SELECT username, compname, price, amount, totalprice FROM buy WHERE username is ?", name)
        compname = []
        price = []
        amount = []
        totalprice = []
        x = range(len(all))
        for i in range(len(all)):
            for k, v in all[i].items():
                if k == 'compname':
                    compname.append(v)
                if k == 'price':
                    price.append(v)
                if k == 'amount':
                    if v <= 0:
                        continue
                    else:
                        amount.append(v)
                if k == 'totalprice':
                    totalprice.append(v)
        spent = sum(totalprice)
        before = round(spent + cash)

        return render_template("index.html", username=name, cash=cash, compname=compname, price=price, amount=amount, totalprice=totalprice, x=x, spent=spent, before=before)

    except UnboundLocalError:

        return render_template("index.html")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")

    else:
        symbol = request.form.get("symbol2")
        shares = request.form.get("shares")
        check = lookup(request.form.get("symbol2"))

        if symbol == "":
            return apology("Can't be empty.")
        if int(shares) < 0:
            return apology("Must be positive number.")

        if not lookup(request.form.get("symbol2")):
            return apology("Invalid company symbol.")

        if check:
            for i, k in check.items():
                if i == 'price':
                    curprice = k
        totalprice = int(shares)*curprice

        usercash = db.execute("SELECT cash FROM users WHERE id is ?", session.get("user_id"))
        username = db.execute("SELECT username FROM users WHERE id is ?", session.get("user_id"))

        for i in usercash:
            for k, v in i.items():
                userscash = v
        for i in username:
            for k, v in i.items():
                usersname = v
        x = datetime.datetime.now()
        if userscash > totalprice:
            db.execute("INSERT INTO bought (id, username, compname, price, amount, totalprice, date) VALUES(?,?,?,?,?,?,?)", session.get("user_id"), usersname , symbol.upper(), curprice, shares, totalprice, x)
            db.execute("INSERT INTO buy (id, username, compname, price, amount, totalprice, date) VALUES(?,?,?,?,?,?,?)", session.get("user_id"), usersname , symbol.upper(), curprice, shares, totalprice, x)
            usernewcash = userscash - totalprice
            db.execute("UPDATE users SET cash = ? WHERE username = ?", usernewcash, usersname)
            return redirect("/")
        if userscash < totalprice:
            return apology("Not enough cash in the account")



@app.route("/check", methods=["GET", "POST"])
@login_required
def check():
    if request.method == "POST":

        symbol = request.form.get("symbol")
        check = lookup(request.form.get("symbol"))

        if symbol == "":
            return apology("Can't be empty.")
        elif not symbol.isalpha():
            return apology("Must only contain letters")
        elif check:
            for i, k in check.items():
                if i == 'price':
                    curprice = k
        elif not check:
            return apology("Invalid company symbol.")

        return render_template("check.html", symbol=symbol, curprice=curprice)




    else:
        return buy()




@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    bought = db.execute("SELECT compname, amount, price, totalprice, date FROM bought WHERE id is ?", session.get("user_id"))
    sold = db.execute("SELECT compname, amount, price, totalprice, date FROM sold WHERE id is ?", session.get("user_id"))

    compname = []
    price = []
    amount = []
    totalprice = []
    date = []
    x = len(bought)
    for i in range(len(bought)):
        for k, v in bought[i].items():
            if k == 'compname':
                compname.append(v)
            if k == 'price':
                price.append(v)
            if k == 'amount':
                amount.append(v)
            if k == 'totalprice':
                totalprice.append(v)
            if k == 'date':
                date.append(v)
    compname2 = []
    price2 = []
    amount2 = []
    totalprice2 = []
    date2 = []
    y = len(sold)
    for i in range(len(sold)):
        for k, v in sold[i].items():
            if k == 'compname':
                compname2.append(v)
            if k == 'price':
                price2.append(v)
            if k == 'amount':
                amount2.append(v)
            if k == 'totalprice':
                totalprice2.append(v)
            if k == 'date':
                date2.append(v)
    return render_template("history.html", compname=compname, price=price, amount=amount, totalprice=totalprice, date=date, x=x, y=y, compname2=compname2, price2=price2, amount2=amount2, totalprice2=totalprice2, date2=date2)




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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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
    if request.method == "GET":
        return render_template("quote.html")
    else:
        try:
            if request.form.get("symbol"):
                symbol = lookup(request.form.get("symbol"))
                return render_template("quoted.html", symbol=symbol)
            elif request.form.get("symbol") == "":
                return apology("Can't be empty")
        except:
            return apology("There is no such company in the database.")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        username = request.form.get("username")
        passconf = request.form.get("password")
        confpass = request.form.get("confirmation")
        password = generate_password_hash(request.form.get("password"))

        if username == "":
            return apology("Username can't be blank.")
        elif db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username")):
            return apology("Username already taken.")
        elif passconf == "":
            return apology("Password can't be blank.")
        if passconf != confpass:
            return apology("Passwords don't match.")

        else:
            db.execute("INSERT INTO users(username, hash) VALUES(?, ?)", username, password)
            return render_template("regsuccess.html")
    else:
        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""


    if request.method == "GET":
        compnames = []
        names = db.execute("SELECT compname FROM buy WHERE id is ?", session.get("user_id"))
        for n in names:
            for k, v in n.items():
                compnames.append(v)
        count = len(compnames)
        return render_template("sell.html", compnames=compnames, count=count)

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")


        if shares != "":
            check = lookup(request.form.get("symbol"))
            if int(shares) < 0:
                return apology("Must be a positive number")

            total = db.execute("SELECT amount FROM buy WHERE compname is ? AND id is ?", symbol, session.get("user_id"))
            price = db.execute("SELECT totalprice FROM buy WHERE compname is ? AND id is ?", symbol, session.get("user_id"))
            for i in price:
                for k, v in i.items():
                    price = v
            for i in total:
                for k, v in i.items():
                    totalshare = v
            for i, k in check.items():
                if i == 'price':
                    curprice = k
            if totalshare < int(shares):
                return apology("You can't sell more shares than you own")
            update = totalshare - int(shares)
            updateprice = price - curprice*int(shares)
            x = datetime.datetime.now()

            if symbol and shares:
                if totalshare > int(shares):
                    db.execute("INSERT INTO sold (id, username, compname, price, amount, totalprice, date) SELECT id, username, compname, price, ?, totalprice, ? FROM buy WHERE compname is ? AND id is ?", int(shares), x , symbol, session.get("user_id"))
                    db.execute("UPDATE buy SET amount = ? WHERE compname is ? AND id is ?", update, symbol, session.get("user_id"))
                    db.execute("UPDATE buy SET totalprice = ? WHERE compname is ? AND id is ?", updateprice , symbol, session.get("user_id"))

                if totalshare == int(shares):
                    db.execute("INSERT INTO sold (id, username, compname, price, amount, totalprice, date) SELECT id, username, compname, price, amount, totalprice, ? FROM buy WHERE compname is ? AND id is ?", x, symbol, session.get("user_id"))
                    db.execute("DELETE FROM buy WHERE compname is ? AND id is ?", symbol, session.get("user_id"))

                usercash = db.execute("SELECT cash FROM users WHERE id is ?", session.get("user_id"))
                for i in usercash:
                    for k, v in i.items():
                        userscash = v


                newcash = userscash + curprice * int(shares)
                db.execute("UPDATE users SET cash = ? WHERE id is ?", newcash, session.get("user_id"))
                return redirect("/")
        else:
            return apology("Can't be empty")


        return render_template("sell.html", symbol=symbol, shares=shares)



