from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class Customer:
    """Модель клиента"""
    id: Optional[int]
    name: str
    phone: str
    address: str
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'address': self.address
        }

@dataclass
class OrderItem:
    """Модель товара в заказе"""
    product_name: str
    quantity: int
    price: float
    
    @property
    def total(self):
        return self.quantity * self.price
    
    def to_dict(self):
        return {
            'product_name': self.product_name,
            'quantity': self.quantity,
            'price': self.price
        }

@dataclass
class Order:
    """Модель заказа"""
    id: Optional[int]
    customer_id: int
    order_date: str
    status: str
    total: float
    items: List[OrderItem]
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'order_date': self.order_date,
            'status': self.status,
            'total': self.total,
            'items': [item.to_dict() for item in self.items]
        }

# Статусы заказов
ORDER_STATUSES = ['новый', 'в доставке', 'выполнен', 'отменён']