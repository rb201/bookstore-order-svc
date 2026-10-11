import pytest
import pytest_asyncio
from httpx2 import AsyncClient, ASGITransport

from orders_svc import exceptions, schemas
from orders_svc.orders_api import app

@pytest_asyncio.fixture(scope="module")
async def client():
    """A single, shared async client for all tests within the same module."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

@pytest_asyncio.fixture
async def test_create_order_success_fix(mocker, client):
    order_id_container
 
    yield order_id_container
    
    # remove orders, doesnt exist
    # client.delete("/orders/delete/{order_id_container}")

@pytest.mark.asyncio
# async def test_create_order_success(client, test_create_order_success_fix):
async def test_create_order_success(client):
       new_order = {
        "user_id": "user0012",
        "status": "created",
        "created_at": "2026-09-25T10:15:00Z",
        "order_info": {
            "total_items": 3,
            "total_price": 19.95,

            "items": [
                {
                "book_id": "1",
                "title": "Buddhism For You",
                "isbn": "987654321",
                "price": 7.97,
                "quantity": 2,
                "subtotal": 7.97
                },
                {
                "book_id": "2",
                "title": "Buddhism 4 u",
                "isbn": "987654321",
                "price": 7.97,
                "quantity": 1,
                "subtotal": 7.97
                }
            ]
        }
    }
    res = await client.post("/orders", json = test_create_order_success_fix)

    assert res.status_code == 200
    assert "order_id" in res.json()

@pytest.mark.asyncio
async def test_create_order_item_not_found(client):
    new_order = {
        "user_id": "user0012",
        "status": "created",
        "created_at": "2026-09-25T10:15:00Z",
        "order_info": {
            "total_items": 1,
            "total_price": 7.97,

            "items": [
                {
                "book_id": "666",
                "title": "Book A",
                "isbn": "987654321",
                "price": 7.97,
                "quantity": 2,
                "subtotal": 7.97
                }
            ]
        }
    }

    res = await client.post("/orders", json = new_order)

    assert res.status_code == 422

@pytest.mark.asyncio
async def test_create_order_insufficient_inventory(client):
    new_order = {
        "user_id": "user0012",
        "status": "created",
        "created_at": "2026-09-25T10:15:00Z",
        "order_info": {
            "total_items": 666,
            "total_price": 7.97,

            "items": [
                {
                "book_id": "666",
                "title": "Book A",
                "isbn": "987654321",
                "price": 7.97,
                "quantity": 666,
                "subtotal": 7.97
                }
            ]
        }
    }

    res = await client.post("/orders", json = new_order)

    assert res.status_code == 422

@pytest.mark.asyncio
async def test_cancel_order_success(client):
    # TODO Will add fixture to setup and clean 
    order_id = "2e54cc74-69b2-4f03-ab1e-ae7aadd05606"

    res = await client.post(f"/orders/{order_id}/cancel")

    assert res.status_code == 200

@pytest.mark.asyncio
async def test_cancel_order_not_found(client):
    order_id = "aaaaaaa-bbbb-cccc-dddd-eeeeeeeeeee"

    res = await client.post(f"/orders/{order_id}/cancel")
    assert res.status_code == 404
    assert res.json()["error"] == "ORDER_NOT_FOUND"
