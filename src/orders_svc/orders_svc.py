import logging
from uuid import uuid4

from asgi_correlation_id import correlation_id

from . import orders_repo
from . import exceptions
from orders_svc.schemas import NewOrder, InventoryReservationRequest

logger = logging.getLogger(__name__)

async def get_all_orders(user_id: str = None):
    if user_id is not None:
        logger.info(f"Fetching orders for {user_id}")

        return await orders_repo.get_all_orders_by_user_id(user_id)

    logger.info(f"Fetching all orders")

    return await orders_repo.get_all_orders()

async def get_order_by_order_id(order_id: str):
    return await orders_repo.get_order_by_order_id(order_id)

async def request_inventory_check(new_order):
    reservation_id = str(uuid4())
    new_order_items = new_order.order_info.items

    request_reserve = InventoryReservationRequest(
        reservation_id = reservation_id,
        items = new_order_items
    ).model_dump()

    logger.info(
        "Sending order to Inventory for availability check",
        extra = {
            "event": "inventory_availability_request",
            "correlation_id": correlation_id.get(),
        }
    )

    res = await orders_repo.request_inventory_check(request_reserve)

    if res["msg"] == "ok":
        return await orders_repo.save_order(new_order, reservation_id)
    return res

async def validate_order(item_not_in_inv, item_not_enough_inv):
    order_errors = []

    if item_not_in_inv:
        logger.info(
            f"Order can not be completed. These items do not exist {item_not_in_inv}",
            extra = {
                "event": "create_order_failed",
                "correlation_id": correlation_id.get(),
                "items": item_not_in_inv
            }
        )

        items_not_found_error_msg = {
            "error": "ITEMS_NOT_FOUND",
            "msg": f"These items were not found {item_not_in_inv}"
        }

        order_errors.append(items_not_found_error_msg)

    if item_not_enough_inv:
        logger.info(
            f"Order can not be completed. Insufficient inv for items {item_not_enough_inv}",
            extra = {
                "event": "create_order_failed",
                "correlation_id": correlation_id.get(),
                "items": item_not_enough_inv,
            }
        )

        items_not_enough_inv_msg = {
            "error": "INSUFFICIENT_INV",
            "msg": f"These items don't have enough inv {item_not_enough_inv}"
        }
        order_errors.append(items_not_enough_inv_msg)

    if order_errors:
        order_error_msg = {
            "error": "ORDER_UNPROCESSABLE",
            "msg": "Unable to process this order. See details below",
        }
        order_error_msg["details"] = order_errors

        raise exceptions.OrderUnprocessable(
            detail = order_error_msg
        )

    return True

async def create_order(new_order: NewOrder):
    return await request_inventory_check(new_order)

async def cancel_order(order_id):
    cancelable_orders = [
        "created",
        "pending"
    ]

    res = await get_order_by_order_id(order_id)

    if res is None:
        logger.info(
            f"Cancel order request failed. Order {order_id} not found.",
            extra = {
                "event": "cancel_order_failed",
                "correlation_id": correlation_id.get(),
                "order_id": order_id
            }
        )

        raise exceptions.OrderNotFound(
            order_id = order_id,
            detail = "Order ID does not exist"
        )

    order_status = res.get("status")

    if order_status not in cancelable_orders:
        logger.info(
            f"Order can not be cancelled. Current state: {order_status}",
            extra = {
                "event": "cancel_order_failed",
                "correlation_id": correlation_id.get(),
                "order_id": order_id
            })

        raise exceptions.OrderNotCancelable(
            order_id = order_id,
            detail = f"Order is in a {order_status} state. Can not cancel"
        )

    return await orders_repo.cancel_order(order_id)
