"""
    Flask Package Mgr
    
    a sample package manager system

"""

from flask import Blueprint, request, session, g, abort, current_app

# create blueprint
bp = Blueprint('flask_package_mgr', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    print "Login Called"
    return "Login Called"

@bp.route('/logout')
def logout():
    print "Logout Called"
    return "Logout Called"

@bp.route('/list_packages', methods=['GET'])
def list_entry():
    print "List Pacakges Called"
    return "List Packages Called"

@bp.route('/upload_package', methods=['POST'])
def upload_package():
    print "Upload Package Called"
    return "Upload Package Called"

