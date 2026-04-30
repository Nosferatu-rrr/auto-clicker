#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль автокликера с распознаванием изображений.
Поиск изображений на экране и автоматический клик.
"""

import os
import time
import threading
import glob
from PIL import Image
import pyautogui
import cv2
import numpy as np


class AutoClicker:
    """Автокликер с поиском изображений на экране."""
    
    def __init__(self, images_dir="clicker_images", confidence=0.8, delay=0.5):
        """
        Инициализация кликера.
        
        Args:
            images_dir: Папка с изображениями-образцами
            confidence: Точность поиска (0.0 - 1.0)
            delay: Задержка между кликами в секундах
        """
        self.images_dir = images_dir
        self.confidence = confidence
        self.delay = delay
        
        self.is_running = False
        self.is_paused = False
        self.stop_event = threading.Event()
        self.click_thread = None
        
        self.images = []
        self.log_callback = None
        
    def set_log_callback(self, callback):
        """
        Установить функцию для логирования.
        
        Args:
            callback: Функция с сигнатурой log(message, level='info')
        """
        self.log_callback = callback
    
    def log(self, message, level='info'):
        """Вывод сообщения в лог."""
        timestamp = time.strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] [{level.upper()}] {message}"
        print(log_msg)
        if self.log_callback:
            self.log_callback(log_msg)
    
    def load_images(self):
        """Загрузить все изображения из папки."""
        self.images = []
        
        if not os.path.exists(self.images_dir):
            self.log(f"Папка изображений не найдена: {self.images_dir}", 'warning')
            return False
        
        # Поддерживаемые расширения
        extensions = ['*.png', '*.jpg', '*.jpeg', '*.bmp']
        
        for ext in extensions:
            pattern = os.path.join(self.images_dir, ext)
            self.images.extend(glob.glob(pattern))
        
        self.log(f"Загружено изображений: {len(self.images)}", 'info')
        return len(self.images) > 0
    
    def find_image_on_screen(self, template_path):
        """
        Найти изображение на экране.
        
        Args:
            template_path: Путь к изображению-образцу
            
        Returns:
            tuple: (x, y) координаты центра или None
        """
        try:
            # Загружаем шаблон
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.log(f"Не удалось загрузить изображение: {template_path}", 'error')
                return None
            
            # Делаем скриншот экрана
            screenshot = pyautogui.screenshot()
            screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Поиск шаблона
            result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # Проверка точности
            if max_val >= self.confidence:
                # Вычисляем центр
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            self.log(f"Ошибка поиска изображения: {e}", 'error')
            return None
    
    def click_at_position(self, x, y):
        """
        Кликнуть по координатам.
        
        Args:
            x: Координата X
            y: Координата Y
        """
        try:
            pyautogui.click(x, y)
            self.log(f"Клик по координатам ({x}, {y})", 'info')
        except Exception as e:
            self.log(f"Ошибка клика: {e}", 'error')
    
    def click_loop(self):
        """Основной цикл кликера."""
        self.log("Кликер запущен", 'info')
        
        while not self.stop_event.is_set():
            if self.is_paused:
                time.sleep(0.1)
                continue
            
            # Загружаем изображения при каждом цикле
            if not self.load_images():
                time.sleep(1)
                continue
            
            found = False
            
            # Проверяем каждое изображение
            for img_path in self.images:
                if self.stop_event.is_set():
                    break
                
                position = self.find_image_on_screen(img_path)
                if position:
                    self.click_at_position(position[0], position[1])
                    found = True
                    time.sleep(self.delay)
                    break
            
            if not found:
                time.sleep(0.5)  # Небольшая задержка перед следующим поиском
        
        self.log("Кликер остановлен", 'info')
    
    def start(self):
        """Запустить кликер."""
        if self.is_running:
            self.log("Кликер уже запущен", 'warning')
            return False
        
        self.is_running = True
        self.is_paused = False
        self.stop_event.clear()
        
        # Создаем поток для кликера
        self.click_thread = threading.Thread(target=self.click_loop, daemon=True)
        self.click_thread.start()
        
        self.log("Кликер запущен в фоновом режиме", 'info')
        return True
    
    def stop(self):
        """Остановить кликер."""
        if not self.is_running:
            self.log("Кликер не запущен", 'warning')
            return False
        
        self.stop_event.set()
        self.is_running = False
        
        if self.click_thread and self.click_thread.is_alive():
            self.click_thread.join(timeout=2)
        
        self.log("Кликер остановлен", 'info')
        return True
    
    def toggle(self):
        """Переключить состояние кликера."""
        if self.is_running:
            self.stop()
            return False
        else:
            return self.start()
    
    def pause(self):
        """Приостановить кликер."""
        self.is_paused = True
        self.log("Кликер приостановлен", 'info')
    
    def resume(self):
        """Возобновить кликер."""
        self.is_paused = False
        self.log("Кликер возобновлен", 'info')
    
    def get_status(self):
        """Получить статус кликера."""
        return {
            'running': self.is_running,
            'paused': self.is_paused,
            'images_count': len(self.images)
        }


if __name__ == "__main__":
    # Тестовый запуск
    clicker = AutoClicker(images_dir="clicker_images", confidence=0.8, delay=0.5)
    clicker.set_log_callback(lambda msg: print(msg))
    
    print("Тест кликера...")
    clicker.start()
    
    time.sleep(5)
    
    clicker.stop()
    print("Тест завершен")
