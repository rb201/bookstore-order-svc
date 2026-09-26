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

async def create_new_order(new_order):
    items = new_order.order_info.items

    # check inv
    for item in items:
        print(item.book_id)
        res = await fetch_item(item.book_id)
        print(res)
        print(res.status_code)

    return