import logging

from orders_svc.orders_json_srv_repo import *

logger = logging.getLogger(__name__)

async def get_all_orders(user_id):
    if user_id is not None:
        logger.info(f"Fetching orders for {user_id}")

        res = await fetch_all_orders_by_user_id(user_id)
    else:
        logger.info(f"Fetching all orders")

        res = await fetch_all_orders()

    return res

async def get_order_by_order_id(order_id: str):
    return await fetch_order_by_order_id(order_id)

async def check_inv_and_stock(new_order):
    order_errors = []
    item_not_in_inv = []
    item_not_enough_inv = []

    for item in new_order.order_info.items:
        print(f"{item.book_id}: {item.quantity} wanted")
        res = await fetch_item(item.book_id)

        if res is None:
            logger.info(f"Item {item.book_id} not found in inv")
            item_not_in_inv.append(item.book_id)
            continue

        item_inv_qty = res.json().get('stock_quantity')
        print(f"item {item.book_id} current stock {item_inv_qty}")

        if item_inv_qty < item.quantity:
            logger.info(f"Item {item.book_id} does not have enough inv")
            item_not_enough_inv.append(item.book_id)

    return order_errors, item_not_in_inv, item_not_enough_inv

async def create_new_order(new_order):
    order_errors, item_not_in_inv, item_not_enough_inv = await check_inv_and_stock(new_order)

    if item_not_in_inv:
        logger.info(f"Order can not be completed. These items do not exist {item_not_in_inv}")

        items_not_found_error_msg = {
            "error": "ITEMS_NOT_FOUND",
            "msg": f"These items were not found {item_not_in_inv}"
        }

        order_errors.append(items_not_found_error_msg)

    if item_not_enough_inv:
        logger.info(f"Order can not be completed. Insufficient inv for items {item_not_enough_inv}")

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

        return order_error_msg

    return await save_order(new_order)

async def cancel_order(order_id):
    cancelable_orders = [
        "created",
        "pending"
    ]

    res = await get_order_by_order_id(order_id)

    order_status = res.get("status")

    if order_status in cancelable_orders:
        return {}
    
    return {
        "error": "ORDER_NOT_CANCELABLE",
        "msg": f"Can not cancel order, its current status is {order_status}"
    }

