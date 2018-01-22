import re
import io
import os
import shutil
import tempfile
import pytest
from flask_package_mgr import flask_package_mgr
from flask import json
import flask_package_mgr.response_codes as response_codes
from cStringIO import StringIO

@pytest.fixture
def client(request):
    db_fd, flask_package_mgr.app.config['DATABASE'] = tempfile.mkstemp()
    flask_package_mgr.app.config['TESTING'] = True
    client = flask_package_mgr.app.test_client()
    with flask_package_mgr.app.app_context():
        flask_package_mgr.init_db()
        uploads_folder = flask_package_mgr.app.config['UPLOAD_FOLDER']
        if not os.path.exists(uploads_folder):
            os.mkdir(uploads_folder)
        for package_files in os.listdir(uploads_folder):
            file_path = os.path.join(uploads_folder, package_files)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)

    def teardown():
        os.close(db_fd)
        os.unlink(flask_package_mgr.app.config['DATABASE'])
    request.addfinalizer(teardown)

    return client

def add_base_user(client):
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
  
def add_base_user_and_get_token(client):
    add_base_user(client)
    get_token_data = {
        'username' : 'nweaver',
        'password' : 'password'
        }

    r = client.post(
            '/user/get_token',
            data=json.dumps(get_token_data),
            content_type='application/json',
            follow_redirects=True
            )
    assert 200 == r.status_code
    response_dict = json.loads(r.data)

    assert b'token' in response_dict
    return response_dict['token']


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

def test_get_token(client):
    add_base_user(client)

    get_token_data = {
        'username' : 'nweaver',
        'password' : 'password'
        }

    r = client.post(
            '/user/get_token',
            data=json.dumps(get_token_data),
            content_type='application/json',
            follow_redirects=True
            )
    assert 200 == r.status_code
    response_dict = json.loads(r.data)

    assert b'token' in response_dict
    assert b'aValidToken' in response_dict['token']

def test_get_token_fail_bad_pass(client):
    add_base_user(client)

    get_token_data = {
        'username' : 'nweaver',
        'password' : 'password1'
        }

    r = client.post(
            '/user/get_token',
            data=json.dumps(get_token_data),
            content_type='application/json',
            follow_redirects=True
            )
    assert response_codes.UNAUTHORIZED == r.status_code
    assert b'password is incorrect' in r.data

def test_get_token_fail_no_pass(client):
    add_base_user(client)

    get_token_data = {
        'username' : 'nweaver'
        }

    r = client.post(
            '/user/get_token',
            data=json.dumps(get_token_data),
            content_type='application/json',
            follow_redirects=True
            )
    assert response_codes.INVALID_USE == r.status_code
    assert b'password is required' in r.data

def test_get_token_fail_no_user(client):
    add_base_user(client)

    get_token_data = {
        'password' : 'password'
        }

    r = client.post(
            '/user/get_token',
            data=json.dumps(get_token_data),
            content_type='application/json',
            follow_redirects=True
            )
    assert response_codes.INVALID_USE == r.status_code
    assert b'username is required' in r.data


def test_invalidate_token(client):
    token = add_base_user_and_get_token(client)

    token_data = { 'token' : token }
    invalidate_token_data = { 
        'username' : 'nweaver',
        'password' : 'password'
        }
    r = client.post(
            '/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert 200 == r.status_code
    assert b'token has been revoked' in r.data

def test_invalidate_token_fail_invalid_token(client):
    token = add_base_user_and_get_token(client)

    token_data = { 'token' : 'anInvalidToken' }
    invalidate_token_data = { 
        'username' : 'nweaver',
        'password' : 'password'
        }
    r = client.post(
            '/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.UNAUTHORIZED == r.status_code
    assert b'Invalid Token' in r.data

def test_invalidate_token_fail_no_token(client):
    token = add_base_user_and_get_token(client)

    invalidate_token_data = { 
        'username' : 'nweaver',
        'password' : 'password'
        }

    r = client.post(
            '/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.UNAUTHORIZED == r.status_code
    assert b'Token not provided' in r.data


def test_invalidate_token_fail_bad_password(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }
    invalidate_token_data = { 
        'username' : 'nweaver',
        'password' : 'password1'
        }
    r = client.post(
            '/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.UNAUTHORIZED == r.status_code
    assert b'password is incorrect' in r.data

def test_invalidate_token_fail_bad_username_in_token(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : 'aValidToken-invalidusername' }
    invalidate_token_data = { 
        'username' : 'nweaver',
        'password' : 'password'
        }
    r = client.post(
            '/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.UNAUTHORIZED == r.status_code
    assert b'Unable to find user' in r.data

def test_file_post(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : "test",
            "tag" : "1.0"
            }

    filename = 'test.txt'
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()

    files = {
        'file' : (open(filename, 'rb'), filename),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }
    print "files is {f}".format(f=files)

    r = client.post(
            '/packages',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

    get_data = {}
        

    r = client.get(
            '/packages',
            headers=token_data,
            data = json.dumps(get_data),
            content_type='application/json'
            )
    
    assert 200==r.status_code
    assert 'test' in r.data

    get_data = {'search' : 'tes'}

    r = client.get(
            '/packages',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    assert 200==r.status_code
    assert 'test' in r.data

    get_data = {'search' : 'unknown'}

    r = client.get(
            '/packages',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    assert 200==r.status_code
    assert 'test' not in r.data

def add_package(client, token, package_name, tag, new_filename='test.txt'):
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : package_name,
            "tag" : tag
            }

    filename = 'test.txt'
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()
    files = {
        'file' : (open(filename, 'rb'), new_filename),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }
    print "files is {f}".format(f=files)

    r = client.post(
            '/packages',
            headers=token_data,
            data=files
            )
    print "{r} : {d}".format(r=r.status_code, d=r.data)
    return r;

def search_package(client, token, package_search):
    token_data = { 'token' : token }
 
    get_data = {}
    if package_search is not None:
        get_data = {'search' : package_search}


    r = client.get(
            '/packages',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    print "{r} : {d}".format(r=r.status_code, d=r.data)
   

def test_multi_post(client):
    token = add_base_user_and_get_token(client)
    add_package(client, token, 'test', '1.0')
    
    r = add_package(client, token, 'test', '1.1', 'test2.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1
    r = add_package(client, token, 'test', '1.2', 'test3.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1
   
    r = search_package(client, token, 'tes')

def test_multi_post_fail(client):
    token = add_base_user_and_get_token(client)
    add_package(client, token, 'test', '1.0')
    
    r = add_package(client, token, 'test', '1.0', 'test2.txt')

    assert response_codes.CONFLICT == r.status_code
    assert 'tag is already in use' in r.data

    r = add_package(client, token, 'test', '1.1', 'test2.txt')

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1


    r = add_package(client, token, 'test', '1.1', 'test2.txt')

    assert response_codes.CONFLICT == r.status_code
    assert 'filename exists' in r.data

    r = add_package(client, token, 'test', '1.2', 'test2.txt')
    
    assert response_codes.CONFLICT == r.status_code
    assert 'filename exists' in r.data

    r = add_package(client, token, 'test', '1.3', 'test3.txt')

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1


