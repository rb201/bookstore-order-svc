import pytest

from orders_svc import orders_svc, exceptions

@pytest.mark.asyncio
async def test_get_all_orders_for_user_doesnt_exists(mocker):
    user = "user0001"

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_all_orders_by_user_id",
        return_value = []
    )

    res = await orders_svc.get_all_orders(user)

    assert res == []

@pytest.mark.asyncio
async def test_get_all_orders_for_user_exists(mocker):
    user = "user01"

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_all_orders_by_user_id",
        return_value = [
            {
                "id": "orders01",
                "user_id": "user01",
                "order_info": {
                    "items": [
                        {},
                        {},
                        {}
                    ]
                }
            },
            {
                "id": "orders01",
                "user_id": "user01",
            }
        ]
    )

    res = await orders_svc.get_all_orders(user)

    assert res[1]["user_id"] == user
    assert len(res) == 2
    assert len(res[0]["order_info"]["items"]) == 3

@pytest.mark.asyncio
async def test_get_all_orders_success(mocker):
    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_all_orders",
        return_value = [
            {
                "id": "order01"
            },
            {
                "id": "order02"
            }
        ]
    )

    res = await orders_svc.get_all_orders()

    assert len(res) == 2

@pytest.mark.asyncio
async def test_get_order_by_id_failure(mocker):
    order_id = "order00000"

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_order_by_order_id",
        return_value = {
            "error": "ORDER_NOT_FOUND"
        }
    )

    res = await orders_svc.get_order_by_order_id(order_id)

    assert res["error"] == "ORDER_NOT_FOUND"

@pytest.mark.asyncio
async def test_get_order_by_id_success(mocker):
    order_id = "order01"

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_order_by_order_id",
        return_value = {
            "id": order_id,
            "order_info": {
                "items": [
                    {},{}
                ]
            }
        }
    )

    res = await orders_svc.get_order_by_order_id(order_id)

    assert res["id"] == order_id
    assert len(res["order_info"]["items"]) == 2

@pytest.mark.asyncio
async def test_cancel_order_orderid_doesnt_exist(mocker):
    mocker.patch(
        "orders_svc.orders_svc.get_order_by_order_id",
        return_value = None
    )

    with pytest.raises(exceptions.OrderNotFound):
        await orders_svc.cancel_order("order000")

@pytest.mark.asyncio
async def test_cancel_order_fail_uncancelable_state(mocker):
    mocker.patch(
        "orders_svc.orders_svc.get_order_by_order_id",
        return_value = { "status": "shipped"}
    )

    with pytest.raises(exceptions.OrderNotCancelable):
        await orders_svc.cancel_order("order01")

@pytest.mark.asyncio
async def test_cancel_order_success(mocker):
    order_id = "order01"

    mocker.patch(
        "orders_svc.orders_svc.get_order_by_order_id",
        return_value = { "status": "created"}
    )

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.cancel_order",
        return_value = { "status": "cancelled"}
    )

    res = await orders_svc.cancel_order(order_id)

    assert res["status"] == "cancelled"

@pytest.mark.asyncio
async def test_check_inv_and_stock_success(mocker):
    new_order_obj = mocker.Mock()

    item_01 = mocker.Mock()
    item_01.book_id = "BK-1002"
    item_01.quantity = 1

    item_02 = mocker.Mock()
    item_02.book_id = "BK-1003"
    item_02.quantity = 1

    new_order_obj.order_info.items = [item_01, item_02]

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_item",
        side_effect = [
            {
                "book_id": "BK-1002",
                "stock_quantity": 10
            },
            {
                "book_id": "BK-1003",
                "stock_quantity": 10
            }
        ]
    )

    res1, res2 = await orders_svc.check_inv_and_stock(new_order_obj)

    assert res1 == [] and res2 == []

@pytest.mark.asyncio
async def test_check_inv_and_stock_item_doesnt_exists(mocker):
    book_id = "BK-0000000"
    new_order_obj = mocker.Mock()

    item_01 = mocker.Mock()
    item_01.book_id = book_id
    item_01.quantity = 1

    item_02 = mocker.Mock()
    item_02.book_id = "BK-1003"
    item_02.quantity = 1

    new_order_obj.order_info.items = [item_01, item_02]

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_item",
        side_effect = [
            None,
            {
                "book_id": "BK-1003",
                "stock_quantity": 10
            }
        ]
    )

    res1, res2 = await orders_svc.check_inv_and_stock(new_order_obj)

    assert res1 == [book_id] and res2 == []

@pytest.mark.asyncio
async def test_check_inv_and_stock_item_low_quantity(mocker):
    new_order_obj = mocker.Mock()

    item_01 = mocker.Mock()
    item_01.book_id = "BK-1002"
    item_01.quantity = 1

    item_02 = mocker.Mock()
    item_02.book_id = "BK-1003"
    item_02.quantity = 100

    new_order_obj.order_info.items = [item_01, item_02]

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.get_item",
        side_effect = [
            {
                "book_id": "BK-1002",
                "stock_quantity": 10
            },
            {
                "book_id": "BK-1003",
                "stock_quantity": 10
            }
        ]
    )

    res1, res2 = await orders_svc.check_inv_and_stock(new_order_obj)

    assert res1 == [] and res2 == ["BK-1003"]

@pytest.mark.asyncio
async def test_validate_order_item_not_inv(mocker):
    item_not_in_inv = ["BK-00000"]
    item_not_enough_inv = []

    with pytest.raises(exceptions.OrderUnprocessable):
        res = await orders_svc.validate_order(item_not_in_inv, item_not_enough_inv)

@pytest.mark.asyncio
async def test_validate_order_item_low_qty(mocker):
    item_not_in_inv = []
    item_not_enough_qty = ["BK-1001"]

    with pytest.raises(exceptions.OrderUnprocessable):
        res = await orders_svc.validate_order(item_not_in_inv, item_not_enough_qty)

@pytest.mark.asyncio
async def test_validate_order_success(mocker):
    item_not_in_inv = []
    item_not_enough_qty = []

    res = await orders_svc.validate_order(item_not_in_inv, item_not_enough_qty)

    assert res == True

@pytest.mark.syncio
async def test_create_order_success(mocker):
    mocker.patch(
        "orders_svc.orders_svc.check_inv_and_stock",
        return_value = [], []
    )

    mocker.patch(
        "orders_svc.orders_svc.validate_order",
        return_value = True
    )

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.inventory_item_decrease",
        return_value = None
    )

    mocker.patch(
        "orders_svc.orders_svc.orders_repo.save_order",
        return_value = {"status": "created"}
    )

    res = await orders_svc.