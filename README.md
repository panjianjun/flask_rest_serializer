# flask-http-serializer

Make flask request parse and response serialize easier.

### Ability

- define request and response schema with Marshmallow.
- request serialize and validation.
- return Python object(Sqlalchemy Model instance or customer Data Object) directly in your view functions.
- automatically swagger generation.

### Usage

```python

# schemas.py
from marshmallow import fields
from marshmallow.schema import BaseSchema


class UserSchema(BaseSchema):
    id = fields.Integer()
    username = fields.String()


class QueryUserSchema(BaseSchema):
    username = fields.String()


# app.py
from flask import Flask

from schemas import QueryUserSchema, UserSchema
from flask_rest_serializer import serialize_with_schemas, generate_swagger

app = Flask("example")


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
def get_users(username):  # username argument is from request_schema definition
    return [user for user in users if username in user.username]


@app.route("/users/<int:user_id>")
@serialize_with_schemas(response_schema=UserSchema)
def get_user_by_id(user_id):
    for user in users:
        if user.id == user_id:
            return user

    return None


generate_swagger(app, "1.0", "./swagger.yaml", "yaml")
```

### Example code

- 1.clone repo to local
- 2.pipenv install
- 3.cd exmaple & pipenv run flask run
