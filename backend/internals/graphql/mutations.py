"""
MIT License

Copyright (c) 2022-present noaione

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import logging
from typing import Literal, Optional, Tuple, TypeVar, Union, cast
from uuid import UUID

import strawberry as gql
from beanie import WriteRules
from beanie.operators import In as OpIn
from bson import ObjectId

from internals.db import AvatarImage
from internals.db import FoodItem as FoodItemDB
from internals.db import FoodOrder as FoodOrderDB
from internals.db import FoodOrderItem as FoodOrderItemDB
from internals.db import Merchant as MerchantDB
from internals.db import PaymentReceipt as PaymentReceiptDB
from internals.db import User as UserDB
from internals.enums import ApprovalStatus, AvatarType, UserType
from internals.session import encrypt_password, verify_password
from internals.utils import make_uuid, to_uuid

from .enums import ApprovalStatusGQL, OrderStatusGQL, UserTypeGQL
from .files import handle_image_upload
from .models import (
    FoodItemGQL,
    FoodItemInputGQL,
    FoodOrderGQL,
    FoodOrderItemInputGQL,
    MerchantInputGQL,
    PaymentMethodGQL,
    UserGQL,
    UserInputGQL,
)

__all__ = (
    "mutate_login_user",
    "mutate_register_user",
    "mutate_apply_new_merchant",
    "mutate_update_merchant",
    "mutate_update_user",
    "mutate_make_new_order",
    "mutate_update_order_status",
    "mutate_new_food_item",
)

logger = logging.getLogger("GraphQL.Mutations")
ResultT = TypeVar("ResultT")
ResultOrT = Union[Tuple[Literal[False], str], Tuple[Literal[True], ResultT]]


async def mutate_login_user(
    email: str,
    password: str,
) -> ResultOrT[UserGQL]:
    user = await UserDB.find_one(UserDB.email == email)
    if not user:
        return False, "User with associated email not found"

    is_verify, new_password = await verify_password(password, user.password)
    if not is_verify:
        return False, "Password is not correct"
    if new_password is not None and user is not None:
        user.password = new_password
        await user.save_changes()
    return True, UserGQL.from_db(user)


async def mutate_register_user(
    email: str,
    password: str,
    name: str,
    type: UserTypeGQL = UserTypeGQL.CUSTOMER,
) -> ResultOrT[UserDB]:
    user = await UserDB.find_one(UserDB.email == email)
    if user:
        return False, "User with associated email already exists"

    hash_paas = await encrypt_password(password)
    new_user = UserDB(email=email, password=hash_paas, name=name, avatar=AvatarImage(), type=type)
    await new_user.save()
    return True, new_user


async def mutate_apply_new_merchant(
    user: UserGQL,
    merchant: MerchantInputGQL,
):
    logger.info(f"Applying new merchant for {user.id}")
    if user.merchant_id is not None:
        logger.error(f"User<{user.id}>: Already have merchant account")
        return False, "User already has a merchant account", None
    name = merchant.name if merchant.name is not gql.UNSET else None
    description = merchant.description if merchant.description is not gql.UNSET else None
    address = merchant.address if merchant.address is not gql.UNSET else None
    avatar = merchant.avatar if merchant.avatar is not gql.UNSET else None

    if name is None:
        logger.error(f"User<{user.id}>: Merchant name is required")
        return False, "Merchant name is required", None
    description = description or ""
    if address is None:
        logger.error(f"User<{user.id}>: Merchant address is required")
        return False, "Merchant address is required", None

    user_acc = await UserDB.find_one(UserDB.user_id == user.id)
    if user_acc is None:
        logger.error(f"User<{user.id}>: User not found at database")
        return False, "User not found", None
    if user_acc.merchant is not None:
        logger.error(f"User<{user.id}>: Already have merchant account")
        return False, "User already has a merchant account", None
    avatar_ingfo = AvatarImage(key="", format="")
    merchant_uuid = cast(UUID, make_uuid(False))
    if avatar is not None:
        avatar_upload = await handle_image_upload(avatar, str(merchant_uuid), AvatarType.MERCHANT)
        avatar_ingfo = AvatarImage(
            key=avatar_upload.filename,
            format=avatar_upload.extension.lstrip("."),
        )
    new_merchant = MerchantDB(
        mercahnt_id=merchant_uuid,
        name=cast(str, name),
        description=cast(str, description),
        address=cast(str, address),
        avatar=avatar_ingfo,
    )
    user_acc.merchant = new_merchant  # type: ignore
    logger.info(f"User<{user.id}>: Saving...")
    await user_acc.save(link_rule=WriteRules.WRITE)
    logger.info(f"User<{user.id}>: Saved")
    return True, new_merchant, user_acc


async def mutate_update_merchant(
    id: gql.ID,
    user: UserGQL,
    merchant: MerchantInputGQL,
    approval: Optional[ApprovalStatus] = gql.UNSET,
) -> ResultOrT[MerchantDB]:
    if merchant.is_unset():
        logger.warning(f"Merchant<{id}>: No changes to update")
        return False, "No changes to Merchant data"
    logger.info(f"Trying to find merchant: {id}")
    merchant_acc = await MerchantDB.find_one(MerchantDB.merchant_id == to_uuid(id))
    if merchant_acc is None:
        logger.error(f"Merchant<{id}>: Merchant not found")
        return False, "Merchant not found"
    # Check if user is the owner of the merchant or is ADMIN
    if user.type != UserType.ADMIN and user.merchant_id != merchant_acc.merchant_id:
        logger.error(f"Merchant<{id}>: User<{user.id}> is not the owner of the merchant")
        return False, "User is not the owner of the merchant"
    if user.merchant_id != str(merchant_acc.id):
        logger.error(f"Merchant<{id}>: User<{user.id}> is not the owner, checking admin status")
        if user.type != UserType.ADMIN:
            logger.error(f"Merchant<{id}>: User<{user.id}> is also not an admin, returning error")
            return False, "User is not the owner of this merchant"
    mc_name = merchant.name if merchant.name is not gql.UNSET else None
    mc_description = merchant.description if merchant.description is not gql.UNSET else None
    mc_address = merchant.address if merchant.address is not gql.UNSET else None
    mc_phone = merchant.phone if merchant.phone is not gql.UNSET else None
    mc_email = merchant.email if merchant.email is not gql.UNSET else None
    mc_website = merchant.website if merchant.website is not gql.UNSET else None
    avatar = merchant.avatar if merchant.avatar is not gql.UNSET else None

    approval = approval if approval is not gql.UNSET else None

    if mc_name is not None:
        merchant_acc.name = mc_name
    if mc_description is not None:
        merchant_acc.description = mc_description
    if mc_address is not None:
        merchant_acc.address = mc_address
    if mc_phone is not None:
        merchant_acc.phone = mc_phone
    if mc_email is not None:
        merchant_acc.email = mc_email
    if mc_website is not None:
        merchant_acc.website = mc_website
    if approval is not None and user.type != UserType.ADMIN:
        logger.error(f"Merchant<{id}>: Only admin can change approval status")
        return False, "Only admin can change approval status"
    elif approval is not None and user.type == UserType.ADMIN:
        merchant_acc.approved = approval
    if avatar is not None:
        avatar_upload = await handle_image_upload(avatar, str(merchant_acc.merchant_id), AvatarType.MERCHANT)
        avatar_ingfo = AvatarImage(
            key=avatar_upload.filename,
            format=avatar_upload.extension.lstrip("."),
        )
        merchant_acc.avatar = avatar_ingfo

    logger.info(f"Merchant<{id}>: Saving updates...")
    await merchant_acc.save_changes()

    return True, merchant_acc


async def mutate_update_user(
    id: gql.ID,
    user: UserInputGQL,
) -> ResultOrT[UserGQL]:
    if user.is_unset():
        logger.warning(f"User<{id}>: No changes to update")
        return False, "No changes to User data"
    logger.info(f"Trying to find user: {id}")
    user_acc = await UserDB.find_one(UserDB.user_id == to_uuid(id))
    if user_acc is None:
        logger.error(f"User<{id}>: User not found")
        return False, "User not found"
    name = user.name if user.name is not gql.UNSET else None
    avatar = user.avatar if user.avatar is not gql.UNSET else None
    password = user.password if user.password is not gql.UNSET else None
    new_password = user.new_password if user.new_password is not gql.UNSET else None
    if name is not None:
        user_acc.name = name
    if password is not None and new_password is None:
        logger.error(f"User<{id}>: New password is not provided")
        return False, "New password is not provided"
    if new_password is not None and password is None:
        logger.error(f"User<{id}>: Current password is not provided")
        return False, "Current password is not provided"
    if password is not None and new_password is not None:
        is_correct, _ = await verify_password(password, user_acc.password)
        if not is_correct:
            logger.error(f"User<{id}>: Incorrect password")
            return False, "Incorrect current password"
        new_pass_hash = await encrypt_password(new_password)
        user_acc.password = new_pass_hash
    if avatar is not None:
        avatar_upload = await handle_image_upload(avatar, str(user_acc.user_id), AvatarType.MERCHANT)
        avatar_ingfo = AvatarImage(
            key=avatar_upload.filename,
            format=avatar_upload.extension.lstrip("."),
        )
        user_acc.avatar = avatar_ingfo
    logger.info(f"User<{id}>: Saving updates...")
    await user_acc.save_changes()
    return True, UserGQL.from_db(user_acc)


async def mutate_make_new_order(
    user: UserGQL,
    items: list[FoodOrderItemInputGQL],
    payment: PaymentMethodGQL,
) -> ResultOrT[FoodOrderGQL]:
    # Let's fetch the items first
    items_ids: list[UUID] = []
    items_quant_map: dict[str, int] = {}
    for idx, item in enumerate(items):
        try:
            items_ids.append(to_uuid(item.id))
        except ValueError:
            return False, f"Invalid ID for items[{idx}]: {item.id}"
        items_quant_map[item.id] = item.quantity
    logger.info(f"Fetching user information for: {user.id}")
    user_info = await UserDB.find_one(UserDB.user_id == user.id)
    if user_info is None:
        logger.warning(f"User<{user.id}>: User not found")
        return False, "User not found"
    logger.info(f"Trying to find items: {items_ids!r}")
    items_data = await FoodItemDB.find(OpIn(FoodItemDB.item_id, items_ids)).to_list()
    merchants = []
    mapped_keys = []
    remapped_items: list[FoodOrderItemDB] = []
    total_amount = 0
    for item in items_data:
        mapped_keys.append(str(item.item_id))
        merch_id = str(item.merchant.ref.id)
        it_quantity = items_quant_map[str(item.item_id)]
        remapped_items.append(FoodOrderItemDB(data=item, quantity=it_quantity))  # type: ignore
        if merch_id not in merchants:
            merchants.append(merch_id)
        total_amount += item.price * it_quantity
    if len(merchants) > 1:
        logger.warning(f"User<{user.id}>: Items from multiple merchants")
        return False, "Items must be from the same merchant!"
    merchant_info = await items_data[0].merchant.fetch()
    if not isinstance(merchant_info, MerchantDB):
        logger.error(f"User<{user.id}>: Merchant not found for the selected item!")
        return False, "Unable to find the associated merchant for that item, might be deleted?"
    invalid_ids = []
    for item in items_ids:
        if str(item) not in mapped_keys:
            invalid_ids.append(str(item))
    if invalid_ids:
        return False, f"Invalid IDs for items: {invalid_ids!r}"
    pay_receipt = PaymentReceiptDB(method=payment.method, amount=total_amount, data=payment.data)
    food_order = FoodOrderDB(
        items=remapped_items,
        user=user_info,
        rider=None,
        merchant=merchant_info,
        target_address=user_info.address,
        receipt=pay_receipt,
    )
    await food_order.save(link_rule=WriteRules.DO_NOTHING)
    return True, FoodOrderGQL.from_db(food_order)


async def mutate_update_order_status(
    id: gql.ID,
    status: OrderStatusGQL,
) -> ResultOrT[FoodOrderGQL]:
    logger.info(f"Trying to find order: {id}")
    order = await FoodOrderDB.find_one(FoodOrderDB.order_id == to_uuid(id))
    if order is None:
        logger.warning(f"Order<{id}>: Order not found")
        return False, "Order not found"
    logger.info(f"Order<{id}>: Updating status to {status}")
    # Check if status update doable.
    _CANCEL = (
        OrderStatusGQL.PROCESSING,
        OrderStatusGQL.DELIVERING,
        OrderStatusGQL.REJECTED,
        OrderStatusGQL.CANCELLED,
        OrderStatusGQL.CANCELED_MERCHANT,
        OrderStatusGQL.PROBLEM_FAIL_TO_DELIVER,
        OrderStatusGQL.DONE,
    )
    _UNCHANGEABLE = (
        OrderStatusGQL.REJECTED,
        OrderStatusGQL.CANCELLED,
        OrderStatusGQL.CANCELED_MERCHANT,
        OrderStatusGQL.DONE,
        OrderStatusGQL.PROBLEM_FAIL_TO_DELIVER,
        OrderStatusGQL.PROBLEM_MERCHANT,
    )
    if order.status in _UNCHANGEABLE:
        logger.warning(f"Order<{id}>: Status is unchangeable")
        return False, "Status is unchangeable for this order"
    if status in (OrderStatusGQL.CANCELED_MERCHANT, OrderStatusGQL.CANCELLED):
        if order.status in _CANCEL:
            logger.warning(f"Order<{id}>: Invalid status update")
            return False, "Unable to cancel order anymore!"
    if status == order.status:
        logger.warning(f"Order<{id}>: Status is already {status}")
        return False, "Status is already set to that value"

    order.status = status
    await order.save_changes()
    return True, FoodOrderGQL.from_db(order)


async def mutate_new_food_item(
    user: UserGQL,
    item: FoodItemInputGQL,
) -> ResultOrT[FoodItemGQL]:
    if user.merchant_id is None:
        return False, "You are not a merchant!"

    merchant = await MerchantDB.find_one(MerchantDB.id == ObjectId(user.merchant_id))
    if merchant is None:
        return False, "Your merchant acccout cannot be found!"
    if merchant.approved != ApprovalStatusGQL.APPROVED:
        return False, "Your merchant account is not approved yet!"

    description = item.description if item.description is not gql.UNSET else None
    image = item.image if item.image is not gql.UNSET else None

    img_info = AvatarImage(key="", format="")
    if image is not None:
        avatar_upload = await handle_image_upload(image, str(merchant.id), AvatarType.ITEMS)
        img_info = AvatarImage(
            key=avatar_upload.filename,
            format=avatar_upload.extension.lstrip("."),
        )

    food_item = FoodItemDB(
        name=item.name,
        description=description or "",
        stock=item.stock,
        price=item.price,
        type=item.type,
        merchant=merchant,
        image=img_info,
    )
    await food_item.save(link_rule=WriteRules.DO_NOTHING)
    return True, FoodItemGQL.from_db(food_item)
