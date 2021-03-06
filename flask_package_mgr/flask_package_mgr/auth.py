from flask import g, current_app
from package_database import lookup_password, add_user, lookup_user_id
from error_handlers import UnauthorizedError

def authorize(username, provided_password):
    """
    this will authorize a user and issue a token to them
    hard coded to 'aValidToken' for right now
    """
    stored_password = lookup_password(username)
    
    if (provided_password == stored_password):
        # for now hard coding a token, real implementations 
        # would require more, plus timeouts/etc
        return { 'token' : "aValidToken-{u}".format(u=username) }
    else:
        raise UnauthorizedError(message='password is incorrect')

def unauthorize(username, provided_password):
    """
    This would theoretically revoke the token
    """
    stored_password = lookup_password(username)
    if (provided_password == stored_password):
        return { 'message' : 'token has been revoked' }
    else:
        raise UnauthorizedError(message='password is incorrect')

def authenticate(token):
    """
    validate that the user has provided a valid token.  Would also
    be where timeout checks would go/etc.
    """
    if 'aValidToken' not in token:
        raise UnauthorizedError(message='Invalid Token')
    username = token.rsplit('-',1)[1]
    
    user_id = lookup_user_id(username=username)

    return user_id

def auth_add_user(username, password):
    """
    This is where one would take extra steps, like salting/hashing
    a password or generating a real apikey like infrastructure
    """
    return add_user(
                username=username,
                password=password,
                key='ApiKey'
                )
