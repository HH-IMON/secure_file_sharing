"""Authentication routes for the application."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.extensions import db, limiter
from app.models import User, LoginAttempt
from app.services.auth_service import register_user, authenticate_user
from app.services.audit_service import log_event
from app.utils.security import get_client_ip

auth_bp = Blueprint('auth', __name__)

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegisterForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Reset Password')

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user, derived_key_hex = authenticate_user(form.email.data, form.password.data)
        ip_address = get_client_ip()
        if user:
            login_user(user, remember=form.remember.data)
            session['_pk_key'] = derived_key_hex
            session.permanent = True
            log_event('login_success', user_id=user.id, details={'ip': ip_address})
            db.session.add(LoginAttempt(email=form.email.data, ip_address=ip_address, success=True))
            db.session.commit()
            return redirect(url_for('dashboard.index'))
        else:
            log_event('login_failure', details={'email': form.email.data, 'ip': ip_address})
            db.session.add(LoginAttempt(email=form.email.data, ip_address=ip_address, success=False))
            db.session.commit()
            flash('Invalid email or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3/minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            if User.query.filter_by(email=form.email.data).first():
                flash('Email already registered.', 'danger')
                return render_template('auth/register.html', form=form)
            user = register_user(form.name.data, form.email.data, form.password.data)
            log_event('user_registered', user_id=user.id)
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            flash(f"Registration failed: {str(e)}", 'danger')
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_event('logout', user_id=current_user.id)
    session.pop('_pk_key', None)
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        flash('If an account with that email exists, a password reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('auth/forgot_password.html', form=form)
