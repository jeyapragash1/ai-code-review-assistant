from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1, le=1_000_000)
    page_size: int = Field(default=20, ge=1, le=100)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


def paginated(items: list[T], total: int, params: PageParams) -> Page[T]:
    return Page(items=items, total=total, page=params.page, page_size=params.page_size,
                total_pages=(total + params.page_size - 1) // params.page_size)
