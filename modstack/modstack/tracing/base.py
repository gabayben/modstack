"""
Taken from Haystack - https://github.com/deepset-ai/haystack/blob/main/haystack/tracing/tracer.py
SPDX-FileCopyrightText: 2022-present deepset GmbH <info@deepset.ai>
SPDX-License-Identifier: Apache-2.0
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
import os
from typing import Any, Generator

from modstack.constants import MODSTACK_CONTENT_TRACING_ENABLED_ENV_VAR

class Span(ABC):
    @property
    def content_tracing_enabled(self) -> bool:
        return self._tracer.content_tracing_enabled

    def __init__(self, tracer: 'Tracer'):
        self._tracer = tracer

    @abstractmethod
    def set_tag(self, key: str, value: Any) -> None:
        """
        Set a single tag on the span.

        Note that the value will be serialized to a string, so it's best to use simple types like strings, numbers, or
        booleans.

        :param key: the name of the tag.
        :param value: the value of the tag.
        """

    def set_tags(self, tags: dict[str, Any]) -> None:
        """
        Set multiple tags on the span.

        :param tags: a mapping of tag names to tag values.
        """
        for key, value in tags.items():
            self.set_tag(key, value)

    def raw_span(self) -> Any:
        """
        Provides access to the underlying span object of the tracer.

        Use this if you need full access to the underlying span object.

        :return: The underlying span object.
        """
        return self

    def set_content_tag(self, key: str, value: Any) -> None:
        """
        Set a single tag containing content information.

        Content is sensitive information such as
        - the content of a query
        - the content of a document
        - the content of an answer

        By default, this behavior is disabled. To enable it
        - set the environment variable `HAYSTACK_CONTENT_TRACING_ENABLED` to `true` or
        - override the `set_content_tag` method in a custom tracer implementation.

        :param key: the name of the tag.
        :param value: the value of the tag.
        """
        if self.content_tracing_enabled:
            self.set_tag(key, value)

    def get_correlation_data_for_logs(self) -> dict[str, Any]:
        """
        Return a dictionary with correlation data for logs.

        This is useful if you want to correlate logs with traces.
        """
        return {}

class Tracer(ABC):
    @property
    def content_tracing_enabled(self) -> bool:
        return os.getenv(MODSTACK_CONTENT_TRACING_ENABLED_ENV_VAR, 'false').lower() == 'true'

    @abstractmethod
    @contextmanager
    def trace(
        self,
        operation_name: str,
        tags: dict[str, Any] | None = None
    ) -> Generator[Span, Any, Any]:
        """
        Trace the execution of a block of code.

        :param operation_name: the name of the operation being traced.
        :param tags: tags to apply to the newly created span.
        :return: the newly created span.
        """

    @abstractmethod
    def current_span(self) -> Span | None:
        """
        Returns the currently active span. If no span is active, returns `None`.

        :return: Currently active span or `None` if no span is active.
        """

class NullSpan(Span):
    def set_tag(self, key: str, value: Any) -> None:
        pass

class NullTracer(Tracer):
    @contextmanager
    def trace(
        self,
        operation_name: str,
        tags: dict[str, Any] | None = None
    ) -> Generator[Span, Any, Any]:
        yield NullSpan(self)

    def current_span(self) -> Span | None:
        yield NullSpan(self)

class ProxyTracer(Tracer):
    def __init__(self, provided_tracer: Tracer):
        self.provided_tracer = provided_tracer

    @contextmanager
    def trace(
        self,
        operation_name: str,
        tags: dict[str, Any] | None = None
    ) -> Generator[Span, Any, Any]:
        with self.provided_tracer.trace(operation_name, tags=tags) as span:
            yield span

    def current_span(self) -> Span | None:
        return self.provided_tracer.current_span()

tracer = ProxyTracer(NullTracer())