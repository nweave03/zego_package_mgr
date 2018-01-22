from marshmallow import Schema, fields

class TokenSchema(Schema):
    username = fields.Str(
                required=True,
                error_messages={'required' : 'username is required'}
                )
    password = fields.Str(
                required=True,
                error_messages={'required' : 'password is required'}
                )

class PackagesGetSchema(Schema):
    search = fields.Str()

class PackagesPostSchema(Schema):
    package_name = fields.Str(
                required=True,
                error_messages={'required' : 'package_name is required'}
                )
    tag = fields.Str(
                required=True,
                error_messages={'required' : 'tag is required'}
                )

class PackagesTitleGetSchema(Schema):
    tag_search = fields.Str()

class PackagesTitlePostSchema(Schema):
    tag = fields.Str(
                required=True,
                error_messages={'required' : 'tag is required'}
                )
