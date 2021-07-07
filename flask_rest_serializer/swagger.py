import re

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from werkzeug.routing import IntegerConverter, NumberConverter


def generate_swagger(app, api_version, doc_path, format="yaml", **options):
    generator = SwaggerGenerator(
        app, api_version, doc_path, format, **options
    )
    generator.generate_swagger()


class SwaggerGenerator:
    """swagger generator class"""

    def __init__(self, app, api_version, doc_path, format="yaml", **options):
        """
        :param app: flask app instance
        :param api_version: api doc version
        :param doc_dir:
        :param format:
        """
        self.app = app
        if doc_path.endswith(format):
            self.doc_path = doc_path
        else:
            self.doc_path = f"{doc_path}.{format}"
        self.doc_format = format
        title = options.pop("title", None)
        self.api_spec = APISpec(
            title=title or f"{self.app.import_name}-api-swagger",
            version=api_version,
            openapi_version="3.0.0",
            plugins=(MarshmallowPlugin(),),
            **options
        )

    def generate_swagger(self):
        for rule in self.app.url_map.iter_rules():
            self.register_rule(rule)

        with open(self.doc_path, "w") as f:
            f.write(self.api_spec.to_yaml())

    def register_rule(self, rule):
        rule_parser = RuleParser(self.app, rule)
        operations = rule_parser.operations
        if not operations:
            return

        self.api_spec.path(
            path=rule_parser.path,
            operations=operations,
            parameters=rule_parser.parameters,
            description=rule_parser.description
        )


class RuleParser:
    def __init__(self, app, rule):
        self.app = app
        self.rule = rule
        self.view_func = self.app.view_functions[self.rule.endpoint]

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
        request_schema = getattr(self.view_func, "request_schema", None)
        response_schema = getattr(self.view_func, "response_schema", None)
        if not any([request_schema, response_schema]):
            return

        operations = {}
        methods = [method.lower() for method in self.rule.methods if
                   method not in ("OPTIONS", "HEAD")]
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
