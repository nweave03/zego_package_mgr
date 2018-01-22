"""
    Flask Package Mgr
    
    a sample package manager system

"""
from __future__ import unicode_literals, absolute_import

from flask import Blueprint, request, session, g, abort, current_app, jsonify, json, send_from_directory
from .schemas import TokenSchema, PackagesGetSchema, PackagesPostSchema, PackagesTitlePostSchema, PackagesTitleGetSchema, PackagesTitleTagPostSchema, PackagesTitleTagGetSchema

from .. import package_database
from ..error_handlers import IntegrityError, UnhandledError, UnauthorizedError, InvalidUseError, NotFoundError
from ..auth import authorize, unauthorize, authenticate, auth_add_user
from ..filestore import store_file, get_all_packages, search_specific_packages, get_all_tags, search_specific_tags, get_filepath_for_package

api_version = '/api/v1'

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

@pckg.route(api_version + '/admin/user_list', methods=['GET'])
def user_list():
    """
    marked as 'admin' but really is just a passthrough for testing purposes
    """
    user_list = package_database.list_users()
    if None == user_list:
        user_list = []
    return jsonify(user_list)

@pckg.route(api_version + '/user/add', methods=['POST'])
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

@pckg.route(api_version + '/user/get_token', methods=['POST'])
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

@pckg.route(api_version + '/user/invalidate_token', methods=['POST'])
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

@pckg.route(api_version + '/packages', methods=['GET', 'POST'])
def packages():
    """ 
    base packages route.  this includes a POST that will allow the upload of a file and
    a GET that can be used to search packages
    """
    if request.method == 'POST':
        user_id = authenticate_upload(request)

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

@pckg.route(api_version + '/packages/<package_title>', methods=['GET','POST'])
def specific_package(package_title):
    """
    The specific packages route will allow upload on POST, in much the same way that 
    POST on the base packages route does, but it will take the package title from the URL.  
    On GET this method will allow searching of tags to get specific tag ids

    because of this '/' are not allowed in the package titles and tags
    """
    if request.method == 'POST':
        user_id = authenticate_upload(request)
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

        parsed_data = parse_message(content, PackagesTitlePostSchema())

        if 'file' not in request.files:
            raise InvalidUseError(message='file not in POST requst')
        file = request.files['file']
        return jsonify(
                store_file(
                    file=file,
                    package_name=package_title,
                    user=user_id,
                    tag=parsed_data['tag']
                    )
                )
    elif request.method == 'GET':
        authenticate_request(request)
        content = request.get_json()

        parsed_data = parse_message(content, PackagesTitleGetSchema())

        if 'tag_search' in parsed_data:
            tags = search_specific_tags(
                    package = package_title,
                    tag_search = parsed_data['tag_search']
                    )
        else:
            tags = get_all_tags(
                    package = package_title
                    )
        return jsonify(tags)
    else:
        raise InvalidUseError(message='method not supported')

@pckg.route(api_version + '/packages/<package_title>/<tag>', methods=['GET','POST'])
def specific_package_tag(package_title, tag):
    """
    The specific packages route will allow upload on POST, in much the same way that 
    POST on the base packages route does, but it will take the package title and
    package tag from the URL.  

    On GET this method will download the file to the client.

    because of this '/' are not allowed in the package titles and tags
    """
    if request.method == 'POST':
        user_id = authenticate_upload(request)
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

        parsed_data = parse_message(content, PackagesTitleTagPostSchema())

        if 'file' not in request.files:
            raise InvalidUseError(message='file not in POST requst')
        file = request.files['file']
        return jsonify(
                store_file(
                    file=file,
                    package_name=package_title,
                    user=user_id,
                    tag=tag
                    )
                )
    elif request.method == 'GET':
        authenticate_request(request)
        content = request.get_json()

        parsed_data = parse_message(content, PackagesTitleGetSchema())

        filepath = get_filepath_for_package(
                        package_name = package_title,
                        tag = tag
                        )
        
        return send_from_directory(directory=filepath[0], filename=filepath[1], as_attachment=True)
    else:
        raise InvalidUseError(message='method not supported')




@pckg.errorhandler(UnauthorizedError)
@pckg.errorhandler(UnhandledError)
@pckg.errorhandler(IntegrityError)
@pckg.errorhandler(NotFoundError)
@pckg.errorhandler(InvalidUseError)
def handle_custom_error(error):
    """
    Handles all of the custom errors in the API and returns the relevant message and response code
    """
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response
