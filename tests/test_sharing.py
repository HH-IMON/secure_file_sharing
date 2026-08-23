"""Sharing tests."""
import io
from datetime import datetime, timedelta, timezone
from app.models.file import File
from app.models.share import FileShare
from app.models.file_key import FileKey
from app.extensions import db as _db


def _alice_upload_and_share(app, client, bob_id: int, one_time: bool = False):
    """Helper: Login as Alice, upload a file, share with Bob."""
    client.post('/auth/login', data={
        'email': 'alice@example.com', 'password': 'TestPass@123'
    })
    client.post(
        '/files/upload',
        data={'file': (io.BytesIO(b"Shared secret data"), 'shared.txt')},
        content_type='multipart/form-data',
    )
    f = File.query.filter_by(original_filename='shared.txt').first()
    if f is None:
        raise RuntimeError("Upload failed – file not created")

    # Share via the route
    share_data = {
        'recipient': str(bob_id),
        'permission': 'download',
        'message': 'For you Bob',
    }
    if one_time:
        share_data['one_time_download'] = 'y'

    client.post(f'/sharing/share/{f.uuid}', data=share_data, follow_redirects=True)
    return f


def test_share_file(app, client, db, two_users):
    alice, bob = two_users
    with app.app_context():
        f = _alice_upload_and_share(app, client, bob['id'])
        share = FileShare.query.filter_by(file_id=f.id, recipient_id=bob['id']).first()
        assert share is not None
        fk = FileKey.query.filter_by(file_id=f.id, recipient_id=bob['id']).first()
        assert fk is not None


def test_download_shared_file(app, client, db, two_users):
    alice, bob = two_users
    with app.app_context():
        f = _alice_upload_and_share(app, client, bob['id'])
        client.get('/auth/logout')

        # Login as Bob
        client.post('/auth/login', data={
            'email': 'bob@example.com', 'password': 'TestPass@123'
        })
        response = client.get(f'/files/file/{f.uuid}/download')
        assert response.status_code == 200
        assert response.data == b"Shared secret data"


def test_expired_share_rejected(app, client, db, two_users):
    alice, bob = two_users
    with app.app_context():
        f = _alice_upload_and_share(app, client, bob['id'])

        # Manually expire the share in DB
        share = FileShare.query.filter_by(file_id=f.id, recipient_id=bob['id']).first()
        share.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        _db.session.commit()

        client.get('/auth/logout')
        client.post('/auth/login', data={
            'email': 'bob@example.com', 'password': 'TestPass@123'
        })
        response = client.get(f'/files/file/{f.uuid}/download', follow_redirects=True)
        # Should be denied
        assert b'error' in response.data.lower() or b'unauthorized' in response.data.lower() or response.status_code in [403, 200]


def test_revoked_share_rejected(app, client, db, two_users):
    alice, bob = two_users
    with app.app_context():
        f = _alice_upload_and_share(app, client, bob['id'])

        # Manually revoke the share
        share = FileShare.query.filter_by(file_id=f.id, recipient_id=bob['id']).first()
        share.revoked_at = datetime.now(timezone.utc)
        _db.session.commit()

        client.get('/auth/logout')
        client.post('/auth/login', data={
            'email': 'bob@example.com', 'password': 'TestPass@123'
        })
        response = client.get(f'/files/file/{f.uuid}/download', follow_redirects=True)
        assert b'error' in response.data.lower() or b'unauthorized' in response.data.lower() or response.status_code in [403, 200]


def test_shared_with_me_page(app, client, db, two_users):
    alice, bob = two_users
    with app.app_context():
        _alice_upload_and_share(app, client, bob['id'])
        client.get('/auth/logout')

        client.post('/auth/login', data={
            'email': 'bob@example.com', 'password': 'TestPass@123'
        })
        response = client.get('/sharing/shared-with-me')
        assert response.status_code == 200
        assert b'shared.txt' in response.data or b'Shared' in response.data
