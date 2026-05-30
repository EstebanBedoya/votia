"""FastAPI dependencies. The container is built once and reused (it holds the
SDK clients). Tests override ``get_container`` to inject fakes."""

from __future__ import annotations

from functools import lru_cache

from dr_votia.entrypoints.container import Container, build_container


@lru_cache(maxsize=1)
def get_container() -> Container:
    return build_container()
