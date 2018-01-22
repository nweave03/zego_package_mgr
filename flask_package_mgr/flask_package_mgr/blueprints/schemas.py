from marshmallow import Schema, fields

class TokenSchema(Schema):
    """
    Schema for basic auth Token manipulation
    """
    username = fields.Str(
                required=True,
                error_messages={'required' : 'username is required'}
                )
    password = fields.Str(
                required=True,
                error_messages={'required' : 'password is required'}
                )

class PackagesGetSchema(Schema):
    """
    Schema for the base level '/packages' GET
    """
    search = fields.Str()

class PackagesPostSchema(Schema):
    """
    Schema for the base level '/packages' POST
    """
    package_name = fields.Str(
                required=True,
                error_messages={'required' : 'package_name is required'}
                )
    tag = fields.Str(
                required=True,
                error_messages={'required' : 'tag is required'}
                )

class PackagesTitleGetSchema(Schema):
    """
    Schema for the level '/packages/<package_name>' GET
    """
    tag_search = fields.Str()

class PackagesTitlePostSchema(Schema):
    """
    Schema for the level '/packages/<package_name>' POST
    """
    tag = fields.Str(
                required=True,
                error_messages={'required' : 'tag is required'}
                )

class PackagesTitleTagPostSchema(Schema):
    """
    Schema for the level '/packages/<package_name>/<tag>' POST
    """
    pass
    # this doesn't have any requirements

class PackagesTitleTagGetSchema(Schema):
    """
    Schema for the level '/packages/<package_name>/<tag>' GET
    """
    pass
    # this doesn't have any requirements
