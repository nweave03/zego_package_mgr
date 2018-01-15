"""
    Flask Package Mgr
    
    a sample package manager system

"""
from __future__ import unicode_literals, absolute_import

from flask import Blueprint, request, session, g, abort, current_app, jsonify
from .schemas import TokenSchema

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

def parse_message(content, schema):
    parsed_data, errors = schema.load(content)

    if errors:
        for key in errors:
            raise InvalidUseError(message=errors[key][0])

    return parsed_data

@pckg.route('/admin/user_list', methods=['GET'])
def user_list():
    user_list = package_database.list_users()
    if None == user_list:
        user_list = []
    return jsonify(user_list)

@pckg.route('/user/add', methods=['POST'])
def user_add():
    content = request.get_json()
    
    parsed_data = parse_message(content, TokenSchema())
    r = auth_add_user(
                username=parsed_data['username'],
                password=parsed_data['password']
                )
    return jsonify(r)

@pckg.route('/user/get_token', methods=['POST'])
def get_token():
    validate_request(request)
    content = request.get_json()

    parsed_data = parse_message(content, TokenSchema())

    return jsonify(authorize(
                    username=parsed_data['username'],
                    provided_password=parsed_data['password']
                    ))

@pckg.route('/user/invalidate_token', methods=['POST'])
def invalidate_token():
    authenticate_request(request)
    content = request.get_json()
    
    parsed_data = parse_message(content, TokenSchema())

    return jsonify(unauthorize(
                    username=parsed_data['username'],
                    provided_password=parsed_data['password']
                    ))

@pckg.route('/packages', methods=['GET', 'POST'])
def packages():
    authenticate_request(request)
    content = request.get_json()
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        parsed_data = parse_message(content, PackagesGetSchema())
        packages = []
        if parsed_data['search']:
            packages = search_packages(
                    search=parsed_data['search']
                    )
        else:
            packages = search_all_packages()
        return jsonify(packages)
    else:
        raise InvalidUseError(message='method not supported')

@pckg.route('/packages/<package_title>', methods=['GET','POST'])
def upload_package():
    authenticate_request(request)
    content = request.get_json()
    if request.method == 'POST':
        pass
    elif request.method == 'GET':
        pass
    else:
        raise InvalidUseError(message='method not supported')


@pckg.errorhandler(UnauthorizedError)
@pckg.errorhandler(UnhandledError)
@pckg.errorhandler(IntegrityError)
@pckg.errorhandler(InvalidUseError)
def handle_custom_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
