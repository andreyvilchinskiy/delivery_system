import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Customer, Order, OrderItem

def test_customer_creation():
    customer = Customer(1, "Иван", "123456", "Москва")
    assert customer.name == "Иван"
    assert customer.phone == "123456"
    assert customer.address == "Москва"

def test_order_item_total():
    item = OrderItem("Пицца", 2, 500.0)
    assert item.total == 1000.0

def test_order_creation():
    items = [OrderItem("Товар1", 1, 100.0)]
    order = Order(1, 1, "2024-01-01", "новый", 100.0, items)
    assert order.status == "новый"
    assert len(order.items) == 1
    assert order.total == 100.0

def test_customer_to_dict():
    customer = Customer(1, "Иван", "123", "Адрес")
    d = customer.to_dict()
    assert d['id'] == 1
    assert d['name'] == "Иван"

def test_order_to_dict():
    items = [OrderItem("Товар", 2, 50.0)]
    order = Order(1, 1, "2024-01-01", "новый", 100.0, items)
    d = order.to_dict()
    assert d['id'] == 1
    assert d['total'] == 100.0
    assert len(d['items']) == 1
    