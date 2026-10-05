import logging

import asyncio
import httpx2 as httpx
from asgi_correlation_id import correlation_id
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from orders_svc.helper import add_correlation_id_header
from orders_svc import exceptions
from orders_svc.schemas import NewOrder

logger = logging.getLogger(__name__)

inv_url = "http://localhost:8000"

async def get_all_orders():
    async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT * FROM orders
                """
            )

            return await cur.fetchall()

async def get_all_orders_by_user_id(user_id: str):
    async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row)  as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT * FROM orders
                WHERE user_id = %s
                """,
                (user_id,)
            )

            return await cur.fetchall()

async def get_order_by_order_id(order_id: str):
    async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row)  as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                SELECT * FROM orders
                WHERE order_id = %s
                """,
                (order_id,)
            )

            return await cur.fetchall()


# async def save_order(new_order: NewOrder):
#     async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row)  as conn:
#         async with conn.cursor() as cur:
#             await cur.execute(
#                 """
#                 SELECT * FROM orders
#                 WHERE order_id = %s
#                 """,
#                 (order_id,)
#             )

#             return cur.fetchall()

async def get_item(item_id):
    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        for attempt in range(3):
            try:
                url = f"{inv_url}/items/{item_id}"
                res = await client.get(url, timeout = 5)

                # TODO
                # maybe return [] from api svc
                if res is None or res.json().get("error") :
                    return None

                return res.json()
            except httpx.TimeoutException:
                logger.warning(f"inventory timeout attempt: {attempt + 1}/3")
                
                if attempt == 2:
                    logger.critical(f"Connection timed-out")
                    raise exceptions.InventoryServiceUnavailableError(
                        detail = "Connection timed-out. Order not proccessed"
                    )
            except httpx.TransportError:
                logger.warning(f"inventory transport failure: {attempt + 1}/3")
                
                if attempt == 2:
                    logger.critical(f"Can not connect to server")
                    raise exceptions.InventoryServiceUnavailableError(
                        detail = "Server unavailable. Order not proccessed"
                    )

            await asyncio.sleep(1)

async def inventory_item_decrease(book_id, quantity):
    payload = {"stock_quantity": quantity}

    logger.info(
        f"Requesting reserve of {quantity} {book_id}",
        extra = {
            "event": "inventory_reserve_request",
            "correlation_id": correlation_id.get(),
            "book_id": book_id,
            "quantity": quantity
        }
    )
    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        res = await client.post(
            url = f"{inv_url}/items/{book_id}/sell?stock_quantity={quantity}",
        )

        if res.status_code == 200:
            logger.info(
                f"Reserved {quantity} of {book_id}",
                extra = {
                    "event": "inventory_reserved",
                    "correlation_id": correlation_id.get(),
                    "book_id": book_id,
                    "quantity": quantity
                }
            )
            return res.json()

        res.raise_for_status()

async def inventory_item_increase(book_id, quantity):
    payload = {"stock_quantity": quantity}

    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        res = await client.post(f"{inv_url}/items/{book_id}/receive?stock_quantity={quantity}")

        if res.status_code == 200:
            logger.info(f"Unreserved {quantity} of {book_id}")
            return

        return {"error": f"seomthing happened {res}"}

# async def save_order(new_order: NewOrder):
#     order = new_order.model_dump_json()
#     print(order)
#     async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row) as conn:
#         with await conn.cursor() as cur:
#             await cur.execute(
#                 """
#                 INSERT INTO orders (user_id, status, created_at, total_items, total_price)
#                 VALUES (%s, %s, %s, %s, %s)
#                 """,
#                 (order["user_id"], order["status"], order["created_at"], order["total_items"], order["total_price"])               
#             )

#             for item in order["items"]:
#                 await cur.execute(
#                 """
#                 INSERT INTO order_items (order_id, book_id, title, isbn, price, quantity, subtotal)
#                 VALUES (%s, %s, %s, %s, %s, %s, %s, )
#                 """,
#                 (item["order_id"], item["book_id"], item["title"], item["isbn"], item["price"], item["quantity"], item["subtotal"])
#                 )

#             await conn.commit()

async def cancel_order(order_id: str): 
    async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row)  as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE orders
                SET status = %s
                WHERE order_id = %s
                """,
                ("cancelled", order_id,)
            )

            return await conn.commit()

