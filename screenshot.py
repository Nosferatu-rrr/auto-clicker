#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для создания скриншотов и выделения области на экране.
Работает в среде Linux с X11.
"""

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageGrab
import os
import datetime


class ScreenshotEditor:
    """Редактор скриншотов для сохранения изображений-образцов."""
    
    def __init__(self, images_dir="clicker_images"):
        """
        Инициализация редактора скриншотов.
        
        Args:
            images_dir: Папка для сохранения изображений
        """
        self.images_dir = images_dir
        os.makedirs(images_dir, exist_ok=True)
        
        self.root = None
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.image = None
        self.canvas = None
        self.rect = None
        self.temp_image_name = None
        
    def capture_full_screen(self):
        """Сделать скриншот всего экрана."""
        try:
            self.image = ImageGrab.grab()
            return True
        except Exception as e:
            print(f"Ошибка создания скриншота: {e}")
            return False
    
    def show_editor(self, parent_root, on_save_callback=None):
        """Показать редактор скриншотов."""
        if not self.capture_full_screen():
            messagebox.showerror("Ошибка", "Не удалось сделать скриншот")
            return None
        
        # Создаем Toplevel вместо Tk
        editor_window = tk.Toplevel(parent_root)
        editor_window.title("Выделите область для сохранения")
        editor_window.attributes('-fullscreen', True)
        editor_window.attributes('-topmost', True)
        
        self.root = editor_window
        
        # Canvas
        self.canvas = tk.Canvas(editor_window, cursor='cross', bg='gray20', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Конвертируем PIL Image в PhotoImage
        import io
        buffer = io.BytesIO()
        self.image.save(buffer, format='PNG')
        buffer.seek(0)
        self.photo = tk.PhotoImage(master=editor_window, data=buffer.getvalue())
        
        # Показываем скриншот
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        # Обработчики событий
        self.canvas.bind('<ButtonPress-1>', self.on_button_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_release)
        editor_window.bind('<Escape>', self.on_escape)
        
        # Инструкции
        info_text = "Выделите область мышкой. Нажмите ESC для отмены."
        self.canvas.create_text(50, 30, anchor=tk.NW, 
                                text=info_text, 
                                fill='yellow', 
                                font=('Arial', 14, 'bold'))
        
        self.on_save_callback = on_save_callback
        self.parent_root = parent_root
        
        return self.temp_image_name
    
    def on_button_press(self, event):
        """Обработка нажатия кнопки мыши."""
        self.start_x = event.x
        self.start_y = event.y
        
        # Создаем прямоугольник выделения
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, 
            self.start_x, self.start_y,
            outline='red', width=2
        )
    
    def on_drag(self, event):
        """Обработка перемещения мыши."""
        if self.rect:
            self.canvas.coords(self.rect, 
                              self.start_x, self.start_y, 
                              event.x, event.y)
    
    def on_button_release(self, event):
        """Обработка отпускания кнопки мыши."""
        self.end_x = event.x
        self.end_y = event.y
        
        # Показываем диалог для ввода имени файла
        self.show_save_dialog()
    
    def on_escape(self, event=None):
        """Обработка нажатия ESC - отмена."""
        if self.root:
            self.root.destroy()
            self.root = None
    
    def show_save_dialog(self):
        """Показать диалог сохранения изображения."""
        # Закрываем окно редактора (Toplevel)
        if self.root:
            self.root.destroy()
            self.root = None
        
        # Создаем Toplevel для диалога
        save_window = tk.Toplevel(self.parent_root)
        save_window.title("Сохранить изображение")
        save_window.geometry("350x150")
        save_window.resizable(False, False)
        save_window.attributes('-topmost', True)
        
        # Центрируем относительно родителя
        save_window.transient(self.parent_root)
        save_window.grab_set()
        
        tk.Label(save_window, text="Имя файла:", font=('Arial', 11)).pack(pady=10)
        
        # Генерируем имя по умолчанию
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"sample_{timestamp}.png"
        
        name_entry = tk.Entry(save_window, width=35, font=('Arial', 11))
        name_entry.insert(0, default_name)
        name_entry.pack(pady=5)
        name_entry.focus_set()
        
        def save_action():
            filename = name_entry.get().strip()
            if not filename:
                filename = default_name
            
            # Добавляем расширение, если нет
            if not filename.lower().endswith('.png'):
                filename += '.png'
            
            filepath = os.path.join(self.images_dir, filename)
            
            # Обрезаем изображение
            x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
            x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
            
            if abs(x1 - x2) < 5 or abs(y1 - y2) < 5:
                messagebox.showwarning("Внимание", "Область выделения слишком мала!")
                return
            
            try:
                cropped = self.image.crop((x1, y1, x2, y2))
                cropped.save(filepath)
                self.temp_image_name = filename
                
                save_window.destroy()
                
                if self.on_save_callback:
                    self.on_save_callback(filename)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")
        
        def cancel_action():
            save_window.destroy()
        
        btn_frame = tk.Frame(save_window)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="Сохранить", width=12, command=save_action).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="Отмена", width=12, command=cancel_action).pack(side=tk.LEFT, padx=10)
        
        # Привязка Enter к сохранению
        save_window.bind('<Return>', lambda e: save_action())
        save_window.bind('<Escape>', lambda e: cancel_action())


def make_screenshot(images_dir="clicker_images"):
    """
    Функция для быстрого создания скриншота.
    
    Args:
        images_dir: Папка для сохранения
        
    Returns:
        str: Имя сохраненного файла или None
    """
    editor = ScreenshotEditor(images_dir)
    
    filename = editor.show_editor()
    
    return filename


if __name__ == "__main__":
    # Тестовый запуск
    filename = make_screenshot()
    if filename:
        print(f"Изображение сохранено: {filename}")
    else:
        print("Сохранение отменено")
