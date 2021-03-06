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
