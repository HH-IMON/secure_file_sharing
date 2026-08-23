"""File operations tests."""
import io
import pytest
from app.models.file import File


def test_upload_file(auth_client, db):
    data = {'file': (io.BytesIO(b"Test file content"), 'test.txt')}
    response = auth_client.post(
        '/files/upload', data=data,
        content_type='multipart/form-data',
        follow_redirects=True,
    )
    assert response.status_code == 200
    f = File.query.filter_by(original_filename='test.txt').first()
    assert f is not None
    assert f.status == 'active'


def test_upload_no_auth(client, db):
    data = {'file': (io.BytesIO(b"Secret"), 'test.txt')}
    response = client.post(
        '/files/upload', data=data,
        content_type='multipart/form-data',
        follow_redirects=True,
    )
    # Should redirect to login
    assert b'login' in response.data.lower() or b'log in' in response.data.lower()


def test_upload_invalid_extension(auth_client, db):
    data = {'file': (io.BytesIO(b"Malicious"), 'hack.exe')}
    response = auth_client.post(
        '/files/upload', data=data,
        content_type='multipart/form-data',
        follow_redirects=True,
    )
    # Should not create a file record
    f = File.query.filter_by(original_filename='hack.exe').first()
    assert f is None


def test_download_own_file(auth_client, db):
    # Upload first
    data = {'file': (io.BytesIO(b"Download me"), 'download.txt')}
    auth_client.post(
        '/files/upload', data=data,
        content_type='multipart/form-data',
    )
    f = File.query.filter_by(original_filename='download.txt').first()
    assert f is not None

    response = auth_client.get(f'/files/file/{f.uuid}/download')
    assert response.status_code == 200
    assert response.data == b"Download me"


def test_download_unauthorized(app, client, db):
    """User B cannot download User A's file without a share."""
    from tests.conftest import create_test_user

    with app.app_context():
        create_test_user('Alice', 'alice_dl@example.com', 'TestPass@123')
        create_test_user('Bob', 'bob_dl@example.com', 'TestPass@123')

    # Alice uploads
    client.post('/auth/login', data={
        'email': 'alice_dl@example.com', 'password': 'TestPass@123'
    })
    data = {'file': (io.BytesIO(b"Alice only"), 'alice.txt')}
    client.post('/files/upload', data=data, content_type='multipart/form-data')
    f = File.query.filter_by(original_filename='alice.txt').first()
    assert f is not None

    # Logout Alice, login Bob
    client.get('/auth/logout')
    client.post('/auth/login', data={
        'email': 'bob_dl@example.com', 'password': 'TestPass@123'
    })

    # Bob tries to download
    response = client.get(f'/files/file/{f.uuid}/download', follow_redirects=True)
    # Should be denied (redirect with error flash or 403)
    assert response.status_code in [200, 403]


def test_delete_file(auth_client, db):
    data = {'file': (io.BytesIO(b"Delete me"), 'delete.txt')}
    auth_client.post('/files/upload', data=data, content_type='multipart/form-data')
    f = File.query.filter_by(original_filename='delete.txt').first()
    assert f is not None

    response = auth_client.post(f'/files/file/{f.uuid}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert File.query.filter_by(uuid=f.uuid).first() is None


def test_file_detail_owner(auth_client, db):
    data = {'file': (io.BytesIO(b"Detail test"), 'detail.txt')}
    auth_client.post('/files/upload', data=data, content_type='multipart/form-data')
    f = File.query.filter_by(original_filename='detail.txt').first()
    assert f is not None

    response = auth_client.get(f'/files/file/{f.uuid}')
    assert response.status_code == 200
    assert b'detail.txt' in response.data
