from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from bson import ObjectId
from pydantic import BaseModel

from internals.db import AvatarImage

from .common import AvatarResponse

__all__ = (
    "MerchantSearch",
    "FoodItemSearch",
    "ProjectionMerchant",
    "ProjectionFoodItem",
    "MultiSearchResponse",
)


@dataclass
class MerchantSearch:
    id: str
    name: str
    avatar: AvatarResponse


class ProjectionMerchant(BaseModel):
    id: ObjectId
    merchant_id: UUID
    name: str
    avatar: AvatarImage

    def to_response(self) -> MerchantSearch:
        return MerchantSearch(
            id=str(self.merchant_id),
            name=self.name,
            avatar=AvatarResponse.from_db(self.avatar, "merchant"),
        )

    class Config:
        arbitrary_types_allowed = True


@dataclass
class FoodItemSearch:
    id: str
    name: str
    description: str
    price: float
    avatar: AvatarResponse


class ProjectionFoodItem(BaseModel):
    id: ObjectId
    item_id: UUID
    name: str
    description: str
    price: float
    avatar: AvatarImage

    def to_response(self) -> FoodItemSearch:
        return FoodItemSearch(
            id=str(self.item_id),
            name=self.name,
            description=self.description,
            price=self.price,
            avatar=AvatarResponse.from_db(self.avatar, "items"),
        )

    class Config:
        arbitrary_types_allowed = True


class MultiSearchResponse(TypedDict):
    merchants: list[MerchantSearch]
    items: list[FoodItemSearch]
