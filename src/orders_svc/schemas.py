from pydantic import BaseModel
from typing import List

class OrderItem(BaseModel):
    book_id: str
    title: str
    isbn: str
    price: float
    quantity: int
    subtotal: float

class OrderInfo(BaseModel):
    total_items: int
    total_price: float
    items: list[OrderItem]

class NewOrder(BaseModel):
    user_id: str
    status: str
    created_at: str
    order_info: OrderInfo