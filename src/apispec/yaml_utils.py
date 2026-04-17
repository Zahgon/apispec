"""YAML utilities"""

from __future__ import annotations

import typing

import yaml

from apispec.utils import dedent, trim_docstring


def dict_to_yaml(dic: dict, yaml_dump_kwargs: typing.Any | None = None) -> str:
    """Serializes a dictionary to YAML."""
    pass


def load_yaml_from_docstring(docstring: str) -> dict:
    """Loads YAML from docstring."""
    pass


PATH_KEYS = {"get", "put", "post", "delete", "options", "head", "patch"}


def load_operations_from_docstring(docstring: str) -> dict:
    """Return a dictionary of OpenAPI operations parsed from a
    a docstring.
    """
    pass
