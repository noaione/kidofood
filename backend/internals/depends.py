from enum import Enum
from typing import Optional, TypedDict
from fastapi import Query


__all__ = (
    "SortDirection",
    "PaginationParams",
    "pagination_parameters",
)


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"
    ASCENDING = "asc"
    DESCENDING = "desc"


class PaginationParams(TypedDict):
    limit: int
    cursor: Optional[str]
    sort: SortDirection


def pagination_parameters(
    max_limit: int = 100,
    default_limit: int = 20,
):
    """
    Pagination parameters for a route.
    """

    async def inner(
        limit: int = Query(default_limit, ge=1, le=max_limit),
        cursor: Optional[str] = None,
        sort: SortDirection = SortDirection.ASC,
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

    return inner
