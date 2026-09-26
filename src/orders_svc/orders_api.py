import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from orders_svc.orders_svc import *
from orders_svc.schemas import NewOrder

logger = logging.getLogger(__name__)

app = FastAPI()

# TODO
# filter with query parameters, status, user_id

@app.get("/orders")
async def get_orders(user_id: str = None):
    logger.info("Request received to retrieve orders")

    return await get_all_orders(user_id)

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    logger.info(f"Request received to retrieve order: `{order_id}`")

    res = await get_order_by_order_id(order_id)
    return res

@app.post("/orders")
async def create_order(new_order: NewOrder):
    res = await create_new_order(new_order)
    return res#.json()

@app.post("/orders/{id}/cancel")
def cancel_order():
    pass

@app.patch("/orders/{id}/")
def update_order(): pass

@app.get("/users/{user_id}/orders")
def get_user_orders(): pass