from abc import ABC, abstractmethod
from enum import StrEnum
import logging
import os
from typing import Any

from pydantic import PrivateAttr

from modstack.core.typing import Serializable

logger = logging.getLogger(__name__)

class SecretType(StrEnum):
    TOKEN = 'token'
    ENV_VAR = 'env_var'

class Secret(Serializable, ABC):
    @property
    @abstractmethod
    def secret_type(self) -> str:
        pass

    @staticmethod
    def from_token(token: str) -> 'Secret':
        return TokenSecret(token)

    @staticmethod
    def from_env_var(variables: str | list[str], strict: bool = True) -> 'Secret':
        return EnvVarSecret(
            tuple([variables] if isinstance(variables, str) else variables),
            strict=strict
        )

    @abstractmethod
    def resolve_value(self) -> Any | None:
        pass

class TokenSecret(Secret):
    _token: str = PrivateAttr()

    @property
    def secret_type(self) -> str:
        return SecretType.TOKEN

    def __init__(self, token: str, **kwargs):
        super().__init__(_token=token, **kwargs)

    def resolve_value(self) -> Any | None:
        return self._token

class EnvVarSecret(Secret):
    variables: tuple[str, ...]
    strict: bool

    @property
    def secret_type(self) -> str:
        return SecretType.ENV_VAR

    def __init__(
        self,
        variables: tuple[str, ...],
        strict: bool = True,
        **kwargs
    ):
        super().__init__(variables=variables, strict=strict, **kwargs)

    def __post_init__(self):
        if len(self.variables) == 0:
            raise ValueError('One or more environment variables must be provided for the secret.')

    def resolve_value(self) -> Any | None:
        out: Any | None = None
        for var in self.variables:
            out = os.getenv(var)
            if out is not None:
                break
        if out is None:
            msg = f'None of the following environment variables are set: {', '.join(self.variables)}.'
            if self.strict:
                raise ValueError(msg)
            else:
                logger.warning(msg)
        return out