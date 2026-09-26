import logging

import httpx
from fastapi import HTTPException

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
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{inv_url}/items/{item_id}")

        return res