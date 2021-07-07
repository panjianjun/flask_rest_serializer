from flask import Flask

from example.schemas import QueryUserSchema, UserSchema
from flask_rest_serializer import generate_swagger, serialize_with_schemas

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
def get_users(username):
    return [user for user in users if username in user.username]


@app.route("/users/<int:user_id>")
@serialize_with_schemas(response_schema=UserSchema)
def get_user_by_id(user_id):
    for user in users:
        if user.id == user_id:
            return user

    return None


generate_swagger(app, "1.0", "./swagger.yaml", "yaml")
