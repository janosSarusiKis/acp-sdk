from functools import wraps
from typing import Any, Type

class ManifestMarker:
    input_class: Type | None = None
    output_class: Type | None = None
    config_class: Type | None = None

    @classmethod
    def input(cls, klass: Type) -> Type:
        cls.input_class = klass
        return klass

    @classmethod
    def output(cls, klass: Type) -> Type:
        cls.output_class = klass
        return klass

    @classmethod
    def config(cls, klass: Type) -> Type:
        cls.config_class = klass
        return klass