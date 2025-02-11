# 新增分頁工具類
from typing import Generic, TypeVar
from pydantic.generics import GenericModel

T = TypeVar('T')

class PaginatedResponse(GenericModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    per_page: int

class Paginator:
    def __init__(self, query, page: int = 1, per_page: int = 20):
        self.query = query
        self.page = page
        self.per_page = per_page
    
    async def paginate(self) -> PaginatedResponse:
        return PaginatedResponse(
            data=await self.query.offset((self.page-1)*self.per_page).limit(self.per_page),
            total=await self.query.count(),
            page=self.page,
            per_page=self.per_page
        ) 