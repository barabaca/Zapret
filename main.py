# -*- coding: utf-8 -*-
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
import threading
import json
import os
import subprocess
import time
from datetime import datetime

# Импорт модулей
from zapret_core import ZapretCore
from network_monitor import NetworkMonitor
from app_manager import AppManager

# Проверка наличия иконок
def check_assets():
    required_assets = [
        'assets/icon.png',
        'assets/presplash.png'
    ]
    
    missing = []
    for asset in required_assets:
        if not os.path.exists(asset):
            missing.append(asset)
    
    if missing:
        print("⚠ Внимание: отсутствуют необходимые файлы иконок!")
        print("Отсутствующие файлы:")
        for asset in missing:
            print(f"  - {asset}")
        
        response = input("\nСоздать иконки автоматически? (y/N): ")
        if response.lower() == 'y':
            try:
                # Пытаемся импортировать и запустить генератор
                import subprocess
                subprocess.run([sys.executable, "icon_generator.py"], check=True)
                print("✓ Иконки успешно созданы!")
            except Exception as e:
                print(f"❌ Ошибка создания иконок: {e}")
                print("Запустите вручную: python icon_generator.py")
                return False
    
    return True

# В функции main():
if __name__ == '__main__':
    if check_assets():
        ZapretApp().run()
        
