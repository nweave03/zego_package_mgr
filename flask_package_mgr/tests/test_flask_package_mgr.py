import os
import tempfile
import pytest
from flask_package_mgr import flask_package_mgr
from flask import json
import flask_package_mgr.response_codes as response_codes

@pytest.fixture
def client(request):
    db_fd, flask_package_mgr.app.config['DATABASE'] = tempfile.mkstemp()
    flask_package_mgr.app.config['TESTING'] = True
    client = flask_package_mgr.app.test_client()
    with flask_package_mgr.app.app_context():
        flask_package_mgr.init_db()

    def teardown():
        os.close(db_fd)
        os.unlink(flask_package_mgr.app.config['DATABASE'])
    request.addfinalizer(teardown)

    return client

def test_list_users(client):
    """ initialized with 0 users """
    r = client.get('/admin/user_list')
    assert r.status_code == 200
    assert b'[]' in r.data


def test_add_user(client):
    adduser = {
        'username' : 'nweaver',
        'password' : 'password'
        }
        
    r = client.post(
            '/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    assert r.status_code == 200
    adduser = {
        'username' : 'johndoe',
        'password' : 'jdoe0123'
        }

    r = client.post(
            '/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    assert r.status_code == 200
    r = client.get(
            '/admin/user_list',
            content_type='application/json',
            follow_redirects=True
            )
    assert r.status_code == 200
    response_dict = json.loads(r.data)

    found_nweaver = False
    found_johndoe = False
    for user_dict in response_dict:
        assert b'username' in user_dict
        assert b'password' in user_dict
        assert b'apikey' in user_dict
        assert b'id' in user_dict
        if 'nweaver' == user_dict['username']:
            assert b'password' in user_dict['password']
            assert b'ApiKey' in user_dict['apikey']
            assert 1 == user_dict['id']
            found_nweaver = True
        if 'johndoe' == user_dict['username']:
            assert b'jdoe0123' in user_dict['password']
            assert b'ApiKey' in user_dict['apikey']
            assert 2 == user_dict['id']
            found_johndoe = True

    assert True == found_nweaver
    assert True == found_johndoe

def test_duplicate_user_add(client):
    adduser = {
        'username' : 'nweaver',
        'password' : 'password'
        }
        
    r = client.post(
            '/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    assert 200 == r.status_code
    r = client.post(
            '/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    response_dict = json.loads(r.data)
    
    assert r.status_code == response_codes.CONFLICT
    assert b'username is already in use' in r.data
    r = client.get(
            '/admin/user_list',
            content_type='application/json',
            follow_redirects=True
            )
    assert 200 == r.status_code
    response_dict = json.loads(r.data)

    found_nweaver = False
    for user_dict in response_dict:
        assert b'username' in user_dict
        assert b'password' in user_dict
        assert b'apikey' in user_dict
        assert b'id' in user_dict
        if 'nweaver' == user_dict['username']:
            assert b'password' in user_dict['password']
            assert b'ApiKey' in user_dict['apikey']
            assert 1 == user_dict['id']
            found_nweaver = True

    assert True == found_nweaver
