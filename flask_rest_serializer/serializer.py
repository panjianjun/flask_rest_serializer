import functools
import logging

from flask import Response, current_app, jsonify, request
from marshmallow import Schema, ValidationError, missing
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)


class RequestFullData(dict):
    def get_val_from_request(self, location, attr_name):
        missing_default = missing
        if location in ("args", "query_string"):
            return request.args.get(attr_name, missing_default)
        elif location == "headers":
            return request.headers.get(attr_name, missing_default)
        elif location == "body":
            if request.is_json:
                return request.json.get(attr_name, missing_default)
            return request.form.get(attr_name, )
        return missing_default

    def get(self, key, default=None):
        location, attr_name = key.split(".")
        return self.get_val_from_request(location, attr_name)


class RequestSerializer:
    @staticmethod
    def get_default_location(method):
        if method.lower() in ("get", "delete"):
            return "args"
        else:
            return "body"

    @staticmethod
    def serialize_request(request_schema):
        """serialize request information into python dict"""
        if request_schema is None:
            return {}

        field_origin_data_key = {}
        for field_name, field_obj in request_schema.load_fields.items():
            # save origin data_key and restore it after serialize request
            field_origin_data_key[field_name] = field_obj.data_key
            # get location for field
            # if missing, get a default according to http method
            location = field_obj.metadata.get("location") or \
                       RequestSerializer.get_default_location(request.method)
            # set location as data_key of field
            field_obj.data_key = f"{location}.{field_name}"

        serialized_data = request_schema.load(RequestFullData())

        for field_name, field_obj in request_schema.load_fields.items():
            field_obj.data_key = field_origin_data_key.get(field_name)
            if field_name not in serialized_data:
                # serialized_data is passed into view_function as kwargs,
                # make sure every key exists
                serialized_data[field_name] = None

        return serialized_data


def get_schema_instance(schema):
    if schema is not None:
        if isinstance(schema, Schema):
            return schema
        elif issubclass(schema, Schema):
            return schema()
    return None


def serialize_with_schemas(request_schema=None,
                           response_schema=None):
    """

    :param request_schema: instance or subclass of marshmallow Schema
    :param response_schema: instance or subclass of marshmallow Schema
    :return: a decorator
    """

    def deco(func):
        setattr(func, "request_schema", request_schema)
        setattr(func, "response_schema", response_schema)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            request_schema_instance = get_schema_instance(request_schema)
            response_schema_instance = get_schema_instance(response_schema)
            try:
                serialized_data = RequestSerializer.serialize_request(
                    request_schema_instance)
                kwargs.update(serialized_data)
            except ValidationError as e:
                logger.debug("serialize request with schema %s failed: %s",
                             request_schema_instance, e)
                get_validation_error_handler()(e)
            origin_ret = func(*args, **kwargs)
            if isinstance(origin_ret, Response) or \
                    response_schema_instance is None:
                return origin_ret
            return jsonify(response_schema_instance.dump(origin_ret))

        return wrapper

    return deco


def abort_handler(exc):
    raise BadRequest(description=str(exc.messages))


def re_raise_handler(exc):
    raise exc


validation_error_handlers = {
    "abort": abort_handler,
    "re_raise": re_raise_handler
}


def get_validation_error_handler():
    handler = current_app.config.get(
        "REST_SERIALIZER_VALIDATION_ERROR_HANDLER", "abort")
    if callable(handler):
        return handler
    return validation_error_handlers.get(handler, abort_handler)
