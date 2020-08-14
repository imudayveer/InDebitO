# MIT License

# Copyright (c) 2020 imudayveer

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from flask import Flask, flash, render_template, request, redirect, session
from cs50 import SQL
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from flask_session import Session
import json

from helpers import sorry, login_required, inr


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
app.jinja_env.filters["inr"] = inr

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")


# Show all recent transactions and charts
@app.route("/")
@login_required
def index():    
    # Query database for transactions
    trans_db = db.execute("SELECT * FROM 'transaction' WHERE user_id = :user_id ORDER BY date_time DESC",
                            user_id = session["user_id"])

    # Dict and some values
    category_dict_e = {}
    source_dict_e = {}
    grand_total_i = 0
    grand_total_e = 0

    # Iterating db for Income
    for i in trans_db:
        if i["trans_type"] == 'Income':
            grand_total_i += i["amount"]

    # Iterating db for Expense and Dict (required by Google Charts API)
    for i in trans_db:
        if i["trans_type"] == 'Expense':
            grand_total_e += i["amount"]

            if i["category"] not in category_dict_e:
                category_dict_e[i["category"]] = i["amount"]
            else:
                category_dict_e[i["category"]] = category_dict_e[i["category"]] + i["amount"]
            
            if i["source"] not in source_dict_e:
                source_dict_e[i["source"]] = i["amount"]
            else:
                source_dict_e[i["source"]] = source_dict_e[i["source"]] + i["amount"]

    return render_template("index.html", trans_db = trans_db, inr = inr, grand_total_e = grand_total_e, grand_total_i = grand_total_i, category_dict_e = category_dict_e, source_dict_e = source_dict_e)


# Log user in
@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("usrnm"):
            return sorry("must provide username", 403)
        elif not request.form.get("pwd"):
            return sorry("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM 'users' WHERE username = :username",
                          username=request.form.get("usrnm"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("pwd")):
            return sorry("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Flash a message
        flash("Welcome Back!!!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("usrnm"):
            return sorry("must provide username", 403)
        elif not request.form.get("pwd"):
            return sorry("must provide password", 403)
        elif not request.form.get("pwd_con"):
            return sorry("must provide password(confirm)", 403)

        # Password checking
        if request.form.get("pwd") != request.form.get("pwd_con"):
            return sorry("passwords didn't matched") 

        # Hashing password and adding it in database
        password_hashed = generate_password_hash(request.form.get("pwd"))
        register_new_user = db.execute("INSERT INTO 'users' (username, hash) VALUES (:usrnm, :hash)",
                            usrnm=request.form.get("usrnm"),
                            hash=password_hashed)

        # Checks if username available             
        if not register_new_user:
            return sorry("username taken")

        # Log in
        session["user_id"] = register_new_user

        # Flash a message
        flash("Registered Successfully!!!")

        # Redirect user to home page
        return redirect("/")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


# Log user out
@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# Adding expense
@app.route("/expense", methods=["GET", "POST"])
@login_required
def expense():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("s_p"):
            return sorry("must provide shop/person")
        elif not request.form.get("amount"):
            return sorry("must provide amount")

        # Insert values in database
        trans_db = db.execute("INSERT INTO 'transaction' (user_id, trans_type, source, category, s_p, amount, remarks) VALUES (:user_id, :trans_type, :source, :category, :s_p, :amount, :remarks)",
                                user_id = session["user_id"],
                                trans_type = "Expense",
                                source = request.form.get("source"),
                                category = request.form.get("category"),
                                s_p = request.form.get("s_p"),
                                amount = request.form.get("amount"),
                                remarks = request.form.get("remarks"))

        # Flash a message
        flash("Transaction added successfully!!!")

        # Redirect user to home page
        return redirect("/")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("expense.html")


# Adding Income
@app.route("/income", methods=["GET", "POST"])
@login_required
def income():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("amount"):
            return sorry("must provide amount")

        # Insert values in database
        trans_db = db.execute("INSERT INTO 'transaction' (user_id, trans_type, source, category, s_p, amount, remarks) VALUES (:user_id, :trans_type, :source, :category, :s_p, :amount, :remarks)",
                                user_id = session["user_id"],
                                trans_type = "Income",
                                source = request.form.get("source"),
                                category = request.form.get("category"),
                                s_p = "-",
                                amount = request.form.get("amount"),
                                remarks = request.form.get("remarks"))

        # Flash a message
        flash("Transaction added successfully!!!")

        # Redirect user to home page
        return redirect("/")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("income.html")


# Render profile main page
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


# Changing username
@app.route("/changeusername", methods=["GET", "POST"])
@login_required
def changeusername():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("new_usrnm"):
            return sorry("must provide input")

        # Checks if username already available 
        check_usrnm = db.execute("SELECT * FROM 'users' WHERE username = :usrnm",
                                    usrnm=request.form.get("new-usrnm"))
        # Returns sorry if yes
        if check_usrnm:
            return sorry("username taken")

        # Update new username in database
        new_usrnm = db.execute("UPDATE 'users' SET username = :usrnm",
                                usrnm=request.form.get("new_usrnm"))
        
        # Flash a message
        flash("Username Changed Successfully!!!")
        
        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changeusername.html")


# Changing passowrd
@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("old_pwd") or not request.form.get("new_pwd") or not request.form.get("new_pwd_con"):
            return sorry("fill all fields")

        # Password checking
        if request.form.get("new_pwd") != request.form.get("new_pwd_con"):
            return sorry("confirmation error")

        # Query db for user id
        rows = db.execute("SELECT * FROM users WHERE id = :id",
                            id = session["user_id"])

        # Ensure old password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("old_pwd")):
            return sorry("old password wrong")

        # Hashing new password and adding it in database
        password_hashed = generate_password_hash(request.form.get("new_pwd"))
        db.execute("UPDATE users SET hash = :hash WHERE id = :id",
                    hash = generate_password_hash(request.form.get("new_pwd")),
                    id = session["user_id"])
        
        # Flash a message
        flash("Password Changed!!!")

        # Redirect user to home page
        return redirect("/")
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("changepassword.html")


# Delete account
@app.route("/delaccapp", methods=["GET", "POST"])
@login_required
def delaccapp():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure everything was submitted
        if not request.form.get("approve"):
            return sorry("input required")
        if not request.form.get("approve") == "YES":
            return sorry("input error")

        # Deletes user from db
        db.execute("DELETE FROM 'users' WHERE id = :id",
                        id = session["user_id"]) 

        # Forget any user_id
        session.clear()

        # Flash a message (not-working)
        flash("Account Deleted!!!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("delaccapp.html")


# Render about page
@app.route("/about")
def about():
    return render_template("about.html")
        

# Search db for keywords
@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # Ensure everything was submitted
        if not request.form.get("search"):
            return sorry("input required")

        # Query database for keyword
        trans_db_search = db.execute("SELECT * FROM 'transaction' WHERE user_id = :user_id AND (trans_type LIKE :search OR source LIKE :search OR category LIKE :search OR s_p LIKE :search OR remarks LIKE :search) ORDER BY date_time DESC",
                            search = "%" + request.form.get("search") + "%",
                            user_id = session["user_id"])

        # Returns a page with search results
        return render_template("searched.html", trans_db_search = trans_db_search, inr = inr)
    
    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("search.html")


# Handles error
def errorhandler(e):
    # Handle error
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return sorry(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)