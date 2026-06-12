import pytest
import os
import sys
import tempfile
import json
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Database
from data_export import DataExport
from models import Customer, Order, OrderItem

@pytest.fixture
def db_and_exporter():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, 'test.db')
        db = Database(db_path)
        exporter = DataExport(db)
        
        customer_id = db.create_customer(Customer(None, "Тест", "123", "Адрес"))
        items = [OrderItem("Пицца", 2, 500.0)]
        db.create_order(Order(None, customer_id, "2024-01-01", "новый", 1000.0, items))
        
        yield db, exporter
        db.close()  # ← ДОБАВИТЬ ЗАКРЫТИЕ

def test_export_to_json(db_and_exporter):
    db, exporter = db_and_exporter
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        filename = f.name
    
    exporter.export_orders_to_json(filename)
    assert os.path.exists(filename)
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert len(data) == 1
    assert data[0]['status'] == 'новый'
    
    os.unlink(filename)

def test_export_to_xml(db_and_exporter):
    db, exporter = db_and_exporter
    with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
        filename = f.name
    
    exporter.export_orders_to_xml(filename)
    assert os.path.exists(filename)
    
    tree = ET.parse(filename)
    root = tree.getroot()
    orders = root.findall('order')
    assert len(orders) == 1
    
    os.unlink(filename)

def test_import_from_json(db_and_exporter):
    db, exporter = db_and_exporter
    
    test_data = [{
        'customer_id': 1,
        'order_date': '2024-01-01',
        'status': 'выполнен',
        'total': 500.0,
        'items': [{'product_name': 'Тест', 'quantity': 1, 'price': 500.0}]
    }]
    
    with tempfile.NamedTemporaryFile(suffix='.json', mode='w', encoding='utf-8', delete=False) as f:
        json.dump(test_data, f)
        filename = f.name
    
    exporter.import_orders_from_json(filename)
    orders = db.get_all_orders()
    assert len(orders) == 2
    
    os.unlink(filename)