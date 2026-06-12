import sqlite3
from typing import List, Optional, Dict
from datetime import datetime
import logging
import os
from models import Customer, Order, OrderItem, ORDER_STATUSES

logger = logging.getLogger(__name__)

class Database:
    """Работа с SQLite базой данных"""
    
    def __init__(self, db_path='data/delivery.db'):
        if not os.path.exists('data'):
            os.makedirs('data')
        self.db_path = db_path
        self._connection = None 
        self.init_database()
    
    def get_connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
        return self._connection
    
    def close(self):
        """Закрыть соединение с БД"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def init_database(self):
        """Инициализация таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT,
                    address TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER REFERENCES customers(id) ON DELETE RESTRICT,
                    order_date TEXT NOT NULL,
                    status TEXT CHECK(status IN ('новый', 'в доставке', 'выполнен', 'отменён')),
                    total REAL NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS order_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER REFERENCES orders(id),
                    product_name TEXT,
                    quantity INTEGER,
                    price REAL
                )
            ''')
            
            conn.commit()
            logger.info("База данных инициализирована")
    
    def create_customer(self, customer: Customer) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)',
                (customer.name, customer.phone, customer.address)
            )
            conn.commit()
            logger.info(f"Создан клиент: {customer.name}")
            return cursor.lastrowid
    
    def get_customer(self, customer_id: int) -> Optional[Customer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone, address FROM customers WHERE id = ?', (customer_id,))
            row = cursor.fetchone()
            if row:
                return Customer(id=row[0], name=row[1], phone=row[2], address=row[3])
            return None
    
    def get_all_customers(self) -> List[Customer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone, address FROM customers')
            return [Customer(id=row[0], name=row[1], phone=row[2], address=row[3]) 
                    for row in cursor.fetchall()]
    
    def update_customer(self, customer: Customer):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE customers SET name=?, phone=?, address=? WHERE id=?',
                (customer.name, customer.phone, customer.address, customer.id)
            )
            conn.commit()
            logger.info(f"Обновлён клиент ID: {customer.id}")
    
    def delete_customer(self, customer_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM orders WHERE customer_id = ?', (customer_id,))
            if cursor.fetchone()[0] > 0:
                logger.warning(f"Нельзя удалить клиента {customer_id} - есть заказы")
                return False
            cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
            conn.commit()
            logger.info(f"Удалён клиент ID: {customer_id}")
            return True
    
    def create_order(self, order: Order) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO orders (customer_id, order_date, status, total) VALUES (?, ?, ?, ?)',
                (order.customer_id, order.order_date, order.status, order.total)
            )
            order_id = cursor.lastrowid
            
            for item in order.items:
                cursor.execute(
                    'INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)',
                    (order_id, item.product_name, item.quantity, item.price)
                )
            
            conn.commit()
            logger.info(f"Создан заказ ID: {order_id}")
            return order_id
    
    def get_order(self, order_id: int) -> Optional[Order]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, customer_id, order_date, status, total FROM orders WHERE id = ?', (order_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            cursor.execute('SELECT product_name, quantity, price FROM order_items WHERE order_id = ?', (order_id,))
            items = [OrderItem(product_name=r[0], quantity=r[1], price=r[2]) for r in cursor.fetchall()]
            
            return Order(id=row[0], customer_id=row[1], order_date=row[2], status=row[3], total=row[4], items=items)
    
    def get_all_orders(self, status_filter: str = None, date_filter: str = None) -> List[Order]:
        query = 'SELECT id, customer_id, order_date, status, total FROM orders'
        params = []
        
        conditions = []
        if status_filter:
            conditions.append('status = ?')
            params.append(status_filter)
        if date_filter:
            conditions.append('order_date = ?')
            params.append(date_filter)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            orders = []
            for row in cursor.fetchall():
                cursor.execute('SELECT product_name, quantity, price FROM order_items WHERE order_id = ?', (row[0],))
                items = [OrderItem(product_name=r[0], quantity=r[1], price=r[2]) for r in cursor.fetchall()]
                orders.append(Order(id=row[0], customer_id=row[1], order_date=row[2], status=row[3], total=row[4], items=items))
            return orders
    
    def update_order(self, order: Order):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE orders SET customer_id=?, order_date=?, status=?, total=? WHERE id=?',
                (order.customer_id, order.order_date, order.status, order.total, order.id)
            )
            cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order.id,))
            
            for item in order.items:
                cursor.execute(
                    'INSERT INTO order_items (order_id, product_name, quantity, price) VALUES (?, ?, ?, ?)',
                    (order.id, item.product_name, item.quantity, item.price)
                )
            
            conn.commit()
            logger.info(f"Обновлён заказ ID: {order.id}")
    
    def delete_order(self, order_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM order_items WHERE order_id = ?', (order_id,))
            cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
            conn.commit()
            logger.info(f"Удалён заказ ID: {order_id}")
    
    def get_orders_by_status_count(self) -> Dict[str, int]:
        result = {status: 0 for status in ORDER_STATUSES}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT status, COUNT(*) FROM orders GROUP BY status')
            for row in cursor.fetchall():
                result[row[0]] = row[1]
        return result
    
    def get_top_customers(self, limit: int = 3) -> List[tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.id, c.name, SUM(o.total) as total_spent
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                GROUP BY c.id, c.name
                ORDER BY total_spent DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
    
    def get_total_revenue(self, period: str = 'day') -> float:
        today = datetime.now().date()
        
        if period == 'day':
            start_date = today.strftime('%Y-%m-%d')
        elif period == 'week':
            from datetime import timedelta
            start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        elif period == 'month':
            from datetime import timedelta
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        else:
            start_date = '1970-01-01'
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(total) FROM orders WHERE order_date >= ?', (start_date,))
            result = cursor.fetchone()[0]
            return result if result else 0.0