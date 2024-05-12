from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any

from modstack.typing import Serializable

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
    token: str

    @property
    def secret_type(self) -> str:
        return SecretType.TOKEN

    def __init__(self, token: str, **kwargs):
        super().__init__(token=token, **kwargs)

    def resolve_value(self) -> Any | None:
        pass

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

    def resolve_value(self) -> Any | None:
        pass