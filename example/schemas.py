from marshmallow import fields
from marshmallow.schema import Schema


class UserSchema(Schema):
    id = fields.Integer()
    username = fields.String()


class QueryUserSchema(Schema):
    username = fields.String()


class CreateUserSchema(Schema):
    username = fields.String(required=True, allow_none=False,
                             metadata={"location": "body"})
