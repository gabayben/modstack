from typing import Any, override

from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_none

from modstack.core.modules import DecoratorBase, Module
from modstack.core.typing import AfterRetryFailure, Effect, Effects, RetryStrategy, StopStrategy, WaitStrategy
from modstack.core.typing.vars import In, Out

class Retry(DecoratorBase[In, Out]):
    retry: RetryStrategy
    stop: StopStrategy
    wait: WaitStrategy
    after: AfterRetryFailure | None

    @property
    def _retry_kwargs(self) -> dict[str, Any]:
        return {
            'reraise': True,
            'retry': self.retry,
            'stop': self.stop,
            'wait': self.wait,
            'after': self.after
        }

    def __init__(
        self,
        bound: Module[In, Out],
        retry: RetryStrategy | None = None,
        stop: StopStrategy | None = None,
        wait: WaitStrategy | None = None,
        after: AfterRetryFailure | None = None
    ):
        super().__init__(
            bound=bound,
            retry=retry or retry_if_exception_type((Exception,)),
            stop=stop or stop_after_attempt(3),
            wait=wait or wait_none(),
            after=after
        )

    @override
    def forward(self, data: In, **kwargs) -> Effect[Out]:
        async def _ainvoke() -> Out:
            async for attempt in AsyncRetrying(**self._retry_kwargs):
                with attempt:
                    result = await super().ainvoke(data, retry_state=attempt.retry_state, **kwargs)
                if attempt.retry_state.outcome and not attempt.retry_state.outcome.failed:
                    attempt.retry_state.set_result(result)
            return result

        return Effects.Async(_ainvoke)