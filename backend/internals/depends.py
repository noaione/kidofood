from enum import Enum
from typing import Any, Callable, Coroutine, Literal, Optional, TypeVar, TypedDict, Union, overload
from fastapi import Query


__all__ = (
    "SortDirection",
    "PaginationParams",
    "pagination_parameters",
)

T = TypeVar("T")
Coro = Coroutine[Any, Any, T]


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"
    ASCENDING = "asc"
    DESCENDING = "desc"


class PaginationParams(TypedDict):
    limit: int
    cursor: Optional[str]
    sort: SortDirection


class DualPaginationParams(TypedDict):
    limit: int
    cursor_a: Optional[str]
    cursor_b: Optional[str]
    sort: SortDirection


@overload
def pagination_parameters(
    max_limit: int = ...,
    default_limit: int = ...,
    dual_cursor: Literal[False] = ...,
) -> Callable[[int, Optional[str], SortDirection], Coro[PaginationParams]]:
    ...


@overload
def pagination_parameters(
    max_limit: int = ...,
    default_limit: int = ...,
    dual_cursor: Literal[True] = ...,
) -> Callable[[int, Optional[str], Optional[str], SortDirection], Coro[DualPaginationParams]]:
    ...


def pagination_parameters(
    max_limit: int = 100,
    default_limit: int = 20,
    dual_cursor: bool = False,
) -> Callable[..., Coro[Union[PaginationParams, DualPaginationParams]]]:
    """
    Pagination parameters for a route.
    """

    async def inner(
        limit: int = Query(default_limit, description="Limit per page of the pagination", ge=1, le=max_limit),
        cursor: Optional[str] = Query(None, description="Next cursor for the pagination"),
        sort: SortDirection = Query(SortDirection.ASCENDING, description="Sort direction for the pagination"),
    ) -> PaginationParams:
        if limit > max_limit:
            limit = max_limit
        if limit < 1:
            limit = 1
        return {
            "limit": limit,
            "cursor": cursor,
            "sort": sort,
        }

    async def inner_dual(
        limit: int = Query(default_limit, description="Limit per page of the pagination", ge=1, le=max_limit),
        cursor_a: Optional[str] = Query(None, description="Next cursor A for the pagination"),
        cursor_b: Optional[str] = Query(None, description="Next cursor B for the pagination"),
        sort: SortDirection = Query(SortDirection.ASCENDING, description="Sort direction for the pagination"),
    ) -> DualPaginationParams:
        if limit > max_limit:
            limit = max_limit
        if limit < 1:
            limit = 1
        return {
            "limit": limit,
            "cursor_a": cursor_a,
            "cursor_b": cursor_b,
            "sort": sort,
        }

    return inner if not dual_cursor else inner_dual
