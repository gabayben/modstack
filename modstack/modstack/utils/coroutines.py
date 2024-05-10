import asyncio
from concurrent.futures import Future, ThreadPoolExecutor
from contextvars import copy_context
from typing import Any, Coroutine, cast

def run_sync[T](
    coroutine: Coroutine[Any, Any, T],
    max_workers: int | None = None
) -> T:
    context = copy_context()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future: Future = executor.submit(context.run, asyncio.run, coroutine) # type: ignore[call-args]
            return cast(T, future.result())
    else:
        return context.run(asyncio.run, coroutine)