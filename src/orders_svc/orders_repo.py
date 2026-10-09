import json
import logging
import os
from uuid import uuid4

import asyncio
import httpx2 as httpx
import psycopg
from asgi_correlation_id import correlation_id
from dotenv import load_dotenv
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from orders_svc.helper import add_correlation_id_header
from orders_svc import exceptions
from orders_svc.schemas import NewOrder

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") + "/orders"
INV_URL = os.getenv("INV_URL")

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

async def get_item(item_id):
    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        for attempt in range(3):
            try:
                url = f"{INV_URL}/items/{item_id}"
                res = await client.get(url, timeout = 3)

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
        for attempt in range(3):
            try:
                res = await client.post(
                    url = f"{INV_URL}/items/{book_id}/sell?stock_quantity={quantity}",
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

async def inventory_item_increase(book_id, quantity):
    payload = {"stock_quantity": quantity}

    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        for attempt in range(3):
            try:
                res = await client.post(f"{INV_URL}/items/{book_id}/receive?stock_quantity={quantity}")

                if res.status_code == 200:
                    logger.info(f"Unreserved {quantity} of {book_id}")
                    return

                return {"error": f"seomthing happened {res}"}

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

async def save_order(new_order: NewOrder, reservation_id: str):
    order = new_order.model_dump()
    ordered_items = order["order_info"]["items"]
    order_id = str(uuid4())

    async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row) as conn:
        async with conn.cursor() as cur:
            try:
                await cur.execute(
                    """
                    INSERT INTO orders (order_id, user_id, status, created_at, total_items, total_price, reservation_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING order_id, status
                    """,
                    (order_id, order["user_id"], order["status"], order["created_at"], order["order_info"]["total_items"], order["order_info"]["total_price"], reservation_id)
                )

                # TODO validate insert
                # updated_row = await cur.fetchone()
                # logger.info(updated_row)

                for item in ordered_items:
                    await cur.execute(
                        """
                        INSERT INTO order_items (order_id, book_id, title, isbn, price, quantity, subtotal)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (order_id, item["book_id"], item["title"], item["isbn"], item["price"], item["quantity"], item["subtotal"])
                    )

                await conn.commit()
                logger.info(
                    "Order saved successfull",
                    extra = {
                        "event": "order_saved_successfully",
                        "correlation_id": correlation_id.get(),
                        "order_id": order_id
                    }
                )
            except psycopg.Error as e:
                logger.error(
                    f"Problem saving to database. {e}",
                    extra = {
                        "event": "order_not_saved",
                        "correlation_id": correlation_id.get(),
                        "detail": e
                    }
                )

                await conn.rollback()

                raise exceptions.RepositoryError(detail = e)

            return {"order_id": order_id}

async def cancel_order(order_id: str): 
    async with await AsyncConnection.connect(DATABASE_URL, row_factory = dict_row)  as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                UPDATE orders
                SET status = %s
                WHERE order_id = %s
                RETURNING order_id, status
                """,
                ("cancelled", order_id,)
            )

            await conn.commit()

            updated_row = await cur.fetchone()

            if not updated_row:
                logger.error("Order not found")
                raise exceptions.RepositoryError("Order did not save?")

            logger.info(
                f"Order {order_id} has been cancelled",
                extra = {
                    "event": "cancel_order_successful",
                    "correlation_id": correlation_id.get(),
                    "order_id": order_id,
                    "status": updated_row.get("status")
                }
            )

            return {"order_id": order_id, "status": updated_row.get("status")}

async def request_inventory_check(inventory_reserve_request):
    async with httpx.AsyncClient(event_hooks={"request": [add_correlation_id_header]}) as client:
        for attempt in range(3):
            try:
                res = await client.post(
                    url = f"{INV_URL}/inventory/reserve",
                    timeout = 1,
                    json = inventory_reserve_request
                )

                if res.json().get("error") == "ORDER_UNPROCESSABLE":
                    raise exceptions.OrderUnprocessable(
                        detail = f"{res.json().get("msg")}: {res.json().get("details")}"
                    )

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
