import logging

import httpx
from fastapi import HTTPException

from orders_svc.helper import add_correlation_id_header

logger = logging.getLogger(__name__)

url =  "http://localhost:3000"
inv_url = "http://localhost:8000"

async def fetch_all_orders():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{url}/orders")

        return res.json()

async def fetch_all_orders_by_user_id(user_id: str):
    logger.info("Fetching now")

    async with httpx.AsyncClient() as client:
        res = await client.get(f"{url}/orders?user_id={user_id}")

        return res.json()

async def fetch_order_by_order_id(order_id: str):
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{url}/orders/{order_id}")

        if res.status_code == 404:
            raise HTTPException(
                status_code = 404,
                detail = {
                    'error': "ORDER_NOT_FOUND",
                    'msg': f"The order `{order_id}` was not found"
                }
            )

        logger.info(f"Order `{order_id}` found")
        return res.json()

async def fetch_item(item_id):
    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        res = await client.get(f"{inv_url}/items/{item_id}")

        if res.status_code == 404:
            return None

        return res

async def save_order(order):
    payload = order.model_dump()

    async with httpx.AsyncClient() as client:
        res = await client.post(
            url = f"{url}/orders",
            json = payload
        )

        if res.status_code not in [200, 201]:
            logger.info(f"Order not saved: {res.status_code}")
            return res.raise_for_status().json()

        return res.json()

async def cancel_order(order_id):
    async with httpx.AsyncClient() as client:
        res = await client.post

async def inventory_item_decrease(book_id, quantity):
    payload = {"stock_quantity": quantity}

    logger.info(f"Requesting reserve of {quantity} {book_id}")
    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        res = await client.post(
            url = f"{inv_url}/items/{book_id}/sell?stock_quantity={quantity}",
        )

        if res.status_code == 200:
            logger.info(f"Reserved {quantity} of {book_id}")
            return

        res.raise_for_status()

async def inventory_item_increase(book_id, quantity):
    payload = {"stock_quantity": quantity}

    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        res = await client.post(f"{inv_url}/items/{book_id}/receive?stock_quantity={quantity}")

        if res.status_code == 200:
            logger.info(f"Unreserved {quantity} of {book_id}")
            return

        return {"error": f"seomthing happened {res}"}

