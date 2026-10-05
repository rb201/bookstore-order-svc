import logging

from asgi_correlation_id import correlation_id, CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException

from . import orders_svc, exceptions
from orders_svc.schemas import NewOrder

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CorrelationIdMiddleware,
    header_name='X-Correlation-ID',
)

exceptions.register_exception_handlers(app)

# TODO
# filter with query parameters, status, user_id

@app.get("/orders")
async def get_all_orders(user_id: str = None):
    logger.info("Request received to retrieve orders")

    return await orders_svc.get_all_orders(user_id)

@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    logger.info(
        f"Request received to retrieve order no: `{order_id}`",
        extra = {
            "event": "get_order_requested",
            "correlation_id": correlation_id.get(),
            "order_id": order_id
        })

    res = await orders_svc.get_order_by_order_id(order_id)

    if res is None:
        raise exceptions.OrderNotFound(
            order_id = order_id,
            detail = "Order ID does not exist"
        )
    return res

@app.post("/orders")
async def create_order(new_order: NewOrder):
    logger.info(
        "Request for new order received",
        extra = {
            "event": "create_order_request",
            "correlation_id": correlation_id.get()
        }
    )

    return await orders_svc.create_order(new_order)

@app.post("/orders/{order_id}/cancel")
async def cancel_order(order_id):
    logger.info(
        f"Request received to cancel order no: {order_id}",
        extra = {
            "event": "cancel_order_requested",
            "correlation_id": correlation_id.get(),
            "order_id": order_id
        }
    )
    return await orders_svc.cancel_order(order_id)

@app.patch("/orders/{id}/")
def update_order(): pass

@app.get("/users/{user_id}/orders")
def get_user_orders(): pass