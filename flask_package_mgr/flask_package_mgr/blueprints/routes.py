"""
    Flask Package Mgr
    
    a sample package manager system

"""
from __future__ import unicode_literals, absolute_import

from flask import Blueprint, request, session, g, abort, current_app, jsonify

from .. import package_database
from ..error_handlers import IntegrityError, UnhandledError, UnauthorizedError, InvalidUseError
from ..auth import authorize, unauthorize, authenticate, auth_add_user

# create blueprint
pckg = Blueprint('pckg', __name__)

def validate_request(request):
    if not request.is_json:
        raise InvalidUseError(message='Request not application/json')
    
def authenticate_request(request):
    validate_request(request)
    if 'token' not in request.headers:
        raise UnauthorizedError(message='Token not provided')
    return authenticate(request.headers['token'])

@pckg.route('/admin/user_list', methods=['GET'])
def user_list():
    user_list = package_database.list_users()
    if None == user_list:
        user_list = []
    return jsonify(user_list)

@pckg.route('/user/add', methods=['POST'])
def user_add():
    content = request.get_json()
    r = auth_add_user(
                username=content['username'],
                password=content['password']
                )
    return jsonify(r)

@pckg.route('/user/get_token', methods=['POST'])
def get_token():
    validate_request(request)
    content = request.get_json()
    if 'username' not in content:
        raise InvalidUseError(message='get_token requires username')
    if 'password' not in content:
        raise InvalidUseError(message='get_token requires password')
    
    return jsonify(authorize(
                    username=content['username'],
                    provided_password=content['password']
                    ))

@pckg.route('/user/invalidate_token', methods=['POST'])
def invalidate_token():
    authenticate_request(request)
    content = request.get_json()
    if 'username' not in content:
        raise InvalidUseError(message='get_token requires username')
    if 'password' not in content:
        raise InvalidUseError(message='get_token requires password')
    return jsonify(unauthorize(
                    username=content['username'],
                    provided_password=content['password']
                    ))

@pckg.route('/list_packages', methods=['GET'])
def list_entry():
    print "List Pacakges Called"
    return "List Packages Called"

@pckg.route('/upload_package', methods=['POST'])
def upload_package():
    print "Upload Package Called"
    return "Upload Package Called"

@pckg.errorhandler(UnauthorizedError)
@pckg.errorhandler(UnhandledError)
@pckg.errorhandler(IntegrityError)
@pckg.errorhandler(InvalidUseError)
def handle_integrity_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
