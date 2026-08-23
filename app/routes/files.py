"""File management routes."""
import io
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, session
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import SubmitField
from app.extensions import limiter, db
from app.models import File, FileShare
from app.services.file_service import save_encrypted_file, get_file_for_download, delete_file, get_user_files
from app.services.sharing_service import get_file_shares
from app.services.audit_service import log_event

files_bp = Blueprint('files', __name__)

class UploadForm(FlaskForm):
    file = FileField('Select File', validators=[FileRequired()])
    submit = SubmitField('Upload')

@files_bp.route('/')
@login_required
def my_files():
    files = get_user_files(current_user)
    return render_template('files/my_files.html', files=files)

@files_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@limiter.limit("10/minute")
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        if '_pk_key' not in session:
            flash('Session expired. Please log in again.', 'danger')
            return redirect(url_for('auth.login'))
        try:
            file_obj = form.file.data
            from app.services.file_service import validate_file
            is_valid, msg = validate_file(file_obj)
            if not is_valid:
                flash(msg, 'danger')
                return render_template('files/upload.html', form=form)
                
            save_encrypted_file(file_obj, current_user, session['_pk_key'])
            log_event('file_uploaded', user_id=current_user.id)
            flash('File uploaded and encrypted successfully.', 'success')
            return redirect(url_for('files.my_files'))
        except Exception as e:
            log_event('file_upload_failed', user_id=current_user.id, details={'error': str(e)})
            flash(f'Error uploading file: {str(e)}', 'danger')
    return render_template('files/upload.html', form=form)

@files_bp.route('/file/<uuid>')
@login_required
def file_detail(uuid):
    file = File.query.filter_by(uuid=uuid).first_or_404()
    is_owner = file.owner_id == current_user.id
    
    shares = []
    if is_owner:
        shares = get_file_shares(uuid, current_user)
    else:
        active_share = FileShare.query.filter_by(file_id=file.id, recipient_id=current_user.id).first()
        if not active_share or not active_share.is_active:
            flash('You do not have permission to view this file.', 'danger')
            return redirect(url_for('dashboard.index'))
            
    verification = {
        'plaintext_hash': file.plaintext_hash,
        'ciphertext_hash': file.ciphertext_hash,
        'signature': file.signature
    }
    return render_template('files/file_detail.html', file=file, shares=shares, is_owner=is_owner, verification=verification)

@files_bp.route('/file/<uuid>/download')
@login_required
def download(uuid):
    if '_pk_key' not in session:
        flash('Session expired. Please log in again.', 'danger')
        return redirect(url_for('auth.login'))
    try:
        decrypted_data, original_filename, metadata = get_file_for_download(uuid, current_user, session['_pk_key'])
        
        file = File.query.filter_by(uuid=uuid).first_or_404()
        if file.owner_id != current_user.id:
            share = FileShare.query.filter_by(file_id=file.id, recipient_id=current_user.id).first()
            if share and share.one_time_download:
                share.downloaded = True
                db.session.commit()
                
        log_event('file_downloaded', user_id=current_user.id, resource_type='file', resource_id=file.id)
        
        return send_file(
            io.BytesIO(decrypted_data),
            as_attachment=True,
            download_name=original_filename,
            mimetype=file.mime_type
        )
    except Exception as e:
        log_event('file_download_failed', user_id=current_user.id, details={'error': str(e)})
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('files.my_files'))

@files_bp.route('/file/<uuid>/delete', methods=['POST'])
@login_required
def delete(uuid):
    try:
        if delete_file(uuid, current_user):
            log_event('file_deleted', user_id=current_user.id)
            flash('File deleted successfully.', 'success')
        else:
            flash('Error deleting file.', 'danger')
    except Exception as e:
        flash(f'Error deleting file: {str(e)}', 'danger')
    return redirect(url_for('files.my_files'))
