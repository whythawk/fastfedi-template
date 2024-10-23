from __future__ import annotations
from typing import Any
from typing_extensions import Annotated
from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationError,
)
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue
from babel import Locale  # , UnknownLocaleError
from sqlalchemy_utils import Country


class BaseSchema(BaseModel):
    @property
    def as_db_dict(self):
        to_db = self.model_dump(exclude_defaults=True, exclude_none=True, exclude={"identifier, id"})
        for key in ["id", "identifier"]:
            if key in self.model_dump().keys():
                to_db[key] = self.model_dump()[key].hex
        return to_db


# ======================================================================================================================
# THIRD-PARTY TYPES FOR LOCALE AND COUNTRY
# https://docs.pydantic.dev/latest/concepts/types/#handling-third-party-types
# https://docs.pydantic.dev/latest/concepts/json_schema/#implementing-__get_pydantic_json_schema__
class _LocalePydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        A Locale Annotation which supports integrations with BaseModel
        * str will be parsed as `Locale` instances
        * `Locale` instances will be parsed as `Locale` instances without any changes
        * Nothing else will pass validation
        * Serialization will always return just a str
        """

        def validate_type(value: str | Locale) -> Locale:
            if isinstance(value, str):
                return Locale.parse(value, sep="-")
            return Locale(str(value).lower())

        from_instance_schema = core_schema.chain_schema(
            [
                core_schema.no_info_plain_validator_function(validate_type),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_instance_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(Locale),
                    from_instance_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance).replace("_", "-")
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `str`
        json_schema = handler(core_schema.str_schema())
        json_schema["examples"] = ["fr"]
        return json_schema


class _CountryPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """
        A Country Annotation which supports integrations with BaseModel
        * str will be parsed as `Country` instances
        * `Country` instances will be parsed as `Country` instances without any changes
        * Nothing else will pass validation
        * Serialization will always return just a str
        """

        def validate_type(value: str | Country) -> Country:
            if isinstance(value, str):
                return Country(value.upper())
            if isinstance(value, Country):
                return Country(value.code)

        from_instance_schema = core_schema.chain_schema(
            [
                core_schema.no_info_plain_validator_function(validate_type),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_instance_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(Country),
                    from_instance_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda instance: str(instance)),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `str`
        json_schema = handler(core_schema.str_schema())
        json_schema["examples"] = ["FR"]
        return json_schema


class _CountryListPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def validate_type(value: list[str] | list[Country]) -> list[Country]:
            if not isinstance(value, list):
                raise ValidationError("Input should be an instance of `list[Country]`")
            validated = []
            for v in value:
                if isinstance(v, str):
                    validated.append(Country(v.upper()))
                if isinstance(v, Country):
                    validated.append(Country(v.code))
            return validated

        from_instance_schema = core_schema.chain_schema(
            [
                core_schema.no_info_plain_validator_function(validate_type),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=from_instance_schema,
            python_schema=core_schema.union_schema(
                [
                    # check if it's an instance first before doing any further work
                    core_schema.is_instance_schema(list),
                    from_instance_schema,
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(lambda instance: [str(i) for i in instance]),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        # Use the same schema that would be used for `str`
        json_schema = handler(core_schema.list_schema())
        json_schema["examples"] = [["FR", "GB", "ZA"]]
        return json_schema


# ANNOTATED WRAPPERS FOR USE IN BASEMODELS
LocaleType = Annotated[Locale, _LocalePydanticAnnotation]
CountryType = Annotated[Country, _CountryPydanticAnnotation]
CountryListType = Annotated[list[Country], _CountryListPydanticAnnotation]

# ======================================================================================================================
