#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Генератор иконок и логотипов для Zapret Android
Запустите один раз для создания всех необходимых изображений
После генерации файл можно удалить
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont
import math

class IconGenerator:
    """Генератор иконок с логотипом ZA (Zapret Android)"""
    
    def __init__(self):
        self.assets_dir = "assets"
        self.font_path = self._get_font_path()
        
        # Создаем папку assets если её нет
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # Цветовая схема
        self.colors = {
            'primary': '#00ff88',      # Неоново-зеленый
            'secondary': '#00aaff',    # Голубой
            'accent': '#ff5500',       # Оранжевый
            'background': '#000000',   # Черный фон
            'text': '#ffffff',         # Белый текст
            'gradient_start': '#0066ff',
            'gradient_end': '#00ccff'
        }
    
    def _get_font_path(self):
        """Поиск шрифта в системе"""
        # Список возможных путей к шрифтам
        font_paths = [
            # Android/Termux
            '/system/fonts/Roboto-Regular.ttf',
            '/system/fonts/DroidSans.ttf',
            # Linux
            '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            # Windows (если запускается оттуда)
            'C:/Windows/Fonts/arial.ttf',
            # Fallback - встроенный шрифт
            None
        ]
        
        for path in font_paths:
            if path and os.path.exists(path):
                return path
        
        return None
    
    def _create_gradient(self, width, height, start_color, end_color):
        """Создание градиентного фона"""
        gradient = Image.new('RGB', (width, height), start_color)
        draw = ImageDraw.Draw(gradient)
        
        for y in range(height):
            # Интерполяция цвета
            ratio = y / height
            r = int((1 - ratio) * int(start_color[1:3], 16) + ratio * int(end_color[1:3], 16))
            g = int((1 - ratio) * int(start_color[3:5], 16) + ratio * int(end_color[3:5], 16))
            b = int((1 - ratio) * int(start_color[5:7], 16) + ratio * int(end_color[5:7], 16))
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            draw.line([(0, y), (width, y)], fill=color)
        
        return gradient
    
    def _draw_za_logo(self, image_size=512, style='primary'):
        """Отрисовка логотипа ZA (Z и A наложены друг на друга)"""
        # Создаем изображение
        img = Image.new('RGBA', (image_size, image_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Центр изображения
        center = image_size // 2
        radius = image_size // 3
        
        # Определяем цвета в зависимости от стиля
        if style == 'primary':
            z_color = self.colors['primary']
            a_color = self.colors['secondary']
            glow_color = self.colors['primary'] + '80'  # С прозрачностью
        elif style == 'monochrome':
            z_color = '#ffffff'
            a_color = '#cccccc'
            glow_color = '#ffffff40'
        else:  # gradient
            z_color = self.colors['gradient_start']
            a_color = self.colors['gradient_end']
            glow_color = self.colors['gradient_start'] + '60'
        
        # Функция для рисования буквы Z с эффектом
        def draw_z(x, y, size, thickness, color):
            # Внешний контур Z (эффект свечения)
            draw.polygon([
                (x - size//2 - thickness, y - size//2 - thickness),
                (x + size//2 + thickness, y - size//2 - thickness),
                (x - size//2 - thickness, y + size//2 + thickness),
                (x - size//2 - thickness*2, y + size//2 + thickness)
            ], fill=glow_color)
            
            # Основная буква Z
            draw.polygon([
                (x - size//2, y - size//2),      # Верхний левый
                (x + size//2, y - size//2),      # Верхний правый
                (x - size//2, y + size//2),      # Нижний левый
                (x - size//2 - thickness, y + size//2)  # Для толщины
            ], fill=color)
            
            # Диагональная линия Z
            draw.line([
                (x + size//2, y - size//2),
                (x - size//2, y + size//2)
            ], fill=color, width=thickness*2)
        
        # Функция для рисования буквы A с эффектом
        def draw_a(x, y, size, thickness, color):
            # Внешний контур A (эффект свечения)
            draw.polygon([
                (x, y - size//2 - thickness),
                (x + size//3 + thickness, y + size//2 + thickness),
                (x - size//3 - thickness, y + size//2 + thickness)
            ], fill=glow_color)
            
            # Основная буква A
            draw.polygon([
                (x, y - size//2),                # Верхняя точка
                (x + size//3, y + size//2),      # Правая нижняя
                (x - size//3, y + size//2)       # Левая нижняя
            ], fill=color)
            
            # Поперечная линия A
            line_y = y + size//6
            draw.line([
                (x - size//4, line_y),
                (x + size//4, line_y)
            ], fill=self.colors['background'], width=thickness)
            
            # Внутренняя часть поперечной линии
            draw.line([
                (x - size//4 + thickness//2, line_y),
                (x + size//4 - thickness//2, line_y)
            ], fill=color, width=thickness//2)
        
        # Рисуем Z (больше и сзади)
        z_size = int(radius * 1.4)
        z_thickness = image_size // 25
        draw_z(center, center, z_size, z_thickness, z_color)
        
        # Рисуем A (немного меньше и спереди)
        a_size = int(radius * 1.2)
        a_thickness = image_size // 20
        draw_a(center, center, a_size, a_thickness, a_color)
        
        # Добавляем свечение вокруг логотипа
        self._add_glow_effect(img, glow_color)
        
        return img
    
    def _add_glow_effect(self, image, glow_color):
        """Добавление эффекта свечения вокруг логотипа"""
        # Создаем размытую копию для свечения
        from PIL import ImageFilter
        
        glow = image.copy()
        
        # Увеличиваем яркость для свечения
        glow_data = glow.load()
        for y in range(glow.size[1]):
            for x in range(glow.size[0]):
                r, g, b, a = glow_data[x, y]
                if a > 0:
                    # Увеличиваем альфа-канал для свечения
                    glow_data[x, y] = (r, g, b, min(255, a + 100))
        
        # Применяем размытие
        glow = glow.filter(ImageFilter.GaussianBlur(radius=10))
        
        # Накладываем свечение на оригинал
        image.paste(glow, (0, 0), glow)
        
        return image
    
    def generate_launcher_icon(self, size=512):
        """Генерация иконки для лаунчера"""
        print(f"Создание иконки лаунчера ({size}x{size})...")
        
        # Создаем градиентный фон
        bg = self._create_gradient(
            size, size,
            self.colors['gradient_start'],
            self.colors['gradient_end']
        )
        
        # Рисуем логотип
        logo = self._draw_za_logo(size, style='gradient')
        
        # Накладываем логотип на фон
        bg.paste(logo, (0, 0), logo)
        
        # Добавляем текст "ZA" внизу для больших иконок
        if size >= 256 and self.font_path:
            try:
                draw = ImageDraw.Draw(bg)
                font_size = size // 10
                font = ImageFont.truetype(self.font_path, font_size)
                
                text = "ZA"
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                
                text_x = (size - text_width) // 2
                text_y = size - text_height - size // 20
                
                # Тень текста
                draw.text((text_x+2, text_y+2), text, 
                         font=font, fill='#00000080')
                
                # Основной текст
                draw.text((text_x, text_y), text, 
                         font=font, fill=self.colors['text'])
            except:
                pass
        
        # Сохраняем
        icon_path = os.path.join(self.assets_dir, 'icon.png')
        bg.save(icon_path, 'PNG', optimize=True)
        print(f"✓ Иконка сохранена: {icon_path}")
        
        return icon_path
    
    def generate_presplash(self, width=1080, height=1920):
        """Генерация заставки (presplash)"""
        print(f"Создание заставки ({width}x{height})...")
        
        # Создаем темный градиентный фон
        bg = self._create_gradient(
            width, height,
            '#0a0a1a',  # Темно-синий
            '#1a1a2e'   # Темно-фиолетовый
        )
        
        # Размер логотипа для заставки
        logo_size = min(width, height) // 2
        
        # Рисуем логотип по центру
        logo = self._draw_za_logo(logo_size, style='primary')
        logo_x = (width - logo_size) // 2
        logo_y = (height - logo_size) // 2
        
        bg.paste(logo, (logo_x, logo_y), logo)
        
        # Добавляем текст
        if self.font_path:
            try:
                draw = ImageDraw.Draw(bg)
                
                # Название приложения
                title_font_size = width // 15
                title_font = ImageFont.truetype(self.font_path, title_font_size)
                
                title = "Zapret Android"
                title_bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = title_bbox[2] - title_bbox[0]
                title_x = (width - title_width) // 2
                title_y = logo_y + logo_size + height // 20
                
                # Тень заголовка
                draw.text((title_x+3, title_y+3), title, 
                         font=title_font, fill='#00000080')
                
                # Заголовок
                draw.text((title_x, title_y), title, 
                         font=title_font, fill=self.colors['primary'])
                
                # Подзаголовок
                subtitle_font_size = width // 30
                subtitle_font = ImageFont.truetype(self.font_path, subtitle_font_size)
                
                subtitle = "DPI Bypass System"
                subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                subtitle_x = (width - subtitle_width) // 2
                subtitle_y = title_y + title_font_size + height // 50
                
                draw.text((subtitle_x, subtitle_y), subtitle, 
                         font=subtitle_font, fill=self.colors['secondary'])
                
                # Версия внизу
                version_font_size = width // 40
                version_font = ImageFont.truetype(self.font_path, version_font_size)
                
                version = "v1.0.0"
                version_bbox = draw.textbbox((0, 0), version, font=version_font)
                version_width = version_bbox[2] - version_bbox[0]
                version_x = (width - version_width) // 2
                version_y = height - version_font_size - height // 20
                
                draw.text((version_x, version_y), version, 
                         font=version_font, fill=self.colors['text'] + '80')
                
            except Exception as e:
                print(f"⚠ Не удалось добавить текст: {e}")
        
        # Сохраняем
        presplash_path = os.path.join(self.assets_dir, 'presplash.png')
        bg.save(presplash_path, 'PNG', optimize=True)
        print(f"✓ Заставка сохранена: {presplash_path}")
        
        return presplash_path
    
    def generate_adaptive_icons(self):
        """Генерация адаптивных иконок для Android"""
        print("Создание адаптивных иконок...")
        
        # Размеры для адаптивных иконок
        sizes = {
            'mdpi': 48,
            'hdpi': 72,
            'xhdpi': 96,
            'xxhdpi': 144,
            'xxxhdpi': 192,
            'play_store': 512
        }
        
        # Создаем иконки для каждой плотности
        for density, size in sizes.items():
            if density == 'play_store':
                filepath = os.path.join(self.assets_dir, 'icon_play_store.png')
            else:
                dir_path = os.path.join(self.assets_dir, f'mipmap-{density}')
                os.makedirs(dir_path, exist_ok=True)
                filepath = os.path.join(dir_path, 'ic_launcher.png')
            
            # Генерируем иконку
            icon = self.generate_launcher_icon(size)
            
            # Переименовываем/копируем если нужно
            if icon != filepath:
                from shutil import copy2
                copy2(icon, filepath)
                print(f"  ✓ {density} ({size}x{size}): {filepath}")
        
        print("✓ Адаптивные иконки созданы")
    
    def generate_app_bar_icon(self, size=64):
        """Генерация иконки для AppBar/панели инструментов"""
        print(f"Создание иконки для AppBar ({size}x{size})...")
        
        # Простой минималистичный логотип
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Простой логотип ZA
        center = size // 2
        radius = size // 3
        
        # Буква Z
        z_points = [
            (center - radius, center - radius),
            (center + radius, center - radius),
            (center - radius, center + radius),
        ]
        draw.polygon(z_points, fill=self.colors['primary'] + 'cc')
        
        # Буква A поверх Z
        a_points = [
            (center, center - radius),
            (center + radius//2, center + radius),
            (center - radius//2, center + radius),
        ]
        draw.polygon(a_points, fill=self.colors['secondary'] + 'cc')
        
        # Поперечная линия A
        draw.line([
            (center - radius//3, center),
            (center + radius//3, center)
        ], fill='#000000', width=size//20)
        
        path = os.path.join(self.assets_dir, 'appbar_icon.png')
        img.save(path, 'PNG', optimize=True)
        print(f"✓ Иконка AppBar сохранена: {path}")
        
        return path
    
    def generate_tab_icons(self):
        """Генерация иконок для вкладок"""
        print("Создание иконок для вкладок...")
        
        icons = {
            'home': '🏠',
            'apps': '📱',
            'strategies': '⚙️',
            'settings': '🔧',
            'start': '▶️',
            'stop': '⏹️',
            'refresh': '🔄',
            'analyze': '🔍',
            'save': '💾',
            'export': '📤',
            'import': '📥',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'network': '📶',
            'shield': '🛡️',
            'lock': '🔒',
            'unlock': '🔓',
            'speed': '⚡',
            'ping': '📡'
        }
        
        size = 48
        for name, emoji in icons.items():
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Используем emoji как иконки
            if self.font_path:
                try:
                    # Пытаемся использовать шрифт с emoji
                    font = ImageFont.truetype(self.font_path, size - 10)
                    draw.text((size//2, size//2), emoji, 
                             font=font, fill=self.colors['primary'], 
                             anchor='mm')
                except:
                    # Fallback: рисуем простую геометрическую иконку
                    if name == 'home':
                        # Домик
                        draw.polygon([
                            (size//2, size//4),
                            (size//4, size//2),
                            (size*3//4, size//2)
                        ], fill=self.colors['primary'])
                        draw.rectangle([
                            (size//3, size//2),
                            (size*2//3, size*3//4)
                        ], fill=self.colors['secondary'])
                    elif name == 'apps':
                        # Квадраты приложений
                        square_size = size // 4
                        for i in range(2):
                            for j in range(2):
                                x = size//4 + i * square_size
                                y = size//4 + j * square_size
                                draw.rectangle([
                                    (x, y),
                                    (x + square_size - 2, y + square_size - 2)
                                ], fill=self.colors['primary'])
            
            path = os.path.join(self.assets_dir, f'icon_{name}.png')
            img.save(path, 'PNG', optimize=True)
        
        print(f"✓ Создано {len(icons)} иконок для вкладок")
    
    def generate_banner(self, width=1200, height=400):
        """Генерация баннера для README/документации"""
        print(f"Создание баннера ({width}x{height})...")
        
        # Градиентный фон
        bg = self._create_gradient(
            width, height,
            '#0a0a2a',
            '#1a1a3e'
        )
        
        draw = ImageDraw.Draw(bg)
        
        # Логотип слева
        logo_size = height * 2 // 3
        logo = self._draw_za_logo(logo_size, style='primary')
        bg.paste(logo, (height//6, height//6), logo)
        
        # Текст
        if self.font_path:
            try:
                # Заголовок
                title_font = ImageFont.truetype(self.font_path, height//5)
                title = "Zapret Android"
                title_x = logo_size + height//3
                title_y = height//4
                
                draw.text((title_x, title_y), title, 
                         font=title_font, fill=self.colors['primary'])
                
                # Подзаголовок
                subtitle_font = ImageFont.truetype(self.font_path, height//10)
                subtitle = "Advanced DPI Bypass System"
                subtitle_y = title_y + height//5
                
                draw.text((title_x, subtitle_y), subtitle, 
                         font=subtitle_font, fill=self.colors['secondary'])
                
                # Слоган
                tagline_font = ImageFont.truetype(self.font_path, height//15)
                tagline = "No Root Required • Auto Strategy Detection • Free & Open Source"
                tagline_y = subtitle_y + height//8
                
                draw.text((title_x, tagline_y), tagline, 
                         font=tagline_font, fill=self.colors['text'] + 'cc')
                
            except Exception as e:
                print(f"⚠ Не удалось добавить текст в баннер: {e}")
        
        # Сохраняем
        banner_path = os.path.join(self.assets_dir, 'banner.png')
        bg.save(banner_path, 'PNG', optimize=True)
        print(f"✓ Баннер сохранен: {banner_path}")
        
        return banner_path
    
    def generate_favicon(self):
        """Генерация favicon.ico"""
        print("Создание favicon.ico...")
        
        # Создаем несколько размеров для favicon
        sizes = [16, 32, 48, 64]
        images = []
        
        for size in sizes:
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            # Простой логотип для маленьких размеров
            center = size // 2
            radius = size // 3
            
            # Z
            draw.polygon([
                (center - radius, center - radius),
                (center + radius, center - radius),
                (center - radius, center + radius),
            ], fill=self.colors['primary'])
            
            # A поверх
            draw.polygon([
                (center, center - radius//2),
                (center + radius//2, center + radius//2),
                (center - radius//2, center + radius//2),
            ], fill=self.colors['secondary'])
            
            images.append(img)
        
        # Сохраняем как .ico
        favicon_path = os.path.join(self.assets_dir, 'favicon.ico')
        images[0].save(favicon_path, format='ICO', sizes=[(s, s) for s in sizes])
        print(f"✓ Favicon сохранен: {favicon_path}")
        
        return favicon_path
    
    def generate_readme_badges(self):
        """Генерация бейджей для README"""
        print("Создание бейджей для README...")
        
        badges = [
            {
                'text': 'Android',
                'color': '#3DDC84',
                'logo': 'android',
                'file': 'badge_android.png'
            },
            {
                'text': 'No Root Required',
                'color': '#4CAF50',
                'file': 'badge_no_root.png'
            },
            {
                'text': 'Open Source',
                'color': '#2196F3',
                'logo': 'github',
                'file': 'badge_opensource.png'
            },
            {
                'text': 'DPI Bypass',
                'color': '#FF9800',
                'file': 'badge_dpi.png'
            },
            {
                'text': 'Free',
                'color': '#9C27B0',
                'file': 'badge_free.png'
            }
        ]
        
        for badge in badges:
            width, height = 200, 40
            
            img = Image.new('RGB', (width, height), badge['color'])
            draw = ImageDraw.Draw(img)
            
            if self.font_path:
                try:
                    font = ImageFont.truetype(self.font_path, 20)
                    text = badge['text']
                    text_bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = text_bbox[2] - text_bbox[0]
                    text_height = text_bbox[3] - text_bbox[1]
                    
                    text_x = (width - text_width) // 2
                    text_y = (height - text_height) // 2
                    
                    draw.text((text_x, text_y), text, font=font, fill='#FFFFFF')
                except:
                    pass
            
            path = os.path.join(self.assets_dir, badge['file'])
            img.save(path, 'PNG', optimize=True)
        
        print(f"✓ Создано {len(badges)} бейджей")
    
    def generate_all(self):
        """Генерация всех изображений"""
        print("\n" + "="*60)
        print("  ГЕНЕРАЦИЯ ИКОНОК И ЛОГОТИПОВ ДЛЯ ZAPRET ANDROID")
        print("="*60)
        
        try:
            # Основные изображения
            self.generate_launcher_icon(512)
            self.generate_presplash(1080, 1920)
            self.generate_adaptive_icons()
            self.generate_app_bar_icon(64)
            self.generate_tab_icons()
            self.generate_banner(1200, 400)
            self.generate_favicon()
            self.generate_readme_badges()
            
            print("\n" + "="*60)
            print("  ВСЕ ИЗОБРАЖЕНИЯ УСПЕШНО СОЗДАНЫ!")
            print("="*60)
            print("\nСозданные файлы:")
            print(f"📍 Основная иконка: assets/icon.png")
            print(f"📍 Заставка: assets/presplash.png")
            print(f"📍 Favicon: assets/favicon.ico")
            print(f"📍 Баннер: assets/banner.png")
            print(f"📍 Иконки вкладок: assets/icon_*.png")
            print(f"📍 Бейджи: assets/badge_*.png")
            print(f"📍 Адаптивные иконки: assets/mipmap-*/")
            print("\n⚠ Теперь вы можете удалить файл icon_generator.py")
            
        except Exception as e:
            print(f"\n❌ Ошибка при генерации: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


def main():
    """Основная функция"""
    generator = IconGenerator()
    
    # Проверяем, существуют ли уже изображения
    existing_files = [
        'assets/icon.png',
        'assets/presplash.png'
    ]
    
    existing_count = sum(1 for f in existing_files if os.path.exists(f))
    
    if existing_count > 0:
        print(f"⚠ Найдено {existing_count} существующих изображений.")
        response = input("Перезаписать существующие файлы? (y/N): ")
        if response.lower() != 'y':
            print("Отменено.")
            return
    
    # Генерируем все изображения
    success = generator.generate_all()
    
    if success:
        print("\n🎉 Генерация завершена успешно!")
        print("Теперь вы можете запустить main.py для запуска приложения.")
    else:
        print("\n❌ Генерация завершилась с ошибками.")


if __name__ == '__main__':
    main()