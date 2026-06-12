import pytest
import sys
import os
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from models import Customer, Order, OrderItem

@pytest.fixture
def db():
    """Фикстура с автоматическим закрытием БД"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        _db = Database(db_path)
        yield _db
        _db.close()

def test_create_customer(db):
    customer = Customer(None, "Тест", "123456", "Адрес")
    customer_id = db.create_customer(customer)
    assert customer_id is not None
    
    retrieved = db.get_customer(customer_id)
    assert retrieved.name == "Тест"

def test_delete_customer_with_orders(db):
    customer = Customer(None, "Тест", "123", "Адрес")
    customer_id = db.create_customer(customer)
    
    order = Order(None, customer_id, "2024-01-01", "новый", 100.0, [])
    db.create_order(order)
    
    assert db.delete_customer(customer_id) == False

def test_get_all_customers(db):
    assert len(db.get_all_customers()) == 0
    
    db.create_customer(Customer(None, "Клиент1", "111", "Адрес1"))
    db.create_customer(Customer(None, "Клиент2", "222", "Адрес2"))
    
    assert len(db.get_all_customers()) == 2

def test_create_order(db):
    customer_id = db.create_customer(Customer(None, "Тест", "123", "Адрес"))
    
    items = [OrderItem("Товар1", 2, 100.0)]
    order = Order(None, customer_id, "2024-01-01", "новый", 200.0, items)
    
    order_id = db.create_order(order)
    assert order_id is not None
    
    retrieved = db.get_order(order_id)
    assert retrieved.status == "новый"
    assert len(retrieved.items) == 1

def test_get_orders_by_status_count(db):
    customer_id = db.create_customer(Customer(None, "Тест", "123", "Адрес"))
    
    db.create_order(Order(None, customer_id, "2024-01-01", "новый", 100.0, []))
    db.create_order(Order(None, customer_id, "2024-01-02", "выполнен", 200.0, []))
    
    counts = db.get_orders_by_status_count()
    assert counts["новый"] == 1
    assert counts["выполнен"] == 1

def test_get_top_customers(db):
    cust1 = db.create_customer(Customer(None, "Клиент1", "111", "Адрес1"))
    cust2 = db.create_customer(Customer(None, "Клиент2", "222", "Адрес2"))
    
    db.create_order(Order(None, cust1, "2024-01-01", "новый", 1000.0, []))
    db.create_order(Order(None, cust2, "2024-01-02", "новый", 500.0, []))
    
    top = db.get_top_customers(2)
    assert top[0][1] == "Клиент1"
    assert top[0][2] == 1000.0