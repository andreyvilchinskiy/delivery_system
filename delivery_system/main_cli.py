#!/usr/bin/env python3
import argparse
import sys
import os
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import Database
from data_export import DataExport
from logger_config import setup_logger
from models import ORDER_STATUSES

logger = setup_logger()


def get_period_name(period: str) -> str:
    """Преобразует период в русское название"""
    period_names = {
        'day': 'день',
        'week': 'неделю',
        'month': 'месяц'
    }
    return period_names.get(period, period)


def cmd_report(args):
    """Команда report - вывод отчёта"""
    db = Database()
    
    # Проверка периода
    if args.period not in ['day', 'week', 'month']:
        print(f"Ошибка: Неверный период '{args.period}'. Доступные: day, week, month")
        return
    
    period_rus = get_period_name(args.period)
    
    print("\n" + "=" * 50)
    print("              ОТЧЁТ ПО ЗАКАЗАМ")
    print("=" * 50)
    
    # 1. Количество заказов по статусам
    print("\n1. Количество заказов по статусам:")
    print("-" * 40)
    status_counts = db.get_orders_by_status_count()
    for status, count in status_counts.items():
        print(f"   • {status}: {count} шт.")
    
    # 2. Топ-3 клиента
    print("\n2. Топ-3 клиента по сумме заказов:")
    print("-" * 40)
    top_customers = db.get_top_customers(3)
    if top_customers:
        for i, (cid, name, total) in enumerate(top_customers, 1):
            print(f"   {i}. {name} - {total:.2f} руб.")
    else:
        print("   Нет данных")
    
    # 3. Общая выручка за период
    print(f"\n3. Общая выручка за {period_rus}:")
    print("-" * 40)
    revenue = db.get_total_revenue(args.period)
    print(f"   {revenue:.2f} руб.")
    
    print("\n" + "=" * 50)
    print("              Конец отчёта")
    print("=" * 50 + "\n")
    
    db.close()


def cmd_export(args):
    """Команда export - экспорт заказов"""
    db = Database()
    exporter = DataExport(db)
    
    # Проверка расширения файла
    if not args.file:
        print("Ошибка: Не указано имя файла")
        return
    
    # Определяем формат по расширению
    if args.file.endswith('.json'):
        try:
            exporter.export_orders_to_json(args.file)
            print(f"✅ Заказы успешно экспортированы в {args.file}")
        except Exception as e:
            print(f"❌ Ошибка при экспорте: {e}")
    elif args.file.endswith('.xml'):
        try:
            exporter.export_orders_to_xml(args.file)
            print(f"✅ Заказы успешно экспортированы в {args.file}")
        except Exception as e:
            print(f"❌ Ошибка при экспорте: {e}")
    else:
        print(f"❌ Ошибка: неподдерживаемый формат файла '{args.file}'")
        print("   Используйте файлы с расширением .json или .xml")
    
    db.close()


def cmd_import(args):
    """Команда import - импорт заказов"""
    db = Database()
    exporter = DataExport(db)
    
    # Проверка существования файла
    if not args.file:
        print("Ошибка: Не указано имя файла")
        return
    
    if not os.path.exists(args.file):
        print(f"❌ Ошибка: Файл '{args.file}' не найден")
        return
    
    # Проверка расширения файла
    if not (args.file.endswith('.json') or args.file.endswith('.xml')):
        print(f"❌ Ошибка: неподдерживаемый формат файла '{args.file}'")
        print("   Используйте файлы с расширением .json или .xml")
        return
    
    try:
        exporter.import_orders(args.file)
        print(f"✅ Заказы успешно импортированы из {args.file}")
    except Exception as e:
        print(f"❌ Ошибка при импорте: {e}")
    
    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Система учёта заказов "Быстрая доставка"',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Примеры:
  python main_cli.py report --period day
  python main_cli.py report --period week
  python main_cli.py report --period month
  python main_cli.py export --file orders.json
  python main_cli.py export --file orders.xml
  python main_cli.py import --file orders.json
  python main_cli.py import --file orders.xml
        '''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда report
    report_parser = subparsers.add_parser('report', help='Показать отчёт')
    report_parser.add_argument(
        '--period', 
        choices=['day', 'week', 'month'], 
        default='day',
        help='Период для выручки (day/week/month, по умолчанию: day)'
    )
    
    # Команда export
    export_parser = subparsers.add_parser('export', help='Экспорт заказов')
    export_parser.add_argument(
        '--file', 
        required=True, 
        help='Имя файла для экспорта (расширение .json или .xml)'
    )
    
    # Команда import
    import_parser = subparsers.add_parser('import', help='Импорт заказов')
    import_parser.add_argument(
        '--file', 
        required=True, 
        help='Имя файла для импорта (расширение .json или .xml)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'report':
        cmd_report(args)
    elif args.command == 'export':
        cmd_export(args)
    elif args.command == 'import':
        cmd_import(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()