import pytest

from fastapi import HTTPException
from fastapi.testclient import TestClient

from orders_svc import exceptions
from orders_svc.orders_api import app

client = TestClient(app)

def test_get_all_orders_success(mocker):
    mocker.patch(
        "orders_svc.orders_api.orders_svc.get_all_orders",
        return_value = [{"order_id": "order01"}]
    )

    res = client.get("/orders")

    assert res.status_code == 200

def test_get_order_by_user_id_success(mocker):
    user_id = "user01"

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_all_orders_by_user_id",
        return_value = [{"order_id": "order01", "user_id": user_id}]
    )

    res = client.get(f"/orders?user_id={user_id}")

    assert res.status_code == 200

def test_get_order_by_id_success(mocker):
    order_id = "order01"

    mocker.patch(
        "orders_svc.orders_api.orders_svc.get_order_by_order_id",
        return_value = [{"order_id": "order01"}]
    )

    res = client.get(f"/orders/{order_id}")

    assert res.status_code == 200

def test_get_order_by_id_does_not_exists(mocker):
    order_id = "order00001"

    mocker.patch(
        "orders_svc.orders_api.orders_svc.get_order_by_order_id",
        side_effect = exceptions.OrderNotFound(order_id = order_id, detail = "")
    )

    client.get(f"/orders/{order_id}")

def test_cancel_order_not_found(mocker):
    order_id = "order01"

    mocker.patch(
        "orders_svc.orders_api.orders_svc.cancel_order",
        side_effect = exceptions.OrderNotFound(order_id = order_id, detail = "")
    )

    res = client.post(f"/orders/{order_id}/cancel")
    assert res.status_code == 404

def test_cancel_order_not_cancelable(mocker):
    order_id = "order01"

    mocker.patch(
        "orders_svc.orders_api.orders_svc.cancel_order",
        side_effect = exceptions.OrderNotCancelable(order_id = order_id, detail = "")
    )

    res = client.post(f"/orders/{order_id}/cancel")
    assert res.status_code == 422

def test_cancel_order_success(mocker):
    order_id = "order01"

    mocker.patch(
        "orders_svc.orders_api.orders_svc.cancel_order",
        return_value = {"status": "cancelled"}
    )

    res = client.post(f"/orders/{order_id}/cancel")
    assert res.status_code == 200

def test_create_order_success(mocker):
    payload = {
        "user_id": "user02",
        "status": "created",
        "created_at": "2026-09-25T10:15:00Z",
        "order_info": {
            "total_items": 1,
            "total_price": 19.95,
            "items": [
                {
                    "book_id": "BK-1001",
                    "title": "Buddhism For Dummies",
                    "isbn": "987654321",
                    "price": 7.97,
                    "quantity": 1,
                    "subtotal": 7.97
                }
            ]
        },
    }

    mocker.patch(
        "orders_svc.orders_api.orders_svc.create_order",
        return_value = {"status": "created"}
    )

    res = client.post(f"/orders", json = payload)
    assert res.status_code == 200

def test_create_order_not_processable(mocker):
    payload = {
        "status": "created",
        "created_at": "2026-09-25T10:15:00Z",
        "order_info": {
            "total_items": 1,
            "total_price": 19.95,
            "items": [
                {
                    "book_id": "BK-1001",
                    "title": "Buddhism For Dummies",
                    "isbn": "987654321",
                    "price": 7.97,
                    "quantity": 1,
                    "subtotal": 7.97
                }
            ]
        },
    }

    mocker.patch(
        "orders_svc.orders_api.orders_svc.create_order",
        side_effect = HTTPException(
            status_code = 422, detail = ''
        )
    )

    res = client.post(f"/orders", json = payload)
    assert res.status_code == 422
