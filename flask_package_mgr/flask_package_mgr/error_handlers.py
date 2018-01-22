from flask import jsonify
import response_codes

class BaseResponseError(Exception):
    status_code = response_codes.INTERNAL_SERVER_ERROR
    
    def __init__(self, message='Internal Server Error', status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class IntegrityError(BaseResponseError):
    """
    IntegrityError is meant for conflicts, such as trying to re-use the same package name/tags
    """
    def __init__(self, message, status_code=response_codes.CONFLICT, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class UnhandledError(BaseResponseError):
    """
    This is an error that holds generic errors, and mostly references internal server problems where there is no
    need to explain to the client where things went wrong
    """
    def __init__(self, message='Internal Server Error', status_code=response_codes.INTERNAL_SERVER_ERROR, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class InvalidUseError(BaseResponseError):
    """
    This is used mainly for when the client has not used the interface correctly
    """
    def __init__(self, message, status_code=response_codes.INVALID_USE, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class UnauthorizedError(BaseResponseError):
    """
    This is used for when the user attempts to do something but has not provided a correct token for it
    """
    def __init__(self, message, status_code=response_codes.UNAUTHORIZED, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class NotFoundError(BaseResponseError):
    """
    This is used for when the client is using the api correctly, but is attmepting to lookup something that
    is not located in the database
    """
    def __init__(self, message, status_code=response_codes.NOT_FOUND, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

