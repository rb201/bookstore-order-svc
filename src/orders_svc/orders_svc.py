import logging

from orders_svc.orders_json_srv_repo import *

async def get_all_orders(user_id):
    # if user_id is None:
    res = await fetch_all_orders()
    # else:
        # res = await fetch_user_orders(user_id)
    
    return
    # pass