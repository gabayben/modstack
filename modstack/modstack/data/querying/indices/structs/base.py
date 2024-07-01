from abc import ABC
from dataclasses import field
from typing import Any, Literal, override
import uuid

from pydantic.main import IncEx

from modstack.typing import PydanticRegistry, Serializable
from modstack.utils.constants import SCHEMA_TYPE
from modstack.utils.string import type_name

class IndexStruct(Serializable, ABC):
    index_id: str = field(default_factory=lambda: str(uuid.uuid4()), kw_only=True)

    @override
    def model_dump(
        self,
        *,
        mode: Literal['json', 'python'] | str = 'python',
        include: IncEx = None,
        exclude: IncEx = None,
        context: dict[str, Any] | None = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal['none', 'warn', 'error'] = True,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        return {
            **super().model_dump(
                mode=mode,
                include=include,
                exclude=exclude,
                context=context,
                by_alias=by_alias,
                exclude_unset=exclude_unset,
                exclude_defaults=exclude_defaults,
                exclude_none=exclude_none,
                round_trip=round_trip,
                warnings=warnings,
                serialize_as_any=serialize_as_any
            ),
            SCHEMA_TYPE: type_name(self.__class__)
        }

class _IndexStructRegistry(PydanticRegistry[IndexStruct]):
    pass

index_struct_registry = _IndexStructRegistry()