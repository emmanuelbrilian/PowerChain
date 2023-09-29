from functools import wraps
from flask import flash, redirect, session

from user.model import User

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Unauthorized, please login", "danger")
            return redirect("/login")

    return wrap

def get_active_user():
    json = session["user"]
    return User.fromJson(json)

def set_active_user(user: User):
    session["logged_in"] = True
    session["username"] = user.username
    session["user"] = user.toJson()
