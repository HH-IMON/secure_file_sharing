"""File sharing routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, StringField, BooleanField, SubmitField
from wtforms.validators import Optional
from app.models import File, User
from app.services.sharing_service import share_file, get_shares_for_recipient, revoke_share
from app.services.audit_service import log_event
from datetime import datetime

sharing_bp = Blueprint('sharing', __name__)

class ShareForm(FlaskForm):
    recipient = SelectField('Recipient', coerce=int)
    permission = SelectField('Permission', choices=[('download','Download'),('view','View Only')])
    message = TextAreaField('Message (Optional)', validators=[Optional()])
    expires_at = StringField('Expiration (YYYY-MM-DDTHH:MM)', validators=[Optional()], description='YYYY-MM-DDTHH:MM')
    one_time_download = BooleanField('One-Time Download')
    submit = SubmitField('Share File')

@sharing_bp.route('/share/<file_uuid>', methods=['GET', 'POST'])
@login_required
def share(file_uuid):
    file = File.query.filter_by(uuid=file_uuid, owner_id=current_user.id).first_or_404()
    
    users = User.query.filter(User.id != current_user.id, User.is_active == True).all()
    form = ShareForm()
    form.recipient.choices = [(u.id, f"{u.name} ({u.email})") for u in users]
    
    if form.validate_on_submit():
        if '_pk_key' not in session:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))
            
        expires_at_dt = None
        if form.expires_at.data:
            try:
                expires_at_dt = datetime.strptime(form.expires_at.data, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash('Invalid expiration date format.', 'danger')
                return render_template('sharing/share_file.html', file=file, form=form, users=users)
                
        try:
            share_file(
                file_uuid=file_uuid,
                sender=current_user,
                recipient_id=form.recipient.data,
                permission=form.permission.data,
                expires_at=expires_at_dt,
                message=form.message.data,
                one_time=form.one_time_download.data,
                derived_key_hex=session['_pk_key']
            )
            log_event('file_shared', user_id=current_user.id, resource_type='file', resource_id=file.id)
            flash('File shared successfully.', 'success')
            return redirect(url_for('files.file_detail', uuid=file_uuid))
        except Exception as e:
            flash(f'Error sharing file: {str(e)}', 'danger')
            
    return render_template('sharing/share_file.html', file=file, form=form, users=users)

@sharing_bp.route('/shared-with-me')
@login_required
def shared_with_me():
    shares = get_shares_for_recipient(current_user)
    return render_template('files/shared_with_me.html', shared_items=shares)

@sharing_bp.route('/<share_uuid>/revoke', methods=['POST'])
@login_required
def revoke(share_uuid):
    try:
        if revoke_share(share_uuid, current_user):
            log_event('share_revoked', user_id=current_user.id)
            flash('Share revoked successfully.', 'success')
        else:
            flash('Unable to revoke share.', 'danger')
    except Exception as e:
        flash(f'Error revoking share: {str(e)}', 'danger')
    return redirect(request.referrer or url_for('dashboard.index'))
