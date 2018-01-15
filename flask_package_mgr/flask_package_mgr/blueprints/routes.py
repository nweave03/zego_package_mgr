"""
    Flask Package Mgr
    
    a sample package manager system

"""
from __future__ import unicode_literals, absolute_import

from flask import Blueprint, request, session, g, abort, current_app, jsonify

from .. import package_database
from ..error_handlers import IntegrityError, UnhandledError

# create blueprint
pckg = Blueprint('pckg', __name__)

@pckg.route('/admin/user_list', methods=['GET'])
def user_list():
    user_list = package_database.list_users()
    if None == user_list:
        user_list = []
    return jsonify(user_list)

@pckg.route('/user/add', methods=['POST'])
def user_add():
    content = request.get_json()
    r = package_database.add_user(
                content['username'],
                content['password'],
                'ApiKey'
                )
    return jsonify(r)

@pckg.route('/user/login', methods=['GET', 'POST'])
def login():
    print "Login Called"
    return "Login Called"

@pckg.route('/user/logout')
def logout():
    print "Logout Called"
    return "Logout Called"

@pckg.route('/list_packages', methods=['GET'])
def list_entry():
    print "List Pacakges Called"
    return "List Packages Called"

@pckg.route('/upload_package', methods=['POST'])
def upload_package():
    print "Upload Package Called"
    return "Upload Package Called"


@pckg.errorhandler(IntegrityError)
def handle_integrity_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@pckg.errorhandler(UnhandledError)
def handle_unhandled_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
