import logging

from asgi_correlation_id import correlation_id

from . import orders_json_srv_repo as orders_repo
from . import exceptions

logger = logging.getLogger(__name__)

async def get_all_orders(user_id: str = None):
    if user_id is not None:
        logger.info(f"Fetching orders for {user_id}")

        res = await orders_repo.get_all_orders_by_user_id(user_id)
    else:
        logger.info(f"Fetching all orders")

        res = await orders_repo.get_all_orders()

    return res

async def get_order_by_order_id(order_id: str):
    return await orders_repo.get_order_by_order_id(order_id)

async def check_inv_and_stock(new_order):
    logger.info(
        "Checking inventory availability",
        extra = {
            "event": "inventory_availability_request",
            "correlation_id": correlation_id.get(),
        }
    )
    item_not_in_inv = []
    item_not_enough_inv = []

    for item in new_order.order_info.items:
        logger.info(f"OrderItem: Item {item.book_id}: qty {item.quantity}")
        res = await orders_repo.get_item(item.book_id)

        if res is None:
            logger.info(
                f"Item {item.book_id} not found in inv",
                extra = {
                    "event": "item_not_found_in_inventory",
                    "correlation_id": correlation_id.get(),
                    "book_id": item.book_id
                }
            )
            item_not_in_inv.append(item.book_id)
            continue

        item_inv_qty = res.get('stock_quantity')
        logger.info(f"Item {item.book_id} current stock {item_inv_qty}")

        if item_inv_qty < item.quantity:
            logger.info(
                f"Item {item.book_id} does not have enough inv",
                extra = {
                    "event": "inventory_availability_request",
                    "correlation_id": correlation_id.get(),
                    "book_id": item.book_id,
                    "current_inventory": item_inv_qty,
                    "requested_inventory": item.quantity
                })
            item_not_enough_inv.append(item.book_id)

    return item_not_in_inv, item_not_enough_inv

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

# big problem: what if i reserve but can't post order and therefore give back reserve
# maybe need a reservation system
async def create_order(new_order):
    item_not_in_inv, item_not_enough_inv = await check_inv_and_stock(new_order)

    order_validated = await validate_order(item_not_in_inv, item_not_enough_inv)

    if not order_validated: return

    logger.info(
        "Order has been validated. Reserving items",
        extra = {
            "event": "create_order_validated",
            "correlation_id": correlation_id.get(),
            "user_id": new_order.user_id
        }
    )

    for item in new_order.order_info.items:
        book_id = item.book_id
        quantity = item.quantity

        # try/catch here;retry
        res = await orders_repo.inventory_item_decrease(book_id, quantity)

    try:
        return await orders_repo.save_order(new_order)
    except Exception as err:
        req_url = err.request.url
        req_method = err.request.method
        status_code = err.response.status_code
        msg = f"Failed with {status_code} on {req_method} {req_url}"

        for item in new_order.order_info.items:
            book_id = item.book_id
            quantity = item.quantity

            # try/catch here for retry
            await orders_repo.inventory_item_increase(book_id, quantity)

        raise exceptions.OrderNotSaved(
            detail = "Not sure what happened"
        )

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
