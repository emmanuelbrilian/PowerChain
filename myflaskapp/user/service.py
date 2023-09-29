from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from wtforms import (
    Form,
    StringField,
    PasswordField,
    validators,
    StringField,
    validators,
)
from passlib.hash import sha256_crypt


from user.model import User
from util.session import get_active_user, is_logged_in, set_active_user


user_service = Blueprint("order", __name__, template_folder="../templates")


class RegisterForm(Form):
    name = StringField("Name", [validators.Length(min=1, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.EqualTo("confirm", message="Password Do Not Match"),
        ],
    )
    confirm = PasswordField("Confirm Password")
    # Modify the field for coordinates
    coordinates = StringField("Coordinates", [validators.DataRequired()])


@user_service.route("/register", methods=["GET"])
def open_register_page():
    form = RegisterForm(request.form)
    return render_template("register.html", form=form)


@user_service.route("/register", methods=["POST"])
def register():
    form = RegisterForm(request.form)
    if not form.validate():
        flash("Form is not valid", "danger")
        return render_template("register.html", form=form)

    email = form.email.data
    if User.is_email_registered(email):
        flash("Email already registered. Please use a different email.", "danger")
        return render_template("register.html", form=form)

    name = form.name.data
    username = form.username.data
    password = sha256_crypt.encrypt(str(form.password.data))
    user_coordinate = form.coordinates.data

    bcaddress = User.get_ethereum_account()

    user = User(username, password, email, name, user_coordinate, bcaddress)
    user.save()

    flash("You are now registered and can log in", "success")
    return redirect(url_for("index"))


@user_service.route("/login", methods=["GET"])
def open_login_page():
    return render_template("login.html")


@user_service.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    try:
        user = User.get_login_user(username, password)
        set_active_user(user)
        flash("You are now logged in", "success")
        return redirect(url_for("dashboard"))
    except Exception as e:
        error = "invalid login"
        return render_template("login.html", error=error)


@user_service.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("You are now logged out", "success")
    return redirect(url_for("login"))


@user_service.route("/peers", methods=["GET"])
@is_logged_in
def peers():
    users = User.get_all()
    return render_template("peers.html", users=users)


@user_service.route("/dashboard", methods=["GET"])
@is_logged_in
def open_dashboard_page():
    user = get_active_user()
    return render_template("dashboard.html", user=user)
