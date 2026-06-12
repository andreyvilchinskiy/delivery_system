import logging
import os
from datetime import datetime

def setup_logger():
    """Настройка логирования"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    log_filename = f'logs/app_{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)