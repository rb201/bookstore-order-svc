import logging

import httpx
from fastapi import HTTPException

url =  "http://localhost:3000"

async def fetch_all_orders():
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{url}/orders")

        print(res.json())