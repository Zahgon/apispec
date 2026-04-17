"""Utilities for generating OpenAPI Specification (fka Swagger) entities from
:class:`Fields <marshmallow.fields.Field>`.

.. warning::

    This module is treated as private API.
    Users should not need to use this module directly.
"""

from __future__ import annotations

import functools
import operator
import re
import typing
import warnings

import marshmallow
from marshmallow.orderedset import OrderedSet
from packaging.version import Version

# marshmallow field => (JSON Schema type, format)
DEFAULT_FIELD_MAPPING: dict[type, tuple[str | None, str | None]] = {
    marshmallow.fields.Integer: ("integer", None),
    marshmallow.fields.Number: ("number", None),
    marshmallow.fields.Float: ("number", None),
    marshmallow.fields.Decimal: ("number", None),
    marshmallow.fields.String: ("string", None),
    marshmallow.fields.Boolean: ("boolean", None),
    marshmallow.fields.UUID: ("string", "uuid"),
    marshmallow.fields.DateTime: ("string", "date-time"),
    marshmallow.fields.Date: ("string", "date"),
    marshmallow.fields.Time: ("string", None),
    marshmallow.fields.TimeDelta: ("number", None),
    marshmallow.fields.Email: ("string", "email"),
    marshmallow.fields.URL: ("string", "url"),
    marshmallow.fields.Dict: ("object", None),
    marshmallow.fields.Field: (None, None),
    marshmallow.fields.Raw: (None, None),
    marshmallow.fields.List: ("array", None),
    marshmallow.fields.IP: ("string", "ip"),
    marshmallow.fields.IPv4: ("string", "ipv4"),
    marshmallow.fields.IPv6: ("string", "ipv6"),
}


# Properties that may be defined in a field's metadata that will be added to the output
# of field2property
# https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#schemaObject
_VALID_PROPERTIES = {
    "format",
    "title",
    "description",
    "default",
    "multipleOf",
    "maximum",
    "exclusiveMaximum",
    "minimum",
    "exclusiveMinimum",
    "maxLength",
    "minLength",
    "pattern",
    "maxItems",
    "minItems",
    "uniqueItems",
    "maxProperties",
    "minProperties",
    "required",
    "enum",
    "type",
    "items",
    "allOf",
    "oneOf",
    "anyOf",
    "not",
    "properties",
    "additionalProperties",
    "readOnly",
    "writeOnly",
    "xml",
    "externalDocs",
    "example",
    "examples",
    "nullable",
    "deprecated",
}


_VALID_PREFIX = "x-"


