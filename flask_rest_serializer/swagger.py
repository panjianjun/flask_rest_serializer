import json
import re
from collections import defaultdict

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import current_app
from werkzeug.routing import IntegerConverter, NumberConverter


def generate_swagger(app, api_version, doc_path, format="yaml", **options):
    generator = SwaggerGenerator(
        app, api_version, doc_path, format, **options
    )
    generator.generate_swagger()


class SwaggerGenerator:
    def __init__(self, app, api_version, doc_path, format="yaml", **options):
        """
        :param app: flask app instance
        :param api_version: api doc version
        :param doc_path: swagger save path
        :param format:swagger file format, json or yaml
        """
        self.app = app
        self.api_version = api_version
        self.doc_path = doc_path.rstrip("/")
        self.doc_format = format
        self.api_spec_opts = options
        self.api_specs = {}
        self.blueprint_to_apis = defaultdict(list)

    def get_api_spec(self, name):
        """
        get api spec for give blueprint or app
        :param name: blurprint name or app.import_name
        :return: api_spec
        """
        if name not in self.api_specs:
            self.api_specs[name] = APISpec(
                title=f"{name}-api",
                version=self.api_version,
                openapi_version="3.0.0",
                plugins=(MarshmallowPlugin(),),
                **self.api_spec_opts
            )
        return self.api_specs[name]

    def generate_swagger(self):
        with self.app.app_context():
            for rule in self.app.url_map.iter_rules():
                self.register_rule(rule)
        for doc_name, apis in self.blueprint_to_apis.items():
            doc_path = f"{self.doc_path}/{doc_name}.{self.doc_format}"
            api_spec = self.get_api_spec(doc_name)
            for api in apis:
                api_spec.path(**api)
            with open(doc_path, "w") as f:
                if self.doc_format == "json":
                    json.dump(
                        api_spec.to_dict(), f, indent=4, ensure_ascii=False,
                        sort_keys=True
                    )
                else:
                    f.write(
                        api_spec.to_yaml(
                            yaml_dump_kwargs={"allow_unicode": True}
                        )
                    )

    def register_rule(self, rule):
        rule_parser = RuleParser(self.app, rule)
        operations = rule_parser.operations
        if not operations:
            return
        self.blueprint_to_apis[rule_parser.doc_file_name].append(
            dict(
                path=rule_parser.path,
                operations=operations,
                parameters=rule_parser.parameters,
                description=rule_parser.description
            )
        )


class RuleParser:
    def __init__(self, app, rule):
        self.app = app
        self.rule = rule
        self.view_func = self.app.view_functions[self.rule.endpoint]

    def get_blueprint_name(self):
        blueprint_name = self.rule.endpoint.rsplit(".", 1)[0]
        if blueprint_name in self.app.blueprints:
            return blueprint_name
        return self.app.import_name

    @property
    def doc_file_name(self):
        if current_app.config.get("REST_SERIALIZER_BLUEPRINT_SEPARATE_DOCS",
                                  False):
            view_cls = getattr(self.view_func, "view_class", None)
            if view_cls and getattr(view_cls, "rest_serialize_doc_name", None):
                return getattr(view_cls, "rest_serialize_doc_name", None)
            return self.get_blueprint_name()
        return self.app.import_name

    @property
    def description(self):
        return self.view_func.__doc__ or self.rule.endpoint

    @property
    def path(self):
        return re.sub(r"<(?:\S+:)?(\S+)>", r"{\1}", self.rule.rule)

    @property
    def parameters(self):
        parameters = []
        for argument in self.rule.arguments:
            convertor = self.rule._converters.get(argument)
            arg_type = "string"
            if convertor:
                if isinstance(convertor, IntegerConverter):
                    arg_type = "integer"
                elif isinstance(convertor, NumberConverter):
                    arg_type = "number"
            parameters.append({
                "name": argument,
                "in": "path",
                "required": True,
                "schema": {"type": arg_type}
            })

        return parameters

    @property
    def operations(self):
        view_cls = getattr(self.view_func, "view_class", None)
        if view_cls:
            operations = {}
            for method in ("get", "post", "delete", "put", "patch"):
                handler_func = getattr(view_cls, method, None)
                if handler_func:
                    request_schema = getattr(handler_func, "request_schema",
                                             None)
                    response_schema = getattr(handler_func,
                                              "response_schema", None)
                    method_operation = self._get_operations([method],
                                                            request_schema,
                                                            response_schema)
                    if method_operation:
                        operations.update(method_operation)
            return operations
        else:
            request_schema = getattr(self.view_func, "request_schema", None)
            response_schema = getattr(self.view_func, "response_schema", None)
            return self._get_operations(self.rule.methods, request_schema,
                                        response_schema)

    @staticmethod
    def _get_operations(methods, request_schema, response_schema):
        if not any([request_schema, response_schema]):
            return
        operations = {}
        methods = [method.lower() for method in methods if
                   method.lower() not in ("options", "head")]
        for method in methods:
            content = {
                "application/json": {
                    "schema": response_schema or {}
                }
            } if response_schema else {}
            operations[method] = dict(
                responses={
                    "200": {
                        "description": "SUCCESS",
                        "content": content
                    }
                }
            )
            if request_schema:
                if method in ("get", "delete"):
                    operations[method]["parameters"] = [
                        {"schema": request_schema, "in": "query"}
                    ]
                else:
                    operations[method]["requestBody"] = {
                        "content": {
                            "application/json": {
                                "schema": request_schema
                            }
                        }
                    }
        return operations
