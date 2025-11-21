#!/usr/bin/env python3
"""
Точка входа для запуска бота Battery Balancer
"""
import os
import sys

# Добавляем src в путь для импортов
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from bot import main

if __name__ == "__main__":
    main()