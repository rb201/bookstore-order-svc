from fastapi import FastAPI
from fastapi.responses import JSONResponse

class OrderNotFound(Exception):
    def __init__(self, order_id: str,  detail: str | dict, status_code: int = 404):
        self.order_id = order_id
        self.detail = detail
        self.status_code = status_code
        self.msg = f"Order {order_id} not found. {detail}"

        super().__init__(self.msg)

class OrderNotCancelable(Exception):
    def __init__(self, order_id: str, detail: str|dict, status_code: int = 422):
        self.order_id = order_id
        self.detail = detail
        self.status_code = status_code
        self.msg = f"Order {order_id} can not be canceled. {detail}"

        super().__init__(self.msg)

class OrderUnprocessable(Exception):
    def __init__(self, detail: str|dict, status_code: int = 422):
        self.detail = detail
        self.status_code = status_code
        self.msg = f"{self.detail}"

        super().__init__(self.msg)

class OrderNotSaved(Exception):
    def __init__(self, detail: str|dict, status_code: int = 503):
        self.detail = detail
        self.status_code = status_code
        self.msg = f"Order not saved. {self.detail}"

        super().__init__(self.msg)

class InventoryServiceUnavailableError(Exception):
    def __init__(self, detail: str|dict):
        self.status_code = 503
        self.detail = detail
        self.msg = f"Problem! {self.detail}."

        super().__init__(self.msg)


async def order_not_found_handler(request, err):
    return JSONResponse(
        status_code = err.status_code,
        content = {
            "error": "ORDER_NOT_FOUND",
            "detail": err.msg
        }
    )

async def order_not_cancelable_handler(request, err):
    return JSONResponse(
        status_code = err.status_code,
        content = {
            "error": "ORDER_NOT_CANCELABLE",
            "detail": err.detail
        }
    )

async def order_unprocessable_handler(request, err):
    return JSONResponse(
        status_code = err.status_code,
        content = err.detail
    )

async def order_not_saved_handler(request, err):
    return JSONResponse(
        status_code = err.status_code,
        content = {"detail": err.detail}
    )

async def inventory_service_unavailble_error_handler(request, err):
    return JSONResponse(
        status_code = err.status_code,
        content = {"detail": err.detail}
    )

EXCEPTION_HANDLERS = {
    OrderNotFound: order_not_found_handler,
    OrderNotCancelable :order_not_cancelable_handler,
    OrderUnprocessable: order_unprocessable_handler,
    OrderNotSaved: order_not_saved_handler,
    InventoryServiceUnavailableError: inventory_service_unavailble_error_handler
}

def register_exception_handlers(app: FastAPI):
    for exception, handler in EXCEPTION_HANDLERS.items():
        app.add_exception_handler(exception, handler)