class FieldConverterMixin:
    """Adds methods for converting marshmallow fields to an OpenAPI properties."""

    field_mapping: dict[type, tuple[str | None, str | None]] = DEFAULT_FIELD_MAPPING
    openapi_version: Version

    def init_attribute_functions(self):
        pass

    def map_to_openapi_type(self, field_cls, *args):
        """Set mapping for custom field class.

        :param type field_cls: Field class to set mapping for.

        ``*args`` can be:

        - a pair of the form ``(type, format)``
        - a core marshmallow field type (in which case we reuse that type's mapping)
        """
        pass

    def add_attribute_function(self, func):
        """Method to add an attribute function to the list of attribute functions
        that will be called on a field to convert it from a field to an OpenAPI
        property.

        :param func func: the attribute function to add
            The attribute function will be bound to the
            `OpenAPIConverter <apispec.ext.marshmallow.openapi.OpenAPIConverter>`
            instance.
            It will be called for each field in a schema with
            `self <apispec.ext.marshmallow.openapi.OpenAPIConverter>` and a
            `field <marshmallow.fields.Field>` instance
            positional arguments and `ret <dict>` keyword argument.
            Must return a dictionary of OpenAPI properties that will be shallow
            merged with the return values of all other attribute functions called on the field.
            User added attribute functions will be called after all built-in attribute
            functions in the order they were added. The merged results of all
            previously called attribute functions are accessible via the `ret`
            argument.
        """
        pass

    def field2property(self, field: marshmallow.fields.Field) -> dict:
        """Return the JSON Schema property definition given a marshmallow
        :class:`Field <marshmallow.fields.Field>`.

        Will include field metadata that are valid properties of OpenAPI schema objects
        (e.g. "description", "enum", "example").

        https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#schemaObject

        :param Field field: A marshmallow field.
        :rtype: dict, a Property Object
        """
        ret: dict = {}

        for attr_func in self.attribute_functions:
            ret.update(attr_func(field, ret=ret))

        return ret

    def field2type_and_format(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary of OpenAPI type and format based on the field type.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2default(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary containing the field's default value.

        Will first look for a `default` key in the field's metadata and then
        fall back on the field's `missing` parameter. A callable passed to the
        field's missing parameter will be ignored.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2choices(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary of OpenAPI field attributes for valid choices definition.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2read_only(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary of OpenAPI field attributes for a dump_only field.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2write_only(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary of OpenAPI field attributes for a load_only field.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2nullable(self, field: marshmallow.fields.Field, ret) -> dict:
        """Return the dictionary of OpenAPI field attributes for a nullable field.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2range(self, field: marshmallow.fields.Field, ret) -> dict:
        """Return the dictionary of OpenAPI field attributes for a set of
        :class:`Range <marshmallow.validators.Range>` validators.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2length(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary of OpenAPI field attributes for a set of
        :class:`Length <marshmallow.validators.Length>` validators.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def field2pattern(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return the dictionary of OpenAPI field attributes for a
        :class:`Regexp <marshmallow.validators.Regexp>` validator.

        If there is more than one such validator, only the first
        is used in the output spec.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def metadata2properties(
        self, field: marshmallow.fields.Field, **kwargs: typing.Any
    ) -> dict:
        """Return a dictionary of properties extracted from field metadata.

        Will include field metadata that are valid properties of `OpenAPI schema
        objects
        <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#schemaObject>`_
        (e.g. "description", "enum", "example").

        In addition, `specification extensions
        <https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#specification-extensions>`_
        are supported.  Prefix `x_` to the desired extension when passing the
        keyword argument to the field constructor. apispec will convert `x_` to
        `x-` to comply with OpenAPI.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def nested2properties(self, field: marshmallow.fields.Field, ret) -> dict:
        """Return a dictionary of properties from :class:`Nested <marshmallow.fields.Nested` fields.

        Typically provides a reference object and will add the schema to the spec
        if it is not already present
        If a custom `schema_name_resolver` function returns `None` for the nested
        schema a JSON schema object will be returned

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def pluck2properties(self, field, **kwargs: typing.Any) -> dict:
        """Return a dictionary of properties from :class:`Pluck <marshmallow.fields.Pluck` fields.

        Pluck effectively trans-includes a field from another schema into this,
        possibly wrapped in an array (`many=True`).

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def list2properties(self, field, **kwargs: typing.Any) -> dict:
        """Return a dictionary of properties from :class:`List <marshmallow.fields.List>` fields.

        Will provide an `items` property based on the field's `inner` attribute

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def dict2properties(self, field, **kwargs: typing.Any) -> dict:
        """Return a dictionary of properties from :class:`Dict <marshmallow.fields.Dict>` fields.

        Only applicable for Marshmallow versions greater than 3. Will provide an
        `additionalProperties` property based on the field's `value_field` attribute

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def timedelta2properties(self, field, **kwargs: typing.Any) -> dict:
        """Return a dictionary of properties from :class:`TimeDelta <marshmallow.fields.TimeDelta>` fields.

        Adds a `x-unit` vendor property based on the field's `precision` attribute

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def enum2properties(self, field, **kwargs: typing.Any) -> dict:
        """Return a dictionary of properties from :class:`Enum <marshmallow.fields.Enum` fields.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass

    def datetime2properties(self, field, **kwargs: typing.Any) -> dict:
        """Return a dictionary of properties from :class:`DateTime <marshmallow.fields.DateTime` fields.

        :param Field field: A marshmallow field.
        :rtype: dict
        """
        pass


def make_type_list(types):
    """Return a list of types from a type attribute

    Since OpenAPI 3.1.0, "type" can be a single type as string or a list of
    types, including 'null'. This function takes a "type" attribute as input
    and returns it as a list, be it an empty or single-element list.
    This is useful to factorize type-conditional code or code adding a type.
    """
    pass


def make_min_max_attributes(validators, min_attr, max_attr) -> dict:
    """Return a dictionary of minimum and maximum attributes based on a list
    of validators. If either minimum or maximum values are not present in any
    of the validator objects that attribute will be omitted.

    :param validators list: A list of `Marshmallow` validator objects. Each
        objct is inspected for a minimum and maximum values
    :param min_attr string: The OpenAPI attribute for the minimum value
    :param max_attr string: The OpenAPI attribute for the maximum value
    """
    pass
