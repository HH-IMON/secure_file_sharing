"""Profile and security routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from app.extensions import db
from app.services.auth_service import verify_password, hash_password, validate_password_strength
from app.services.key_service import derive_key_from_password
from app.services.audit_service import get_user_activity, log_event
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

profile_bp = Blueprint('profile', __name__)

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

@profile_bp.route('/')
@login_required
def profile():
    return render_template('profile/profile.html', user=current_user)

@profile_bp.route('/security', methods=['GET', 'POST'])
@login_required
def security():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not verify_password(current_user.password_hash, form.current_password.data):
            flash('Current password is incorrect.', 'danger')
            return redirect(url_for('profile.security'))
            
        if not validate_password_strength(form.new_password.data):
            flash('New password does not meet strength requirements.', 'danger')
            return redirect(url_for('profile.security'))
            
        if '_pk_key' not in session:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))
            
        try:
            old_derived_key = bytes.fromhex(session['_pk_key'])
            
            iv = base64.b64decode(current_user.private_key_nonce)
            ciphertext = base64.b64decode(current_user.encrypted_private_key)
            cipher = Cipher(algorithms.AES(old_derived_key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            private_key_pem = decryptor.update(ciphertext) + decryptor.finalize()
            
            new_salt = os.urandom(16)
            new_derived_key = derive_key_from_password(form.new_password.data, new_salt)
            
            new_iv = os.urandom(16)
            cipher_new = Cipher(algorithms.AES(new_derived_key), modes.CBC(new_iv))
            encryptor = cipher_new.encryptor()
            new_ciphertext = encryptor.update(private_key_pem) + encryptor.finalize()
            
            current_user.password_hash = hash_password(form.new_password.data)
            current_user.private_key_salt = base64.b64encode(new_salt).decode('utf-8')
            current_user.private_key_nonce = base64.b64encode(new_iv).decode('utf-8')
            current_user.encrypted_private_key = base64.b64encode(new_ciphertext).decode('utf-8')
            
            db.session.commit()
            
            session['_pk_key'] = new_derived_key.hex()
            
            log_event('password_changed', user_id=current_user.id)
            flash('Password updated successfully.', 'success')
            return redirect(url_for('profile.security'))
            
        except Exception as e:
            flash(f'Error updating password: {str(e)}', 'danger')
            
    recent_logs = get_user_activity(current_user.id, limit=5)
    return render_template('profile/security.html', user=current_user, recent_logs=recent_logs, form=form)
