#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Clicker - Графический интерфейс для автокликера.
Поддержка Linux (X11).
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading

# Импорт локальных модулей
from clicker import AutoClicker
from screenshot import ScreenshotEditor


class AutoClickerGUI:
    """Графический интерфейс автокликера."""
    
    def __init__(self):
        """Инициализация GUI."""
        self.root = tk.Tk()
        self.root.title("Auto Clicker")
        self.root.geometry("500x450")
        self.root.resizable(True, True)
        
        # Настройки
        self.images_dir = "clicker_images"
        self.confidence = tk.DoubleVar(value=0.8)
        self.delay = tk.DoubleVar(value=0.5)
        
        # Инициализация кликера
        self.clicker = AutoClicker(
            images_dir=self.images_dir,
            confidence=self.confidence.get(),
            delay=self.delay.get()
        )
        self.clicker.set_log_callback(self.add_log)
        
        # Переменные состояния
        self.is_running = False
        
        # Создаем интерфейс
        self.create_widgets()
        
        # Обновление статуса
        self.update_status()
    
    def create_widgets(self):
        """Создание виджетов интерфейса."""
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка расширения сетки
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame, 
            text="🖱️ Auto Clicker", 
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Статус
        self.status_label = ttk.Label(
            main_frame, 
            text="Статус: Остановлен", 
            font=('Arial', 12),
            foreground='red'
        )
        self.status_label.grid(row=1, column=0, pady=(0, 20))
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=(0, 20))
        
        self.toggle_btn = ttk.Button(
            button_frame, 
            text="🔴 Включить", 
            command=self.toggle_clicker,
            width=15
        )
        self.toggle_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(
            button_frame, 
            text="⏹️ Стоп", 
            command=self.stop_clicker,
            width=15,
            state='disabled'
        )
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        self.screenshot_btn = ttk.Button(
            button_frame, 
            text="📸 Скриншот", 
            command=self.take_screenshot,
            width=15
        )
        self.screenshot_btn.grid(row=0, column=2, padx=5)
        
        # Настройки
        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Настройки", padding="10")
        settings_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        settings_frame.columnconfigure(1, weight=1)
        
        ttk.Label(settings_frame, text="Точность поиска:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.confidence, 
                 command=self.on_setting_change).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.confidence_label = ttk.Label(settings_frame, text="0.80")
        self.confidence_label.grid(row=0, column=2, padx=5)
        
        ttk.Label(settings_frame, text="Задержка (сек):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Scale(settings_frame, from_=0.1, to=5.0, variable=self.delay,
                 command=self.on_setting_change).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.delay_label = ttk.Label(settings_frame, text="0.5")
        self.delay_label.grid(row=1, column=2, padx=5)
        
        # Информация о папке с изображениями
        info_frame = ttk.LabelFrame(main_frame, text="📁 Образцы", padding="10")
        info_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Кнопка открытия папки
        open_folder_btn = ttk.Button(
            info_frame, 
            text="Открыть папку с образцами", 
            command=self.open_images_folder
        )
        open_folder_btn.grid(row=0, column=0, pady=5)
        
        self.images_count_label = ttk.Label(info_frame, text="Найдено образцов: 0")
        self.images_count_label.grid(row=1, column=0, pady=5)
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="📋 Лог событий", padding="10")
        log_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            wrap=tk.WORD,
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопка очистки лога
        clear_log_btn = ttk.Button(
            log_frame, 
            text="Очистить лог", 
            command=self.clear_log
        )
        clear_log_btn.grid(row=1, column=0, pady=5)
        
        # Сетка для растягивания
        main_frame.rowconfigure(5, weight=1)
    
    def toggle_clicker(self):
        """Переключить состояние кликера."""
        if self.is_running:
            self.stop_clicker()
        else:
            self.start_clicker()
    
    def start_clicker(self):
        """Запустить кликер."""
        # Обновляем настройки
        self.clicker.confidence = self.confidence.get()
        self.clicker.delay = self.delay.get()
        
        # Проверяем наличие изображений
        if not os.path.exists(self.images_dir) or not os.listdir(self.images_dir):
            messagebox.showwarning(
                "Внимание", 
                f"Папка '{self.images_dir}' пуста или не существует.\n"
                f"Сначала сохраните изображения-образцы (кнопка 'Скриншот')."
            )
            return
        
        if self.clicker.start():
            self.is_running = True
            self.status_label.config(text="Статус: Запущен", foreground='green')
            self.toggle_btn.config(text="🟢 Выключить")
            self.stop_btn.config(state='normal')
            self.add_log("Кликер запущен", 'info')
    
    def stop_clicker(self):
        """Остановить кликер."""
        if self.clicker.stop():
            self.is_running = False
            self.status_label.config(text="Статус: Остановлен", foreground='red')
            self.toggle_btn.config(text="🔴 Включить")
            self.stop_btn.config(state='disabled')
            self.add_log("Кликер остановлен", 'info')
    
    def take_screenshot(self):
        """Сделать скриншот и сохранить образец."""
        self.add_log("Открытие редактора скриншотов...", 'info')
        
        def on_save(filename):
            self.add_log(f"Изображение сохранено: {filename}", 'success')
            self.root.after(0, self.update_images_count)
        
        # Создаем редактор
        editor = ScreenshotEditor(self.images_dir)
        editor.on_save_callback = on_save
        
        # Запускаем редактор (он создаст свое окно и mainloop)
        editor.show_editor()
    
    def on_setting_change(self, *args):
        """Обработка изменения настроек."""
        self.confidence_label.config(text=f"{self.confidence.get():.2f}")
        self.delay_label.config(text=f"{self.delay.get():.1f}")
    
    def add_log(self, message, level='info'):
        """Добавить сообщение в лог."""
        self.log_text.config(state='normal')
        
        # Цвет в зависимости от уровня
        if level == 'error':
            color = 'red'
        elif level == 'warning':
            color = 'orange'
        elif level == 'success':
            color = 'green'
        else:
            color = 'black'
        
        self.log_text.insert(tk.END, f"{message}\n", color)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def clear_log(self):
        """Очистить лог."""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.config(state='disabled')
    
    def open_images_folder(self):
        """Открыть папку с изображениями."""
        import subprocess
        
        if os.path.exists(self.images_dir):
            try:
                # Открытие папки в файловом менеджере
                subprocess.run(['xdg-open', self.images_dir])
                self.add_log(f"Открыта папка: {self.images_dir}", 'info')
            except Exception as e:
                self.add_log(f"Ошибка открытия папки: {e}", 'error')
        else:
            messagebox.showinfo("Информация", f"Папка '{self.images_dir}' еще не создана.")
    
    def update_images_count(self):
        """Обновить счетчик изображений."""
        if os.path.exists(self.images_dir):
            count = len([f for f in os.listdir(self.images_dir) 
                        if f.endswith(('.png', '.jpg', '.jpeg', '.bmp'))])
            self.images_count_label.config(text=f"Найдено образцов: {count}")
            return count
        return 0
    
    def update_status(self):
        """Периодическое обновление статуса."""
        if self.is_running:
            status = self.clicker.get_status()
            # Можно добавить дополнительную логику обновления
        self.root.after(1000, self.update_status)
    
    def on_closing(self):
        """Обработка закрытия окна."""
        if self.is_running:
            if messagebox.askokcancel("Выход", "Кликер запущен. Закрыть приложение?"):
                self.clicker.stop()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Запуск главного цикла приложения."""
        # Обновляем счетчик изображений при запуске
        self.update_images_count()
        
        # Обработка закрытия
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Запуск главного цикла
        self.root.mainloop()


def main():
    """Точка входа."""
    # Создаем папку для изображений
    os.makedirs("clicker_images", exist_ok=True)
    
    # Создаем и запускаем GUI
    app = AutoClickerGUI()
    app.run()


if __name__ == "__main__":
    main()