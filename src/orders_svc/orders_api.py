import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from orders_svc.orders_svc import *

logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/orders")
async def get_orders(user_id: str = None):
    # if user_id is None:
    res = await get_all_orders(user_id)
    # else:
        # res = await get_orders(user_id)
    return {'ere': res}

@app.get("/orders/{id}")
def get_order_by_id(id: str):
    pass

@app.post("/orders")
def create_order():
    pass

@app.post("/orders/{id}/cancel")
def cancel_order():
    pass

@app.patch("/orders/{id}/")
def update_order(): pass

@app.get("/users/{user_id}/orders")
def get_user_orders(): pass