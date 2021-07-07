from marshmallow import fields
from marshmallow.schema import BaseSchema


class UserSchema(BaseSchema):
    id = fields.Integer()
    username = fields.String()


class QueryUserSchema(BaseSchema):
    username = fields.String()
