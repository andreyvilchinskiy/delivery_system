import json
import xml.etree.ElementTree as ET
from typing import List
import logging
from models import Order, OrderItem, Customer

logger = logging.getLogger(__name__)

class DataExport:
    """Экспорт и импорт данных"""
    
    def __init__(self, database):
        self.db = database
    
    def export_orders_to_json(self, filename: str):
        """Экспорт заказов в JSON"""
        orders = self.db.get_all_orders()
        data = [order.to_dict() for order in orders]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Экспортировано {len(orders)} заказов в {filename}")
    
    def export_orders_to_xml(self, filename: str):
        """Экспорт заказов в XML"""
        root = ET.Element('orders')
        orders = self.db.get_all_orders()
        
        for order in orders:
            order_elem = ET.SubElement(root, 'order')
            ET.SubElement(order_elem, 'id').text = str(order.id)
            ET.SubElement(order_elem, 'customer_id').text = str(order.customer_id)
            ET.SubElement(order_elem, 'order_date').text = order.order_date
            ET.SubElement(order_elem, 'status').text = order.status
            ET.SubElement(order_elem, 'total').text = str(order.total)
            
            items_elem = ET.SubElement(order_elem, 'items')
            for item in order.items:
                item_elem = ET.SubElement(items_elem, 'item')
                ET.SubElement(item_elem, 'product_name').text = item.product_name
                ET.SubElement(item_elem, 'quantity').text = str(item.quantity)
                ET.SubElement(item_elem, 'price').text = str(item.price)
        
        tree = ET.ElementTree(root)
        tree.write(filename, encoding='utf-8', xml_declaration=True)
        logger.info(f"Экспортировано {len(orders)} заказов в {filename}")
    
    def import_orders_from_json(self, filename: str):
        """Импорт заказов из JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            count = 0
            for order_data in data:
                # Проверка корректности данных
                if not all(k in order_data for k in ['customer_id', 'order_date', 'status', 'total', 'items']):
                    logger.warning(f"Пропущен некорректный заказ: {order_data}")
                    continue
                
                items = [OrderItem(**item) for item in order_data['items']]
                order = Order(
                    id=None,
                    customer_id=order_data['customer_id'],
                    order_date=order_data['order_date'],
                    status=order_data['status'],
                    total=order_data['total'],
                    items=items
                )
                self.db.create_order(order)
                count += 1
            
            logger.info(f"Импортировано {count} заказов из {filename}")
        except Exception as e:
            logger.error(f"Ошибка импорта из {filename}: {e}")
            raise
    
    def import_orders_from_xml(self, filename: str):
        """Импорт заказов из XML"""
        try:
            tree = ET.parse(filename)
            root = tree.getroot()
            
            count = 0
            for order_elem in root.findall('order'):
                try:
                    customer_id = int(order_elem.find('customer_id').text)
                    order_date = order_elem.find('order_date').text
                    status = order_elem.find('status').text
                    total = float(order_elem.find('total').text)
                    
                    items = []
                    items_elem = order_elem.find('items')
                    if items_elem:
                        for item_elem in items_elem.findall('item'):
                            product_name = item_elem.find('product_name').text
                            quantity = int(item_elem.find('quantity').text)
                            price = float(item_elem.find('price').text)
                            items.append(OrderItem(product_name, quantity, price))
                    
                    order = Order(None, customer_id, order_date, status, total, items)
                    self.db.create_order(order)
                    count += 1
                except Exception as e:
                    logger.warning(f"Пропущен некорректный заказ: {e}")
            
            logger.info(f"Импортировано {count} заказов из {filename}")
        except Exception as e:
            logger.error(f"Ошибка импорта из {filename}: {e}")
            raise
    
    def export_orders(self, filename: str, format: str = 'json'):
        """Экспорт в указанном формате"""
        if format.lower() == 'json':
            self.export_orders_to_json(filename)
        elif format.lower() == 'xml':
            self.export_orders_to_xml(filename)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")
    
    def import_orders(self, filename: str):
        """Импорт из файла (автоопределение формата)"""
        if filename.endswith('.json'):
            self.import_orders_from_json(filename)
        elif filename.endswith('.xml'):
            self.import_orders_from_xml(filename)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {filename}")