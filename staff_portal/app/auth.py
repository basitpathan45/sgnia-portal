from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length

from .extensions import db
from .audit import append_audit_log
from .models import User

auth_bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    email = StringField("Official staff email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("staff.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.active and user.check_password(form.password.data):
            login_user(user)
            append_audit_log(user, "login", "user", user.id, "Staff account signed in.")
            db.session.commit()
            next_page = request.args.get("next", "")
            if next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("staff.dashboard"))
        flash("Email or password is incorrect, or this account is inactive.", "danger")

    return render_template("login.html", form=form)


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        append_audit_log(current_user, "logout", "user", current_user.id, "Staff account signed out.")
        db.session.commit()
        logout_user()
    return redirect(url_for("auth.login"))
