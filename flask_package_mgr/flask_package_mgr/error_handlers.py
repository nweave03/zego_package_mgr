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

    def __init__(self, message, status_code=response_codes.CONFLICT, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class UnhandledError(BaseResponseError):
    def __init__(self, message='Internal Server Error', status_code=response_codes.INTERNAL_SERVER_ERROR, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class InvalidUseError(BaseResponseError):
    def __init__(self, message, status_code=response_codes.INVALID_USE, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)

class UnauthorizedError(BaseResponseError):
    def __init__(self, message, status_code=response_codes.UNAUTHORIZED, payload=None):
        BaseResponseError.__init__(self, message, status_code, payload)
