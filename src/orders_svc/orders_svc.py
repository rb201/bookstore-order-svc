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
    res = await fetch_order_by_order_id(order_id)

    return res

async def check_does_item_exist(book_id): pass

async def check_enough_quantity(book_id): pass

async def create_new_order(new_order):
    items = new_order.order_info.items

    # check inv and stock
    item_not_in_inv = []
    item_not_enough_inv = []
    for item in items:
        print(f"{item.book_id}: {item.quantity} wanted")
        res = await fetch_item(item.book_id)

        if res.status_code == 404:
            logger.info(f"Item {item.book_id} not found in inv")
            item_not_in_inv.append(item.book_id)

        item_inv_qty = res.json().get('stock_quantity')
        print(f"item {item.book_id} current stock {item_inv_qty}")

        if item_inv_qty < item.quantity:
            logger.info(f"Item {item.book_id} does not have enough inv")
            item_not_enough_inv.append(item.book_id)

    if item_not_in_inv:
        logger.info(f"Order can not be completed. Items {item_not_in_inv} DNE")

        return {
            "error": "ITEM_NOT_FOUND",
            "msg": "Order can not be completed, items not found in inventory",
            "detail": item_not_in_inv
        }

     # check stock
    return