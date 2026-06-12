#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from datetime import date
import re
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from models import Customer, Order, OrderItem, ORDER_STATUSES
from data_export import DataExport
from logger_config import setup_logger

logger = setup_logger()


class DeliveryApp:
    """GUI приложение для учёта заказов"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Быстрая доставка - Учёт заказов")
        self.root.geometry("1200x700")
        
        self.db = Database()
        self.exporter = DataExport(self.db)
        
        self.setup_ui()
        self.load_orders()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # Держим главное окно сверху
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
    
    def on_closing(self):
        """Обработка закрытия окна"""
        try:
            self.db.close()
        except:
            pass
        self.root.destroy()
    
    def show_error(self, parent, message):
        """Показать ошибку в модальном окне поверх родителя"""
        messagebox.showerror("Ошибка", message, parent=parent)
        # Возвращаем фокус на родительское окно
        parent.lift()
        parent.focus_force()
    
    def show_warning(self, parent, message):
        """Показать предупреждение в модальном окне поверх родителя"""
        messagebox.showwarning("Предупреждение", message, parent=parent)
        parent.lift()
        parent.focus_force()
    
    def show_info(self, parent, message):
        """Показать информацию в модальном окне поверх родителя"""
        messagebox.showinfo("Информация", message, parent=parent)
        parent.lift()
        parent.focus_force()
    
    def setup_ui(self):
        """Настройка интерфейса"""
        try:
            # Верхняя панель с фильтрами
            filter_frame = ttk.LabelFrame(self.root, text="Фильтры", padding=10)
            filter_frame.pack(fill=tk.X, padx=10, pady=5)
            
            filters_inner = ttk.Frame(filter_frame)
            filters_inner.pack(fill=tk.X)
            
            ttk.Label(filters_inner, text="Статус:").pack(side=tk.LEFT, padx=5)
            self.status_filter = ttk.Combobox(filters_inner, values=['Все'] + ORDER_STATUSES, width=15)
            self.status_filter.set('Все')
            self.status_filter.pack(side=tk.LEFT, padx=5)
            self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_orders())
            
            ttk.Label(filters_inner, text="Дата (ГГГГ-ММ-ДД):").pack(side=tk.LEFT, padx=5)
            self.date_filter = ttk.Entry(filters_inner, width=12)
            self.date_filter.pack(side=tk.LEFT, padx=5)
            
            ttk.Button(filters_inner, text="Применить", command=self.load_orders).pack(side=tk.LEFT, padx=2)
            ttk.Button(filters_inner, text="Сбросить", command=self.clear_filters).pack(side=tk.LEFT, padx=2)
            
            # Панель кнопок - одна строка
            button_frame = ttk.LabelFrame(self.root, text="Управление", padding=10)
            button_frame.pack(fill=tk.X, padx=10, pady=5)
            
            ttk.Button(button_frame, text="Добавить заказ", command=self.add_order, width=18).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Редактировать заказ", command=self.edit_order, width=22).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Удалить заказ", command=self.delete_order, width=18).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Показать отчёт", command=self.show_report, width=18).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Управление клиентами", command=self.manage_customers, width=22).pack(side=tk.LEFT, padx=5)
            
            # Таблица заказов
            table_frame = ttk.LabelFrame(self.root, text="Список заказов", padding=10)
            table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            tree_frame = ttk.Frame(table_frame)
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            columns = ('ID', 'Дата', 'Клиент', 'Телефон', 'Статус', 'Сумма')
            self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=20)
            
            self.tree.heading('ID', text='ID')
            self.tree.heading('Дата', text='Дата')
            self.tree.heading('Клиент', text='Клиент')
            self.tree.heading('Телефон', text='Телефон')
            self.tree.heading('Статус', text='Статус')
            self.tree.heading('Сумма', text='Сумма (руб.)')
            
            self.tree.column('ID', width=50)
            self.tree.column('Дата', width=100)
            self.tree.column('Клиент', width=200)
            self.tree.column('Телефон', width=120)
            self.tree.column('Статус', width=100)
            self.tree.column('Сумма', width=120)
            
            v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
            h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
            self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
            
            self.tree.grid(row=0, column=0, sticky='nsew')
            v_scrollbar.grid(row=0, column=1, sticky='ns')
            h_scrollbar.grid(row=1, column=0, sticky='ew')
            
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)
            
            self.statusbar = ttk.Label(self.root, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
            self.statusbar.pack(fill=tk.X, padx=10, pady=5)
            
            self.tree.bind('<Double-Button-1>', lambda e: self.edit_order())
        except Exception as e:
            logger.error(f"Ошибка при настройке UI: {e}")
            self.show_error(self.root, f"Не удалось загрузить интерфейс: {str(e)}")
    
    def clear_filters(self):
        self.status_filter.set('Все')
        self.date_filter.delete(0, tk.END)
        self.load_orders()
    
    def load_orders(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            status = None if self.status_filter.get() == 'Все' else self.status_filter.get()
            date_filter = self.date_filter.get() if self.date_filter.get() else None
            
            orders = self.db.get_all_orders(status_filter=status, date_filter=date_filter)
            
            for order in orders:
                customer = self.db.get_customer(order.customer_id)
                customer_name = customer.name if customer else f"ID:{order.customer_id}"
                customer_phone = customer.phone if customer else ""
                
                self.tree.insert('', tk.END, values=(
                    order.id, order.order_date, customer_name, customer_phone, order.status, f"{order.total:.2f}"
                ))
            
            self.statusbar.config(text=f"Загружено заказов: {len(orders)}")
        except Exception as e:
            logger.error(f"Ошибка загрузки заказов: {e}")
            self.show_error(self.root, f"Не удалось загрузить заказы: {str(e)}")
    
    def add_order(self):
        try:
            dialog = OrderDialog(self.root, self.db)
            dialog.transient(self.root)  # Делаем диалог дочерним окном
            dialog.grab_set()  # Захватываем фокус
            self.root.wait_window(dialog)
            if dialog.result:
                self.db.create_order(dialog.result)
                self.load_orders()
                self.show_info(self.root, "Заказ успешно добавлен")
        except Exception as e:
            logger.error(f"Ошибка при добавлении заказа: {e}")
            self.show_error(self.root, f"Не удалось добавить заказ: {str(e)}")
    
    def edit_order(self):
        try:
            selection = self.tree.selection()
            if not selection:
                self.show_warning(self.root, "Пожалуйста, выберите заказ для редактирования")
                return
            
            order_id = self.tree.item(selection[0])['values'][0]
            order = self.db.get_order(order_id)
            
            if order:
                dialog = OrderDialog(self.root, self.db, order)
                dialog.transient(self.root)  # Делаем диалог дочерним окном
                dialog.grab_set()  # Захватываем фокус
                self.root.wait_window(dialog)
                if dialog.result:
                    dialog.result.id = order_id
                    self.db.update_order(dialog.result)
                    self.load_orders()
                    self.show_info(self.root, "Заказ успешно обновлён")
        except Exception as e:
            logger.error(f"Ошибка при редактировании заказа: {e}")
            self.show_error(self.root, f"Не удалось отредактировать заказ: {str(e)}")
    
    def delete_order(self):
        try:
            selection = self.tree.selection()
            if not selection:
                self.show_warning(self.root, "Пожалуйста, выберите заказ для удаления")
                return
            
            if messagebox.askyesno("Подтверждение", "Вы действительно хотите удалить выбранный заказ?", parent=self.root):
                order_id = self.tree.item(selection[0])['values'][0]
                self.db.delete_order(order_id)
                self.load_orders()
                self.show_info(self.root, "Заказ удалён")
        except Exception as e:
            logger.error(f"Ошибка при удалении заказа: {e}")
            self.show_error(self.root, f"Не удалось удалить заказ: {str(e)}")
    
    def show_report(self):
        try:
            report_window = tk.Toplevel(self.root)
            report_window.title("Отчёт по заказам")
            report_window.geometry("600x500")
            report_window.resizable(False, False)
            report_window.transient(self.root)  # Делаем дочерним
            report_window.grab_set()  # Захватываем фокус
            
            main_frame = ttk.Frame(report_window, padding=10)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            title_label = ttk.Label(main_frame, text="ОТЧЁТ ПО ЗАКАЗАМ", font=('Arial', 14, 'bold'))
            title_label.pack(pady=10)
            
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill=tk.BOTH, expand=True)
            
            text = tk.Text(text_frame, wrap=tk.WORD, font=('Courier', 10))
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            report_text = "=" * 50 + "\n"
            report_text += "           СТАТИСТИКА ЗАКАЗОВ\n"
            report_text += "=" * 50 + "\n\n"
            
            report_text += "1. Количество заказов по статусам:\n"
            report_text += "-" * 40 + "\n"
            status_counts = self.db.get_orders_by_status_count()
            for status, count in status_counts.items():
                report_text += f"   • {status}: {count} шт.\n"
            
            report_text += "\n2. Топ-3 клиента по сумме заказов:\n"
            report_text += "-" * 40 + "\n"
            top_customers = self.db.get_top_customers(3)
            if top_customers:
                for i, (cid, name, total) in enumerate(top_customers, 1):
                    report_text += f"   {i}. {name} - {total:.2f} руб.\n"
            else:
                report_text += "   Нет данных\n"
            
            report_text += "\n3. Общая выручка:\n"
            report_text += "-" * 40 + "\n"
            report_text += f"   • За день:    {self.db.get_total_revenue('day'):.2f} руб.\n"
            report_text += f"   • За неделю:  {self.db.get_total_revenue('week'):.2f} руб.\n"
            report_text += f"   • За месяц:   {self.db.get_total_revenue('month'):.2f} руб.\n"
            
            report_text += "\n" + "=" * 50 + "\n"
            report_text += "            Конец отчёта\n"
            report_text += "=" * 50
            
            text.insert(tk.END, report_text)
            text.config(state=tk.DISABLED)
            
            ttk.Button(main_frame, text="Закрыть", command=report_window.destroy).pack(pady=10)
        except Exception as e:
            logger.error(f"Ошибка при формировании отчёта: {e}")
            self.show_error(self.root, f"Не удалось сформировать отчёт: {str(e)}")
    
    def manage_customers(self):
        try:
            dialog = CustomerManager(self.root, self.db)
            dialog.transient(self.root)
            dialog.grab_set()
        except Exception as e:
            logger.error(f"Ошибка при открытии управления клиентами: {e}")
            self.show_error(self.root, f"Не удалось открыть управление клиентами: {str(e)}")


class OrderDialog(tk.Toplevel):
    """Диалог добавления/редактирования заказа с валидацией"""
    
    def __init__(self, parent, db, order=None):
        super().__init__(parent)
        self.db = db
        self.order = order
        self.result = None
        
        self.title("Создание заказа" if not order else "Редактирование заказа")
        self.geometry("650x650")
        self.resizable(False, False)
        
        # Делаем окно модальным и поверх родителя
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        if order:
            self.load_data()
        
        # Центрируем окно относительно родителя
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
    
    def show_error(self, message):
        """Показать ошибку в этом диалоге"""
        messagebox.showerror("Ошибка", message, parent=self)
        self.lift()
        self.focus_force()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Клиент
        customer_frame = ttk.LabelFrame(main_frame, text="Информация о клиенте", padding=10)
        customer_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(customer_frame, text="Клиент:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.customer_combo = ttk.Combobox(customer_frame, width=45)
        self.customer_combo.grid(row=0, column=1, padx=5, pady=5)
        self.load_customers()
        
        ttk.Button(customer_frame, text="Новый клиент", command=self.add_new_customer).grid(row=0, column=2, padx=5, pady=5)
        
        # Дата и статус
        info_frame = ttk.LabelFrame(main_frame, text="Детали заказа", padding=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(info_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.date_entry = ttk.Entry(info_frame, width=20)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.date_entry.insert(0, date.today().isoformat())
        
        ttk.Label(info_frame, text="Статус:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.status_combo = ttk.Combobox(info_frame, values=ORDER_STATUSES, width=18)
        self.status_combo.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.status_combo.set('новый')
        
        # Товары
        items_frame = ttk.LabelFrame(main_frame, text="Состав заказа", padding=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        list_frame = ttk.Frame(items_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.items_listbox = tk.Listbox(list_frame, width=50, height=8, font=('Courier', 10))
        self.items_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.items_listbox.yview)
        self.items_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        items_buttons = ttk.Frame(items_frame)
        items_buttons.pack(fill=tk.X, pady=5)
        
        ttk.Button(items_buttons, text="Добавить товар", command=self.add_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(items_buttons, text="Удалить товар", command=self.remove_item).pack(side=tk.LEFT, padx=5)
        
        self.items = []
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=15)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save, width=15).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy, width=15).pack(side=tk.RIGHT, padx=5)
    
    def load_customers(self):
        try:
            customers = self.db.get_all_customers()
            self.customer_combo['values'] = [f"{c.id}: {c.name} (тел: {c.phone})" for c in customers]
        except Exception as e:
            logger.error(f"Ошибка загрузки клиентов: {e}")
            self.show_error("Не удалось загрузить список клиентов")
    
    def add_new_customer(self):
        try:
            dialog = CustomerDialog(self, self.db)
            dialog.transient(self)
            dialog.grab_set()
            self.wait_window(dialog)
            if dialog.result:
                self.db.create_customer(dialog.result)
                self.load_customers()
                messagebox.showinfo("Успех", "Клиент добавлен! Теперь выберите его в списке.", parent=self)
                self.lift()
                self.focus_force()
        except Exception as e:
            logger.error(f"Ошибка при создании клиента: {e}")
            self.show_error(f"Не удалось создать клиента: {str(e)}")
    
    def load_data(self):
        try:
            customer = self.db.get_customer(self.order.customer_id)
            self.customer_combo.set(f"{customer.id}: {customer.name} (тел: {customer.phone})")
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, self.order.order_date)
            self.status_combo.set(self.order.status)
            self.items = self.order.items.copy()
            self.update_items_list()
        except Exception as e:
            logger.error(f"Ошибка загрузки данных заказа: {e}")
            self.show_error(f"Не удалось загрузить данные заказа: {str(e)}")
            self.destroy()
    
    def add_item(self):
        try:
            dialog = ItemDialog(self)
            dialog.transient(self)
            dialog.grab_set()
            self.wait_window(dialog)
            if dialog.result:
                self.items.append(dialog.result)
                self.update_items_list()
        except Exception as e:
            logger.error(f"Ошибка при добавлении товара: {e}")
            self.show_error(f"Не удалось добавить товар: {str(e)}")
    
    def remove_item(self):
        selection = self.items_listbox.curselection()
        if selection:
            del self.items[selection[0]]
            self.update_items_list()
    
    def update_items_list(self):
        self.items_listbox.delete(0, tk.END)
        for i, item in enumerate(self.items, 1):
            self.items_listbox.insert(tk.END, f"{i}. {item.product_name} | {item.quantity} шт x {item.price:.2f} = {item.total:.2f} руб.")
    
    def save(self):
        try:
            # Проверка выбора клиента
            customer_str = self.customer_combo.get()
            if not customer_str:
                self.show_error("Выберите клиента из списка")
                return
            
            try:
                customer_id = int(customer_str.split(':')[0])
            except (ValueError, IndexError):
                self.show_error("Неверный формат выбора клиента")
                return
            
            # Проверка даты
            order_date = self.date_entry.get().strip()
            if not order_date:
                self.show_error("Введите дату")
                return
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', order_date):
                self.show_error("Неверный формат даты. Используйте ГГГГ-ММ-ДД (например: 2024-01-15)")
                return
            try:
                date.fromisoformat(order_date)
            except ValueError:
                self.show_error("Неверная дата. Проверьте, что день и месяц корректны")
                return
            
            # Проверка статуса
            status = self.status_combo.get()
            if not status:
                self.show_error("Выберите статус заказа")
                return
            if status not in ORDER_STATUSES:
                self.show_error(f"Неверный статус. Доступные статусы: {', '.join(ORDER_STATUSES)}")
                return
            
            # Проверка наличия товаров
            if not self.items:
                self.show_error("Добавьте хотя бы один товар")
                return
            
            # Рассчитываем сумму
            total = sum(item.total for item in self.items)
            
            self.result = Order(None, customer_id, order_date, status, total, self.items)
            self.destroy()
        except Exception as e:
            logger.error(f"Ошибка при сохранении заказа: {e}")
            self.show_error(f"Не удалось сохранить заказ: {str(e)}")


class ItemDialog(tk.Toplevel):
    """Диалог добавления товара с валидацией"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        
        self.title("Добавление товара")
        self.geometry("450x350")
        self.resizable(False, False)
        
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Центрируем
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Название товара:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.name_entry.pack(fill=tk.X, pady=5)
        
        ttk.Label(main_frame, text="Количество:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.quantity_entry = ttk.Entry(main_frame, width=15, font=('Arial', 10))
        self.quantity_entry.pack(anchor=tk.W, pady=5)
        
        ttk.Label(main_frame, text="Цена за единицу (руб.):", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.price_entry = ttk.Entry(main_frame, width=15, font=('Arial', 10))
        self.price_entry.pack(anchor=tk.W, pady=5)
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Добавить", command=self.save, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy, width=12).pack(side=tk.RIGHT, padx=5)
    
    def save(self):
        try:
            name = self.name_entry.get().strip()
            quantity_str = self.quantity_entry.get().strip()
            price_str = self.price_entry.get().strip()
            
            # Валидация названия товара
            if not name:
                messagebox.showerror("Ошибка", "Введите название товара", parent=self)
                return
            if len(name) < 2:
                messagebox.showerror("Ошибка", "Название товара должно содержать минимум 2 символа", parent=self)
                return
            
            # Валидация количества
            try:
                quantity = int(quantity_str)
                if quantity <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть больше 0", parent=self)
                    return
                if quantity > 10000:
                    messagebox.showerror("Ошибка", "Количество не может превышать 10000", parent=self)
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Количество должно быть целым числом", parent=self)
                return
            
            # Валидация цены
            try:
                price = float(price_str)
                if price <= 0:
                    messagebox.showerror("Ошибка", "Цена должна быть больше 0", parent=self)
                    return
                if price > 1000000:
                    messagebox.showerror("Ошибка", "Цена не может превышать 1 000 000 руб.", parent=self)
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Цена должна быть числом", parent=self)
                return
            
            self.result = OrderItem(name, quantity, price)
            self.destroy()
        except Exception as e:
            logger.error(f"Ошибка при сохранении товара: {e}")
            messagebox.showerror("Ошибка", f"Не удалось добавить товар: {str(e)}", parent=self)


class CustomerManager(tk.Toplevel):
    """Управление клиентами"""
    
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        
        self.title("Управление клиентами")
        self.geometry("900x500")
        
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Центрируем
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        self.load_customers()
    
    def show_error(self, message):
        messagebox.showerror("Ошибка", message, parent=self)
        self.lift()
        self.focus_force()
    
    def setup_ui(self):
        button_frame = ttk.Frame(self, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Добавить клиента", command=self.add_customer, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Редактировать", command=self.edit_customer, width=18).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить", command=self.delete_customer, width=18).pack(side=tk.LEFT, padx=5)
        
        table_frame = ttk.Frame(self, padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ('ID', 'Имя', 'Телефон', 'Адрес')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('ID', text='ID')
        self.tree.heading('Имя', text='Имя')
        self.tree.heading('Телефон', text='Телефон')
        self.tree.heading('Адрес', text='Адрес')
        
        self.tree.column('ID', width=50)
        self.tree.column('Имя', width=200)
        self.tree.column('Телефон', width=150)
        self.tree.column('Адрес', width=400)
        
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_customer())
    
    def load_customers(self):
        try:
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            customers = self.db.get_all_customers()
            for customer in customers:
                self.tree.insert('', tk.END, values=(customer.id, customer.name, customer.phone, customer.address))
        except Exception as e:
            logger.error(f"Ошибка загрузки клиентов: {e}")
            self.show_error(f"Не удалось загрузить клиентов: {str(e)}")
    
    def add_customer(self):
        try:
            dialog = CustomerDialog(self, self.db)
            dialog.transient(self)
            dialog.grab_set()
            self.wait_window(dialog)
            if dialog.result:
                self.db.create_customer(dialog.result)
                self.load_customers()
                messagebox.showinfo("Успех", "Клиент успешно добавлен", parent=self)
        except Exception as e:
            logger.error(f"Ошибка при добавлении клиента: {e}")
            self.show_error(f"Не удалось добавить клиента: {str(e)}")
    
    def edit_customer(self):
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите клиента для редактирования", parent=self)
                return
            
            customer_id = self.tree.item(selection[0])['values'][0]
            customer = self.db.get_customer(customer_id)
            
            if customer:
                dialog = CustomerDialog(self, self.db, customer)
                dialog.transient(self)
                dialog.grab_set()
                self.wait_window(dialog)
                if dialog.result:
                    dialog.result.id = customer_id
                    self.db.update_customer(dialog.result)
                    self.load_customers()
                    messagebox.showinfo("Успех", "Клиент успешно обновлён", parent=self)
        except Exception as e:
            logger.error(f"Ошибка при редактировании клиента: {e}")
            self.show_error(f"Не удалось отредактировать клиента: {str(e)}")
    
    def delete_customer(self):
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Предупреждение", "Выберите клиента для удаления", parent=self)
                return
            
            customer_id = self.tree.item(selection[0])['values'][0]
            
            if messagebox.askyesno("Подтверждение", "Удалить клиента?\n\nЕсли у клиента есть заказы, удаление будет невозможно.", parent=self):
                if self.db.delete_customer(customer_id):
                    self.load_customers()
                    messagebox.showinfo("Успех", "Клиент успешно удалён", parent=self)
                else:
                    messagebox.showerror("Ошибка", "Нельзя удалить клиента с существующими заказами", parent=self)
        except Exception as e:
            logger.error(f"Ошибка при удалении клиента: {e}")
            self.show_error(f"Не удалось удалить клиента: {str(e)}")


class CustomerDialog(tk.Toplevel):
    """Диалог добавления/редактирования клиента с валидацией"""
    
    def __init__(self, parent, db, customer=None):
        super().__init__(parent)
        self.db = db
        self.customer = customer
        self.result = None
        
        self.title("Новый клиент" if not customer else "Редактирование клиента")
        self.geometry("450x400")
        self.resizable(False, False)
        
        # Делаем окно модальным
        self.transient(parent)
        self.grab_set()
        
        # Центрируем
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")
        
        self.setup_ui()
        if customer:
            self.load_data()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(main_frame, text="Имя клиента:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.name_entry.pack(fill=tk.X, pady=5)
        
        ttk.Label(main_frame, text="Телефон:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.phone_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.phone_entry.pack(fill=tk.X, pady=5)
        
        ttk.Label(main_frame, text="Адрес:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        self.address_entry = ttk.Entry(main_frame, width=40, font=('Arial', 10))
        self.address_entry.pack(fill=tk.X, pady=5)
        
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=15)
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy, width=12).pack(side=tk.RIGHT, padx=5)
    
    def load_data(self):
        self.name_entry.insert(0, self.customer.name)
        self.phone_entry.insert(0, self.customer.phone)
        self.address_entry.insert(0, self.customer.address)
    
    def save(self):
        try:
            name = self.name_entry.get().strip()
            phone = self.phone_entry.get().strip()
            address = self.address_entry.get().strip()
            
            # Валидация имени
            if not name:
                messagebox.showerror("Ошибка", "Введите имя клиента", parent=self)
                return
            if len(name) < 2:
                messagebox.showerror("Ошибка", "Имя должно содержать минимум 2 символа", parent=self)
                return
            if not re.match(r'^[а-яА-Яa-zA-Z\s\-]+$', name):
                messagebox.showerror("Ошибка", "Имя может содержать только буквы, дефис и пробелы", parent=self)
                return
            
            # Валидация телефона (необязательное поле)
            if phone:
                clean_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
                if not re.match(r'^\d{10,15}$', clean_phone):
                    messagebox.showerror("Ошибка", "Телефон должен содержать 10-15 цифр", parent=self)
                    return
            
            # Валидация адреса
            if not address:
                messagebox.showerror("Ошибка", "Введите адрес", parent=self)
                return
            if len(address) < 5:
                messagebox.showerror("Ошибка", "Адрес должен содержать минимум 5 символов", parent=self)
                return
            
            self.result = Customer(None, name, phone, address)
            self.destroy()
        except Exception as e:
            logger.error(f"Ошибка при сохранении клиента: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить клиента: {str(e)}", parent=self)


def main():
    try:
        root = tk.Tk()
        app = DeliveryApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске приложения: {e}")
        print(f"Ошибка: {e}")
        input("Нажмите Enter для выхода...")


if __name__ == '__main__':
    main()