class MainScreen(BoxLayout):
    status = StringProperty("Остановлено")
    is_running = BooleanProperty(False)
    ping = NumericProperty(0)
    download_speed = NumericProperty(0)
    upload_speed = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10
        
        # Установка фона
        with self.canvas.before:
            Color(rgba=get_color_from_hex('#1a1a2e'))
            self.rect = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        # Заголовок
        header = BoxLayout(size_hint_y=0.12)
        header.add_widget(Image(source='assets/logo.png', size_hint_x=0.2))
        
        title_label = Label(
            text='[b]Zapret Android[/b]\nDPI Bypass System',
            font_size=24,
            markup=True,
            color=get_color_from_hex('#ffffff'),
            halign='center'
        )
        header.add_widget(title_label)
        self.add_widget(header)
        
        # Основной контейнер с табами
        self.tabs = TabbedPanel(
            do_default_tab=False,
            tab_width=120,
            background_color=get_color_from_hex('#16213e'),
            border=[0, 0, 0, 0]
        )
        
        # Таб 1: Главная
        main_tab = TabbedPanelItem(text='Главная')
        main_content = self.create_main_tab()
        main_tab.add_widget(main_content)
        self.tabs.add_widget(main_tab)
        
        # Таб 2: Приложения
        apps_tab = TabbedPanelItem(text='Приложения')
        apps_content = self.create_apps_tab()
        apps_tab.add_widget(apps_content)
        self.tabs.add_widget(apps_tab)
        
        # Таб 3: Стратегии
        strategies_tab = TabbedPanelItem(text='Стратегии')
        strategies_content = self.create_strategies_tab()
        strategies_tab.add_widget(strategies_content)
        self.tabs.add_widget(strategies_tab)
        
        # Таб 4: Настройки
        settings_tab = TabbedPanelItem(text='Настройки')
        settings_content = self.create_settings_tab()
        settings_tab.add_widget(settings_content)
        self.tabs.add_widget(settings_tab)
        
        self.add_widget(self.tabs)
        
        # Инициализация ядра
        self.core = ZapretCore()
        self.monitor = NetworkMonitor()
        self.app_manager = AppManager()
        
        # Запуск мониторинга
        Clock.schedule_interval(self.update_stats, 1)
        
        # Загрузка конфигурации
        self.load_config()
    
    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
    
    def create_main_tab(self):
        """Создание главной вкладки"""
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Статус
        status_box = BoxLayout(size_hint_y=0.15)
        self.status_label = Label(
            text=f'Статус: {self.status}',
            font_size=20,
            color=get_color_from_hex('#00ff88'),
            bold=True
        )
        status_box.add_widget(self.status_label)
        layout.add_widget(status_box)
        
        # Кнопка старт/стоп
        self.start_button = Button(
            text='▶ ЗАПУСТИТЬ',
            font_size=22,
            background_color=get_color_from_hex('#00aa55'),
            size_hint_y=0.15,
            on_press=self.toggle_zapret
        )
        layout.add_widget(self.start_button)
        
        # Мониторинг сети
        monitor_box = GridLayout(cols=2, rows=2, size_hint_y=0.3, spacing=10)
        
        # Пинг
        ping_box = BoxLayout(orientation='vertical')
        ping_box.add_widget(Label(text='Пинг', font_size=16, color=get_color_from_hex('#ffffff')))
        self.ping_label = Label(text='0 ms', font_size=24, color=get_color_from_hex('#00ffff'))
        ping_box.add_widget(self.ping_label)
        monitor_box.add_widget(ping_box)
        
        # Загрузка
        download_box = BoxLayout(orientation='vertical')
        download_box.add_widget(Label(text='Скачивание', font_size=16, color=get_color_from_hex('#ffffff')))
        self.download_label = Label(text='0 Mbps', font_size=24, color=get_color_from_hex('#00ff00'))
        download_box.add_widget(self.download_label)
        monitor_box.add_widget(download_box)
        
        # Отправка
        upload_box = BoxLayout(orientation='vertical')
        upload_box.add_widget(Label(text='Отправка', font_size=16, color=get_color_from_hex('#ffffff')))
        self.upload_label = Label(text='0 Mbps', font_size=24, color=get_color_from_hex('#ff8800'))
        upload_box.add_widget(self.upload_label)
        monitor_box.add_widget(upload_box)
        
        # Активные соединения
        conn_box = BoxLayout(orientation='vertical')
        conn_box.add_widget(Label(text='Соединения', font_size=16, color=get_color_from_hex('#ffffff')))
        self.conn_label = Label(text='0', font_size=24, color=get_color_from_hex('#ff00ff'))
        conn_box.add_widget(self.conn_label)
        monitor_box.add_widget(conn_box)
        
        layout.add_widget(monitor_box)
        
        # Лог
        log_box = BoxLayout(orientation='vertical', size_hint_y=0.4)
        log_box.add_widget(Label(text='Лог событий:', font_size=16, color=get_color_from_hex('#ffffff')))
        
        self.log_scroll = ScrollView()
        self.log_text = Label(
            text='Система инициализирована\n',
            font_size=12,
            color=get_color_from_hex('#cccccc'),
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            halign='left',
            valign='top'
        )
        self.log_text.bind(texture_size=self.log_text.setter('size'))
        self.log_scroll.add_widget(self.log_text)
        log_box.add_widget(self.log_scroll)
        
        layout.add_widget(log_box)
        
        return layout
    
    def create_apps_tab(self):
        """Вкладка управления приложениями"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        layout.add_widget(Label(
            text='Управление приложениями',
            font_size=20,
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.1
        ))
        
        # Кнопки управления
        btn_box = BoxLayout(size_hint_y=0.1, spacing=10)
        
        scan_btn = Button(
            text='Сканировать приложения',
            background_color=get_color_from_hex('#2980b9'),
            on_press=self.scan_apps
        )
        btn_box.add_widget(scan_btn)
        
        auto_btn = Button(
            text='Автоопределение',
            background_color=get_color_from_hex('#27ae60'),
            on_press=self.auto_detect_apps
        )
        btn_box.add_widget(auto_btn)
        
        layout.add_widget(btn_box)
        
        # Список приложений с прокруткой
        self.apps_scroll = ScrollView(size_hint_y=0.7)
        self.apps_grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.apps_grid.bind(minimum_height=self.apps_grid.setter('height'))
        self.apps_scroll.add_widget(self.apps_grid)
        layout.add_widget(self.apps_scroll)
        
        # Кнопка подтверждения
        confirm_btn = Button(
            text='✓ ПРИМЕНИТЬ ВЫБОР',
            font_size=18,
            background_color=get_color_from_hex('#2ecc71'),
            size_hint_y=0.1,
            on_press=self.apply_app_selection
        )
        layout.add_widget(confirm_btn)
        
        return layout
    
    def create_strategies_tab(self):
        """Вкладка стратегий"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Описание стратегий из исходников
        strategies = {
            'FAKE_TLS_AUTO': 'Полная автоматическая маскировка под TLS',
            'FAKE_TLS_AUTO_ALT': 'Альтернативная TLS маскировка',
            'FAKE_TLS_AUTO_ALT2': 'TLS + badseq обман',
            'FAKE_TLS_AUTO_ALT3': 'TLS + multisplit обман',
            'SIMPLE_FAKE': 'Простая маскировка',
            'SIMPLE_FAKE_ALT': 'Простая маскировка с badseq',
            'ALT': 'Базовый обход',
            'ALT2': 'Multisplit обход',
            'ALT3': 'Fakedsplit обход',
            'ALT4': 'Fake+multisplit с badseq',
            'ALT5': 'Syndata (не рекомендуется)',
            'ALT6': 'Multisplit Google',
            'ALT7': 'Multisplit позиция 2',
            'ALT8': 'Fake с badseq=2',
            'ALT9': 'Hostfakesplit',
            'ALT10': 'Fake с TLS шаблонами'
        }
        
        layout.add_widget(Label(
            text='Выбор стратегии обхода',
            font_size=20,
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.1
        ))
        
        # Выбор стратегии
        strategy_box = BoxLayout(size_hint_y=0.15)
        strategy_box.add_widget(Label(text='Стратегия:', font_size=16, color=get_color_from_hex('#ffffff')))
        
        self.strategy_spinner = Spinner(
            text='AUTO',
            values=['AUTO'] + list(strategies.keys()),
            size_hint_x=0.7
        )
        strategy_box.add_widget(self.strategy_spinner)
        layout.add_widget(strategy_box)
        
        # Описание стратегии
        self.strategy_desc = Label(
            text='Автоматический выбор лучшей стратегии',
            font_size=14,
            color=get_color_from_hex('#aaaaaa'),
            size_hint_y=0.15,
            text_size=(Window.width - 20, None)
        )
        layout.add_widget(self.strategy_desc)
        
        # Привязка описания
        self.strategy_spinner.bind(text=self.update_strategy_desc)
        
        # Тестирование стратегий
        test_box = BoxLayout(size_hint_y=0.15, spacing=10)
        
        test_btn = Button(
            text='Тест стратегий',
            background_color=get_color_from_hex('#3498db'),
            on_press=self.test_strategies
        )
        test_box.add_widget(test_btn)
        
        auto_test_btn = Button(
            text='Автотест всех',
            background_color=get_color_from_hex('#9b59b6'),
            on_press=self.auto_test_all
        )
        test_box.add_widget(auto_test_btn)
        
        layout.add_widget(test_box)
        
        # Прогресс тестирования
        self.test_progress = ProgressBar(max=100, size_hint_y=0.05)
        layout.add_widget(self.test_progress)
        
        # Результаты теста
        self.test_results = Label(
            text='Результаты теста будут здесь',
            font_size=12,
            color=get_color_from_hex('#cccccc'),
            size_hint_y=0.4
        )
        layout.add_widget(self.test_results)
        
        return layout
    
    def create_settings_tab(self):
        """Вкладка настроек"""
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Настройки сети
        layout.add_widget(Label(
            text='Настройки сети',
            font_size=20,
            color=get_color_from_hex('#ffffff'),
            size_hint_y=0.1
        ))
        
        # DNS сервер
        dns_box = BoxLayout(size_hint_y=0.1)
        dns_box.add_widget(Label(text='DNS:', font_size=16, color=get_color_from_hex('#ffffff')))
        self.dns_input = TextInput(
            text='8.8.8.8',
            multiline=False,
            size_hint_x=0.7
        )
        dns_box.add_widget(self.dns_input)
        layout.add_widget(dns_box)
        
        # Порт прокси
        port_box = BoxLayout(size_hint_y=0.1)
        port_box.add_widget(Label(text='Порт:', font_size=16, color=get_color_from_hex('#ffffff')))
        self.port_input = TextInput(
            text='8080',
            multiline=False,
            size_hint_x=0.7
        )
        port_box.add_widget(self.port_input)
        layout.add_widget(port_box)
        
        # Автозапуск
        auto_box = BoxLayout(size_hint_y=0.1)
        auto_box.add_widget(Label(text='Автозапуск:', font_size=16, color=get_color_from_hex('#ffffff')))
        self.auto_switch = Switch(active=False)
        auto_box.add_widget(self.auto_switch)
        layout.add_widget(auto_box)
        
        # Game Filter (аналог из Windows)
        game_box = BoxLayout(size_hint_y=0.1)
        game_box.add_widget(Label(text='Game Filter:', font_size=16, color=get_color_from_hex('#ffffff')))
        self.game_switch = Switch(active=False)
        game_box.add_widget(self.game_switch)
        layout.add_widget(game_box)
        
        # Автообновление списков
        update_box = BoxLayout(size_hint_y=0.1)
        update_box.add_widget(Label(text='Автообновление:', font_size=16, color=get_color_from_hex('#ffffff')))
        self.update_switch = Switch(active=True)
        update_box.add_widget(self.update_switch)
        layout.add_widget(update_box)
        
        # Кнопки управления
        btn_box = BoxLayout(size_hint_y=0.2, spacing=10)
        
        update_lists_btn = Button(
            text='Обновить списки',
            background_color=get_color_from_hex('#16a085'),
            on_press=self.update_lists
        )
        btn_box.add_widget(update_lists_btn)
        
        clear_cache_btn = Button(
            text='Очистить кэш',
            background_color=get_color_from_hex('#e74c3c'),
            on_press=self.clear_cache
        )
        btn_box.add_widget(clear_cache_btn)
        
        layout.add_widget(btn_box)
        
        # Информация
        info_box = BoxLayout(orientation='vertical', size_hint_y=0.3)
        self.info_label = Label(
            text='Zapret Android v1.0\nБез root прав\nАвтоопределение стратегий',
            font_size=14,
            color=get_color_from_hex('#aaaaaa')
        )
        info_box.add_widget(self.info_label)
        layout.add_widget(info_box)
        
        return layout
    
    def toggle_zapret(self, instance):
        """Запуск/остановка системы"""
        if not self.is_running:
            self.start_zapret()
        else:
            self.stop_zapret()
    
    def start_zapret(self):
        """Запуск обхода"""
        self.log("Запуск Zapret...")
        self.status = "Запускается"
        self.start_button.text = '⏸ ОСТАНОВИТЬ'
        self.start_button.background_color = get_color_from_hex('#e74c3c')
        
        # Запуск в отдельном потоке
        thread = threading.Thread(target=self._start_zapret_thread)
        thread.daemon = True
        thread.start()
    
    def _start_zapret_thread(self):
        """Поток запуска"""
        try:
            # Получаем выбранную стратегию
            strategy = self.strategy_spinner.text
            
            # Получаем настройки
            dns = self.dns_input.text
            port = int(self.port_input.text)
            game_filter = self.game_switch.active
            
            # Запуск ядра
            success = self.core.start(
                strategy=strategy,
                dns_server=dns,
                proxy_port=port,
                game_filter=game_filter
            )
            
            if success:
                self.is_running = True
                self.status = "Работает"
                self.log("Zapret успешно запущен")
            else:
                self.status = "Ошибка"
                self.log("Ошибка запуска Zapret")
                
        except Exception as e:
            self.log(f"Ошибка: {str(e)}")
    
    def stop_zapret(self):
        """Остановка системы"""
        self.log("Остановка Zapret...")
        self.status = "Останавливается"
        
        try:
            self.core.stop()
            self.is_running = False
            self.status = "Остановлено"
            self.start_button.text = '▶ ЗАПУСТИТЬ'
            self.start_button.background_color = get_color_from_hex('#00aa55')
            self.log("Zapret остановлен")
        except Exception as e:
            self.log(f"Ошибка остановки: {str(e)}")
    
    def update_stats(self, dt):
        """Обновление статистики"""
        if self.is_running:
            stats = self.monitor.get_stats()
            self.ping = stats['ping']
            self.download_speed = stats['download']
            self.upload_speed = stats['upload']
            
            self.ping_label.text = f"{self.ping} ms"
            self.download_label.text = f"{self.download_speed:.1f} Mbps"
            self.upload_label.text = f"{self.upload_speed:.1f} Mbps"
            self.conn_label.text = f"{stats['connections']}"
    
    def scan_apps(self, instance):
        """Сканирование приложений"""
        self.log("Сканирование приложений...")
        apps = self.app_manager.get_installed_apps()
        
        # Очищаем список
        self.apps_grid.clear_widgets()
        
        # Загружаем сохранённые настройки
        try:
            with open('app_profiles.json', 'r') as f:
                saved = json.load(f)
        except:
            saved = {}
        
        # Добавляем приложения
        for app in apps[:20]:  # Показываем первые 20
            row = BoxLayout(size_hint_y=None, height=60)
            
            # Чекбокс (используем Switch)
            switch = Switch(active=app['package'] in saved)
            switch.package = app['package']
            switch.bind(active=self.on_app_toggle)
            row.add_widget(switch)
            
            # Иконка и название
            app_box = BoxLayout(orientation='vertical', size_hint_x=0.6)
            app_box.add_widget(Label(
                text=app['name'],
                font_size=14,
                color=get_color_from_hex('#ffffff'),
                size_hint_y=0.6
            ))
            app_box.add_widget(Label(
                text=app['package'],
                font_size=10,
                color=get_color_from_hex('#aaaaaa'),
                size_hint_y=0.4
            ))
            row.add_widget(app_box)
            
            # Кнопка анализа
            analyze_btn = Button(
                text='Анализ',
                size_hint_x=0.2,
                font_size=12,
                on_press=self.analyze_app
            )
            analyze_btn.package = app['package']
            row.add_widget(analyze_btn)
            
            self.apps_grid.add_widget(row)
        
        self.log(f"Найдено {len(apps)} приложений")
    
    def auto_detect_apps(self, instance):
        """Автоопределение стратегий для всех приложений"""
        self.log("Автоопределение стратегий...")
        
        # В отдельном потоке
        thread = threading.Thread(target=self._auto_detect_thread)
        thread.daemon = True
        thread.start()
    
    def _auto_detect_thread(self):
        """Поток автоопределения"""
        try:
            apps = self.app_manager.get_installed_apps()
            for app in apps[:10]:  # Первые 10
                strategy = self.core.auto_detect_strategy(app['package'])
                self.app_manager.save_app_profile(app['package'], strategy)
                self.log(f"{app['name']} -> {strategy}")
            
            self.log("Автоопределение завершено")
        except Exception as e:
            self.log(f"Ошибка автоопределения: {str(e)}")
    
    def apply_app_selection(self, instance):
        """Применение выбора приложений"""
        self.log("Применение настроек приложений...")
        # Здесь будет логика применения
        self.log("Настройки применены")
    
    def test_strategies(self, instance):
        """Тестирование стратегий"""
        self.log("Тестирование стратегий...")
        
        thread = threading.Thread(target=self._test_strategies_thread)
        thread.daemon = True
        thread.start()
    
    def _test_strategies_thread(self):
        """Поток тестирования стратегий"""
        strategies = ['FAKE_TLS_AUTO', 'ALT', 'SIMPLE_FAKE', 'ALT9']
        results = []
        
        for i, strategy in enumerate(strategies):
            # Обновляем прогресс
            progress = (i + 1) / len(strategies) * 100
            Clock.schedule_once(lambda dt, p=progress: self.update_progress(p), 0)
            
            # Тестируем стратегию
            success = self.core.test_strategy(strategy)
            results.append(f"{strategy}: {'✓' if success else '✗'}")
            
            self.log(f"Тест {strategy}: {'успех' if success else 'провал'}")
        
        # Показываем результаты
        Clock.schedule_once(lambda dt, r=results: self.show_test_results(r), 0)
    
    def update_progress(self, value):
        """Обновление прогресса"""
        self.test_progress.value = value
    
    def show_test_results(self, results):
        """Показать результаты теста"""
        self.test_results.text = '\n'.join(results)
    
    def update_strategy_desc(self, spinner, text):
        """Обновление описания стратегии"""
        descriptions = {
            'AUTO': 'Автоматический выбор лучшей стратегии',
            'FAKE_TLS_AUTO': 'Полная автоматическая маскировка под TLS',
            'FAKE_TLS_AUTO_ALT': 'Альтернативная TLS маскировка',
            'ALT9': 'Hostfakesplit - подмена хоста',
            'SIMPLE_FAKE': 'Простая маскировка под HTTPS'
        }
        self.strategy_desc.text = descriptions.get(text, 'Описание стратегии')
    
    def update_lists(self, instance):
        """Обновление списков доменов и IP"""
        self.log("Обновление списков...")
        
        thread = threading.Thread(target=self._update_lists_thread)
        thread.daemon = True
        thread.start()
    
    def _update_lists_thread(self):
        """Поток обновления списков"""
        try:
            self.core.update_lists()
            self.log("Списки успешно обновлены")
        except Exception as e:
            self.log(f"Ошибка обновления: {str(e)}")
    
    def clear_cache(self, instance):
        """Очистка кэша"""
        self.log("Очистка кэша...")
        try:
            self.app_manager.clear_cache()
            self.log("Кэш очищен")
        except Exception as e:
            self.log(f"Ошибка очистки: {str(e)}")
    
    def log(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Обновляем в основном потоке
        Clock.schedule_once(lambda dt: self._update_log(log_entry), 0)
    
    def _update_log(self, message):
        """Обновление лога (вызывается в основном потоке)"""
        self.log_text.text += message
        # Прокручиваем вниз
        self.log_scroll.scroll_y = 0
    
    def load_config(self):
        """Загрузка конфигурации"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
                self.dns_input.text = config.get('dns', '8.8.8.8')
                self.port_input.text = str(config.get('port', 8080))
                self.auto_switch.active = config.get('autostart', False)
                self.game_switch.active = config.get('game_filter', False)
                self.strategy_spinner.text = config.get('strategy', 'AUTO')
        except:
            pass
    
    def save_config(self):
        """Сохранение конфигурации"""
        config = {
            'dns': self.dns_input.text,
            'port': int(self.port_input.text),
            'autostart': self.auto_switch.active,
            'game_filter': self.game_switch.active,
            'strategy': self.strategy_spinner.text
        }
        
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
    
    def on_stop(self):
        """При закрытии приложения"""
        self.save_config()
        if self.is_running:
            self.stop_zapret()

class ZapretApp(App):
    def build(self):
        self.icon = 'assets/icon.png'
        self.title = 'Zapret Android'
        return MainScreen()

if __name__ == '__main__':
    ZapretApp().run()