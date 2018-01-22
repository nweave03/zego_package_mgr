"""
    Flask Package Mgr
    
    a sample package manager system

"""
from __future__ import unicode_literals, absolute_import

from flask import Blueprint, request, session, g, abort, current_app, jsonify, json
from .schemas import TokenSchema, PackagesGetSchema, PackagesPostSchema

from .. import package_database
from ..error_handlers import IntegrityError, UnhandledError, UnauthorizedError, InvalidUseError
from ..auth import authorize, unauthorize, authenticate, auth_add_user
from ..filestore import store_file, get_all_packages, search_specific_packages

# create blueprint
pckg = Blueprint('pckg', __name__)

def validate_request(request):
    """
    enforces application/json on all messages
    """
    if not request.is_json:
        raise InvalidUseError(message='Request not application/json')
    
def authenticate_request(request):
    """
    validates and authenticates a request, forces check of token
    """
    validate_request(request)
    if 'token' not in request.headers:
        raise UnauthorizedError(message='Token not provided')
    
    user_id = authenticate(request.headers['token'])

    if None == user_id:
        raise UnauthorizedError(message='Unable to find user')
    
    return user_id

def authenticate_upload(request):
    """
    authenticate upload is different than authenticate_request because upload is a multipart 
    request.  This means the entire request is not json, so it just does a few more manual checks
    """
    if 'token' not in request.headers:
        raise UnauthorizedError(message='Token not provided')
    
    user_id = authenticate(request.headers['token'])

    if None == user_id:
        raise UnauthorizedError(message='Unable to find user')
    
    return user_id


def parse_message(content, schema):
    """
    wrapper around schemas, to detect if the schema raises any errors while parsing the message
    """
    parsed_data, errors = schema.load(content)

    if errors:
        for key in errors:
            raise InvalidUseError(message=errors[key][0])

    return parsed_data

@pckg.route('/admin/user_list', methods=['GET'])
def user_list():
    """
    marked as 'admin' but really is just a passthrough for testing purposes
    """
    user_list = package_database.list_users()
    if None == user_list:
        user_list = []
    return jsonify(user_list)

@pckg.route('/user/add', methods=['POST'])
def user_add():
    """
    adding a user to the system.  no auth or checking for now, so we can add users
    """
    content = request.get_json()
    
    parsed_data = parse_message(content, TokenSchema())
    r = auth_add_user(
                username=parsed_data['username'],
                password=parsed_data['password']
                )
    return jsonify(r)

@pckg.route('/user/get_token', methods=['POST'])
def get_token():
    """
    get a token to use in further requests.  this token is not unique/enforced right now, but does
    add username
    """
    validate_request(request)
    content = request.get_json()

    parsed_data = parse_message(content, TokenSchema())

    return jsonify(authorize(
                    username=parsed_data['username'],
                    provided_password=parsed_data['password']
                    ))

@pckg.route('/user/invalidate_token', methods=['POST'])
def invalidate_token():
    """
    invalidates a token.  in order to be a bit safer requires the login credentials again so 
    other users cannot simply log out other clients
    """
    authenticate_request(request)
    content = request.get_json()
    
    parsed_data = parse_message(content, TokenSchema())

    return jsonify(unauthorize(
                    username=parsed_data['username'],
                    provided_password=parsed_data['password']
                    ))

@pckg.route('/packages', methods=['GET', 'POST'])
def packages():
    """ 
    base packages route.  this includes a POST that will allow the upload of a file and
    a GET that can be used to search packages
    """
    print "in packages"
    if request.method == 'POST':
        user_id = authenticate_upload(request)
        print "filename {fn}, data {d}, content_type {ct}, content_size {s}".format(
                fn=request.files['json'].filename,
                d=request.files['json'].read(),
                ct=request.files['json'].content_type,
                s=request.files['json'].content_length
                )

        print "filename {fn}, data {d}, content_type {ct}, content_size {s}".format(
                fn=request.files['file'].filename,
                d=request.files['file'].read(),
                ct=request.files['file'].content_type,
                s=request.files['file'].content_length
                )

        # this is really weird, i've spent a lot of time looking into this, and
        # for some reason the python multi-part stuff isn't well defined.
        # werkzeug will not accept anything that cannot be opened in add_file, which 
        # restricts potential string options.  I tried adding it into a temporary file
        # but then werkzeug wouldn't accept application/json as content_type, it 
        # overrode it with application/octet-stream
        # I tried numerous string streams, but then werkzeug doesn't actually place the
        # data of the string, but rather the type@memory_address identification.
        # it appears that it will not actually read the string, but rather just the
        # identification information.  Given these restrictions, and a lack of further time
        # to spend looking into this weird python/flask multipart problem, I decided to just decode
        # the json filename for now and move on.  This is an interview test, not something
        # i intend to put into production.
        content = json.loads(request.files['json'].filename)

        parsed_data = parse_message(content, PackagesPostSchema())
        if 'file' not in request.files:
            raise InvalidUseError(message='file not in POST request')
        file = request.files['file']
        return jsonify(
                store_file(
                    file=file,
                    package_name=parsed_data['package_name'],
                    user=user_id,
                    tag=parsed_data['tag']
                    )
                )
    elif request.method == 'GET':
        user_id = authenticate_request(request)
        content = request.get_json()
        parsed_data = parse_message(content, PackagesGetSchema())
        packages = []
        if 'search' in parsed_data:
            packages = search_specific_packages(
                    search_term=parsed_data['search']
                    )
        else:
            packages = get_all_packages()
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
