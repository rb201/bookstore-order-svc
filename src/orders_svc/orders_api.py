import logging

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI

from orders_svc.orders_svc import *
from orders_svc.schemas import NewOrder

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CorrelationIdMiddleware,
    header_name='X-Correlation-ID',
)

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
    logger.info("Request for new order received")
    res = await create_new_order(new_order)

    if res.get("status_code") == 404:
        logger.critical(f"Order not saved: {res.get("detail")}")

    if res.get("error") == "ORDER_UNPROCESSABLE":
        logger.error("Order not processed")
        raise HTTPException(
            status_code = 422,
            detail = res
        )

    if res.get("error") == "ORDER_NOT_SAVED":
        raise HTTPException(
            status_code = res.get("status_code"),
            detail = res.get("detail")
        )

    return res

@app.post("/orders/{order_id}/cancel")
async def cancel_order_req(order_id):
    logger.info(f"Request received to cancel order for order no: {order_id}")
    res = await cancel_order(order_id)

    if res.get("error") == "ORDER_NOT_CANCELABLE":
        raise HTTPException(
            status_code = 422,
            detail = res
        )

    return res

@app.patch("/orders/{id}/")
def update_order(): pass

@app.get("/users/{user_id}/orders")
def get_user_orders(): pass