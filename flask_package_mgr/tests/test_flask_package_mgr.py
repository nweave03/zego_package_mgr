from time import sleep
import re
import io
import os
import shutil
import tempfile
import pytest
import filecmp
from flask_package_mgr import flask_package_mgr
from flask import json
import flask_package_mgr.response_codes as response_codes
from cStringIO import StringIO

test_filenames=[
            'test.txt',
            'test2.txt',
            'test3.txt',
            'test4.txt',
            'test5.txt',
            'test6.txt'
            ]

@pytest.fixture
def client(request):
    db_fd, flask_package_mgr.app.config['DATABASE'] = tempfile.mkstemp()
    flask_package_mgr.app.config['TESTING'] = True
    client = flask_package_mgr.app.test_client()

    for test_file in test_filenames:
        if os.path.exists(test_file):
            os.unlink(test_file)

    for test_file in test_filenames:
        f = open(test_file, 'w')
        f.write("this is a test file {f}".format(f=test_file))
        f.close()

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
        for test_file in test_filenames:
            if os.path.exists(test_file):
                os.unlink(test_file)

        with flask_package_mgr.app.app_context():
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

    request.addfinalizer(teardown)

    return client

def add_base_user(client):
    adduser = {
        'username' : 'nweaver',
        'password' : 'password'
        }
        
    r = client.post(
            '/api/v1/user/add',
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
            '/api/v1/user/get_token',
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
    r = client.get('/api/v1/admin/user_list')
    assert r.status_code == 200
    assert b'[]' in r.data


def test_add_user(client):
    adduser = {
        'username' : 'nweaver',
        'password' : 'password'
        }
        
    r = client.post(
            '/api/v1/user/add',
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
            '/api/v1/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    assert r.status_code == 200
    r = client.get(
            '/api/v1/admin/user_list',
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
            '/api/v1/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    assert 200 == r.status_code
    r = client.post(
            '/api/v1/user/add',
            data=json.dumps(adduser),
            content_type='application/json',
            follow_redirects=True
            )
    response_dict = json.loads(r.data)
    
    assert r.status_code == response_codes.CONFLICT
    assert b'username is already in use' in r.data
    r = client.get(
            '/api/v1/admin/user_list',
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
            '/api/v1/user/get_token',
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
            '/api/v1/user/get_token',
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
            '/api/v1/user/get_token',
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
            '/api/v1/user/get_token',
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
            '/api/v1/user/invalidate_token',
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
            '/api/v1/user/invalidate_token',
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
            '/api/v1/user/invalidate_token',
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
            '/api/v1/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.UNAUTHORIZED == r.status_code
    assert b'password is incorrect' in r.data

def test_invalidate_token_fail_no_password(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }
    invalidate_token_data = { 
        'username' : 'nweaver'
        }
    r = client.post(
            '/api/v1/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.INVALID_USE == r.status_code
    assert b'password is required' in r.data

def test_invalidate_token_fail_no_username(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }
    invalidate_token_data = { 
        'password' : 'password'
        }
    r = client.post(
            '/api/v1/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.INVALID_USE == r.status_code
    assert b'username is required' in r.data

def test_invalidate_token_fail_bad_username(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }
    invalidate_token_data = { 
        'username' : 'invalidusername',
        'password' : 'password'
        }
    r = client.post(
            '/api/v1/user/invalidate_token',
            data=json.dumps(invalidate_token_data),
            headers=token_data,
            content_type='application/json',
            follow_redirects=True
            )
    
    assert response_codes.NOT_FOUND == r.status_code
    assert b'username not found' in r.data

def test_invalidate_token_fail_bad_username_in_token(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : 'aValidToken-invalidusername' }
    invalidate_token_data = { 
        'username' : 'nweaver',
        'password' : 'password'
        }
    r = client.post(
            '/api/v1/user/invalidate_token',
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

    filename = test_filenames[0]
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

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

    get_data = {}
        

    r = client.get(
            '/api/v1/packages',
            headers=token_data,
            data = json.dumps(get_data),
            content_type='application/json'
            )
    
    assert 200==r.status_code
    assert 'test' in r.data

    get_data = {'search' : 'tes'}

    r = client.get(
            '/api/v1/packages',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    assert 200==r.status_code
    assert 'test' in r.data

    get_data = {'search' : 'unknown'}

    r = client.get(
            '/api/v1/packages',
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

    filename = test_filenames[0]
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

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    return r;

def search_package(client, token, package_search):
    token_data = { 'token' : token }
 
    get_data = {}
    if package_search is not None:
        get_data = {'search' : package_search}


    r = client.get(
            '/api/v1/packages',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
   

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

def test_post_fail(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "tag" : "1.0" 
            }

    filename = test_filenames[0]
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()
    files = {
        'file' : (open(filename, 'rb'), 'test.txt'),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    assert response_codes.INVALID_USE == r.status_code
    assert "package_name is required" in r.data

def test_post_fail_2(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : "test" 
            }

    filename = test_filenames[0]
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()
    files = {
        'file' : (open(filename, 'rb'), 'test.txt'),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    assert response_codes.INVALID_USE == r.status_code
    assert "tag is required" in r.data

def test_post_fail_3(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : "test",
            "tag" : "1.0"
            }

    filename = test_filenames[0]
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()
    files = {
        'file' : (open(filename, 'rb'), 'test.xfd'),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    assert response_codes.INVALID_USE == r.status_code
    assert "file is not of type" in r.data

def test_post_fail_4(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : "tes/t",
            "tag" : "1.0"
            }

    filename = test_filenames[0]
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()
    files = {
        'file' : (open(filename, 'rb'), 'test.txt'),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    assert response_codes.INVALID_USE == r.status_code
    assert "package_name cannot contain" in r.data

def test_post_fail_5(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : "test",
            "tag" : "1.0/2"
            }

    filename = test_filenames[0]
    json_dumps = json.dumps(package_post_data) 

    json_dumps = re.sub(r'"',
                       r'\\"',
                       json_dumps
                       )    

    fd,tmp=tempfile.mkstemp()
    files = {
        'file' : (open(filename, 'rb'), 'test.txt'),
        'json' : (open(tmp, 'rb'), json_dumps, 'application/json')
        }

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    assert response_codes.INVALID_USE == r.status_code
    assert "tags cannot contain" in r.data



def test_file_package_post(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {
            "tag" : "1.0"
            }

    filename = test_filenames[0]
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

    r = client.post(
            '/api/v1/packages/test',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

def test_file_package_post(client):
    token = add_base_user_and_get_token(client)
    
    r = add_package(client, token, 'test', '1.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    token_data = {
            "token" : token
            }

    package_get_data = {
            "search_tag" : "1.0"
            }

    r = client.get(
            '/api/v1/packages/test',
            headers=token_data,
            data=json.dumps(package_get_data),
            content_type='application/json'
            )
    assert 200 == r.status_code
    assert '"tag": "1.0"' in r.data

def get_package_tag_info(client, token, package, search_term=None):
    token_data = { 'token' : token }
 
    get_data = {}
    if search_term is not None:
        get_data = {'tag_search' : search_term}


    r = client.get(
            "/api/v1/packages/{p}".format(p=package),
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    return r


def test_file_package_get(client):
    token = add_base_user_and_get_token(client)
    
    r = add_package(client, token, 'test', '1.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

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

    r = add_package(client, token, 'test', '2.0', 'test4.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package(client, token, 'test', '2.1', 'test5.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package(client, token, 'test', '3.0', 'test6.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package(client, token, 'foo', '1.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 2

    r = add_package(client, token, 'bar', '2.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 3


    r = get_package_tag_info(client, token, 'test')

    assert 200 == r.status_code
    assert '"tag": "1.0"' in r.data
    assert '"tag": "1.1"' in r.data
    assert '"tag": "1.2"' in r.data
    assert '"tag": "2.0"' in r.data
    assert '"tag": "2.1"' in r.data
    assert '"tag": "3.0"' in r.data
    resp = json.loads(r.data)
    assert len(resp) == 6


    r = get_package_tag_info(client, token, 'foo')

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "1.0"' in r.data

    r = get_package_tag_info(client, token, 'bar')

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "2.0"' in r.data

    r = get_package_tag_info(client, token, 'test', "1.")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 3
    assert '"tag": "1.0"' in r.data
    assert '"tag": "1.1"' in r.data
    assert '"tag": "1.2"' in r.data

    r = get_package_tag_info(client, token, 'test', "2.")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 2
    assert '"tag": "2.0"' in r.data
    assert '"tag": "2.1"' in r.data

    r = get_package_tag_info(client, token, 'test', "3.")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "3.0"' in r.data

    r = get_package_tag_info(client, token, 'test', ".0")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 3
    assert '"tag": "3.0"' in r.data
    assert '"tag": "2.0"' in r.data
    assert '"tag": "1.0"' in r.data

    r = get_package_tag_info(client, token, 'test', ".1")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 2
    assert '"tag": "2.1"' in r.data
    assert '"tag": "1.1"' in r.data

    r = get_package_tag_info(client, token, 'test', ".2")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "1.2"' in r.data

    r = get_package_tag_info(client, token, 'foo', ".5")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 0

    r = get_package_tag_info(client, token, 'foo', ".0")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "1.0"' in r.data

    r = get_package_tag_info(client, token, 'bar', ".0")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "2.0"' in r.data

    r = get_package_tag_info(client, token, 'bar', "5.0")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 0

def test_file_package_get_fail(client):
    token = add_base_user_and_get_token(client)
    
    r = add_package(client, token, 'test', '1.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

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

    r = add_package(client, token, 'test', '2.0', 'test4.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package(client, token, 'test', '2.1', 'test5.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package(client, token, 'test', '3.0', 'test6.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package(client, token, 'foo', '1.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 2

    r = add_package(client, token, 'bar', '2.0', 'test.txt')
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 3

    r = get_package_tag_info(client, token, 'unknown', "5.0")

    assert response_codes.NOT_FOUND == r.status_code
    assert 'could not locate package' in r.data

    r = get_package_tag_info(client, token, 'unknown')

    assert response_codes.NOT_FOUND == r.status_code
    assert 'could not locate package' in r.data

def test_file_package_tag_post(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {}

    filename = test_filenames[0]
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

    r = client.post(
            '/api/v1/packages/test/1.0',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

    r = get_package_tag_info(client, token, 'test', "1.0")

    assert 200 == r.status_code
    resp = json.loads(r.data)
    assert len(resp) == 1
    assert '"tag": "1.0"' in r.data

def test_file_package_tag_get(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {}
    
    # this was just a test for a non-text file
    # bintest is actually /bin/ls
    # just making sure it works for whatever kind of 
    # file is desired
    filename = 'bintest.npm'
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

    r = client.post(
            '/api/v1/packages/bintest/1.0',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

    get_data = {}

    r = client.get(
            '/api/v1/packages/bintest/1.0',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    
    receive_filename = 'bintestrcv.npm'
    f = open(receive_filename, 'w')
    f.write(r.data)
    f.close()
    
    assert filecmp.cmp(filename, receive_filename) == True
    
    if os.path.exists(receive_filename) and os.path.isfile(receive_filename):
        os.unlink(receive_filename)

def test_file_package_get_fail(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {}
    
    # this was just a test for a non-text file
    # bintest is actually /bin/ls
    # just making sure it works for whatever kind of 
    # file is desired
    filename = test_filenames[0] 
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

    r = client.post(
            '/api/v1/packages/test/1.0',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

    get_data = {}

    r = client.get(
            '/api/v1/packages/bintest/1.0',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )

    assert response_codes.NOT_FOUND == r.status_code
    assert 'could not locate package' in r.data


def test_file_package_get_fail_2(client):
    token = add_base_user_and_get_token(client)
    token_data = { 'token' : token }

    package_post_data = {}
    
    # this was just a test for a non-text file
    # bintest is actually /bin/ls
    # just making sure it works for whatever kind of 
    # file is desired
    filename = test_filenames[0] 
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

    r = client.post(
            '/api/v1/packages/test/1.0',
            headers=token_data,
            data=files
            )

    assert 200==r.status_code
    assert 'package_id' in r.data
    assert 'tag_id' in r.data

    get_data = {}

    r = client.get(
            '/api/v1/packages/test/1.1',
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )

    assert response_codes.NOT_FOUND == r.status_code
    assert 'could not locate tag for package' in r.data

def add_package_filename(client, token, package_name, tag, new_filename='test.txt', local_filename='test.txt'):
    token_data = { 'token' : token }

    package_post_data = {
            "package_name" : package_name,
            "tag" : tag
            }

    filename = local_filename
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

    r = client.post(
            '/api/v1/packages',
            headers=token_data,
            data=files
            )
    return r;

def get_package(client, token, package_name, tag):
    token_data = { 'token' : token }

    get_data = {}

    r = client.get(
            "/api/v1/packages/{p}/{t}".format(p=package_name, t=tag),
            headers=token_data,
            data=json.dumps(get_data),
            content_type='application/json'
            )
    try:
        if r.response_code:
            return r, False
        return r, False
    except AttributeError as err:
        return r, True

def test_file_package_get_multi(client):
    token = add_base_user_and_get_token(client)
    
    r = add_package_filename(client, token, 'test', '1.0', test_filenames[0], test_filenames[0])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package_filename(client, token, 'test', '1.1', test_filenames[1], test_filenames[1])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package_filename(client, token, 'test', '1.2', test_filenames[2], test_filenames[2])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package_filename(client, token, 'test', '2.0', test_filenames[3], test_filenames[3])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package_filename(client, token, 'test', '2.1', test_filenames[4], test_filenames[4])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package_filename(client, token, 'test', '3.0', test_filenames[5], test_filenames[5])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 1

    r = add_package_filename(client, token, 'foo', '2.2', test_filenames[3], test_filenames[3])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 2

    r = add_package_filename(client, token, 'bar', '3.1', test_filenames[5], test_filenames[5])
    assert r.status_code == 200
    resp = json.loads(r.data)
    assert 'package_id' in resp
    assert resp['package_id'] == 3

    
    r, response = get_package(client, token, 'test', '2.1')
    assert response == True
    assert test_filenames[4] in r.data

    r, response = get_package(client, token, 'test', '1.2')
    assert response == True
    assert test_filenames[2] in r.data
        
    r, response = get_package(client, token, 'test', '1.0')
    assert response == True
    assert test_filenames[0] in r.data

    r, response = get_package(client, token, 'test', '3.0')
    assert response == True
    assert test_filenames[5] in r.data

    r, response = get_package(client, token, 'test', '2.0')
    assert response == True
    assert test_filenames[3] in r.data

    r, response = get_package(client, token, 'test', '1.1')
    assert response == True
    assert test_filenames[1] in r.data

    r, response = get_package(client, token, 'foo', '2.2')
    assert response == True
    assert test_filenames[3] in r.data

    r, response = get_package(client, token, 'bar', '3.1')
    assert response == True
    assert test_filenames[5] in r.data

