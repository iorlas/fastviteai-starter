import functools
import inspect
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


def cached(cache_dir: Path, key_fn: Callable[..., str]) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache_key = key_fn(*args, **kwargs)
            cache_file = cache_dir / f"{cache_key}.json"

            if cache_file.exists():
                cached_data = cache_file.read_text()

                sig = inspect.signature(func)
                return_type = sig.return_annotation

                if inspect.isclass(return_type) and issubclass(return_type, BaseModel):
                    return return_type.model_validate_json(cached_data)

                import json

                return json.loads(cached_data)

            result = await func(*args, **kwargs)

            cache_dir.mkdir(parents=True, exist_ok=True)

            if isinstance(result, BaseModel):
                cache_file.write_text(result.model_dump_json(indent=2))
            else:
                import json

                cache_file.write_text(json.dumps(result, indent=2))

            return result

        return wrapper

    return decorator
