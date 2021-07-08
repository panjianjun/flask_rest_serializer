# flask-http-serializer

Make flask request parse and response serialize easier.

### Ability

- define request and response schema with Marshmallow.
- request serialize and validation (validation is supported by Marshmallow Schema load).
- field can specify request location to get value , location is one of `headers`, `body`(form or json), `args`). If not set location will be `args` for http GET, DELETE and `body` for http POST, PUT, PATCH. 
- return Python object(Sqlalchemy Model instance or customer Data Object) directly in your view functions.
- automatically swagger generation.

### Configurations

| flask_config_key | type |description |
| -------- | --------- | ------- | 
| REST_SERIALIZER_BLUEPRINT_SEPARATE_DOCS | boolean | if set `True`, will generate separated swagger doc file for blueprint. if set `False` only one doc file will be generated. |
| REST_SERIALIZER_VALIDATION_ERROR_HANDLER | string `abort`, string `re_raise` or a callable object | behaviour when serialize request occurred a ValidationError. if set `abort`, will raise a `HttpException`. if set `re_raise` will reraise ValidationError. if set a `callable` object, will call it with ValidationError|

### Usage

```python

# schemas.py
from marshmallow import fields
from marshmallow.schema import Schema


class UserSchema(Schema):
    id = fields.Integer()
    username = fields.String()


class QueryUserSchema(Schema):
    username = fields.String()


class CreateUserSchema(Schema):
    username = fields.String(required=True, allow_none=False,
                             metadata={"location": "body"})  # if location not set, 

# app.py
from flask import Flask
from flask_restful import Api, Resource

from example.schemas import CreateUserSchema, QueryUserSchema, UserSchema
from flask_rest_serializer import generate_swagger, serialize_with_schemas

app = Flask("example")
api = Api(app, prefix="/rest")


class User:
    def __init__(self, id, username):
        self.id = id
        self.username = username


user_one = User(id=1, username="one")
user_two = User(id=2, username="two")

users = [user_one, user_two]


@app.route("/users", methods=["GET"])
@serialize_with_schemas(request_schema=QueryUserSchema,
                        response_schema=UserSchema(many=True))
def get_users(username):
    return [user for user in users if username in user.username]


@app.route("/users/<int:user_id>")
@serialize_with_schemas(response_schema=UserSchema)
def get_user_by_id(user_id):
    for user in users:
        if user.id == user_id:
            return user

    return None


@api.resource("/users")
class UserResource(Resource):
    @serialize_with_schemas(request_schema=CreateUserSchema,
                            response_schema=UserSchema)
    def post(self, username):
        new_user = User(id=3, username=username)
        return new_user


generate_swagger(app, "1.0", "./", "yaml")

```

### Example code

- 1.clone repo to local
- 2.pipenv install
- 3.cd exmaple & pipenv run flask run
