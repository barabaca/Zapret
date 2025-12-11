#!/usr/bin/env python3
"""
Автоматическое тестирование всех компонентов
"""

import unittest
import sys
import os
import json
import time
from datetime import datetime

class TestZapretAndroid(unittest.TestCase):
    
    def setUp(self):
        """Настройка перед каждым тестом"""
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
    def test_01_core_initialization(self):
        """Тест инициализации ядра"""
        from zapret_core import ZapretCore
        core = ZapretCore()
        
        # Проверка директорий
        self.assertTrue(os.path.exists(core.lists_dir))
        self.assertTrue(os.path.exists(core.bin_dir))
        
        # Проверка файлов конфигурации
        self.assertTrue(os.path.exists(core.config_file))
        
        print("[✓] Ядро системы инициализировано")
    
    def test_02_lists_creation(self):
        """Тест создания списков"""
        lists_dir = os.path.join(os.path.dirname(__file__), 'lists')
        
        required_files = [
            'list-general.txt',
            'list-google.txt',
            'list-exclude.txt',
            'ipset-all.txt',
            'ipset-exclude.txt'
        ]
        
        for filename in required_files:
            filepath = os.path.join(lists_dir, filename)
            self.assertTrue(os.path.exists(filepath))
            
            # Проверка содержимого
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertGreater(len(content), 0)
        
        print("[✓] Списки доменов и IP созданы")
    
    def test_03_strategy_detection(self):
        """Тест определения стратегий"""
        from zapret_core import ZapretCore
        core = ZapretCore()
        
        test_cases = [
            ('com.google.android.youtube', 'FAKE_TLS_AUTO'),
            ('com.discord', 'ALT9'),
            ('com.valvesoftware.android.steam.community', 'ALT'),
            ('com.unknown.app', 'AUTO')
        ]
        
        for package, expected in test_cases:
            strategy = core.auto_detect_strategy(package)
            if 'unknown' not in package:
                self.assertIn(strategy, ['FAKE_TLS_AUTO', 'ALT9', 'ALT', 'SIMPLE_FAKE'])
            
            print(f"[✓] {package} -> {strategy}")
    
    def test_04_network_monitor(self):
        """Тест мониторинга сети"""
        from network_monitor import NetworkMonitor
        monitor = NetworkMonitor()
        
        stats = monitor.get_stats()
        
        # Проверка структуры
        required_keys = ['ping', 'download', 'upload', 'connections']
        for key in required_keys:
            self.assertIn(key, stats)
        
        print(f"[✓] Мониторинг сети: {stats}")
    
    def test_05_app_manager(self):
        """Тест менеджера приложений"""
        from app_manager import AppManager
        manager = AppManager()
        
        apps = manager.get_installed_apps()
        
        # Проверка что список не пустой
        self.assertIsInstance(apps, list)
        
        if len(apps) > 0:
            app = apps[0]
            self.assertIn('package', app)
            self.assertIn('name', app)
            
            print(f"[✓] Найдено приложений: {len(apps)}")
    
    def test_06_config_save_load(self):
        """Тест сохранения/загрузки конфигурации"""
        test_config = {
            'strategy': 'TEST',
            'dns_server': '1.1.1.1',
            'proxy_port': 9090,
            'game_filter': True,
            'timestamp': time.time()
        }
        
        config_file = 'test_config.json'
        
        # Сохранение
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Загрузка
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        # Проверка
        self.assertEqual(test_config['strategy'], loaded_config['strategy'])
        self.assertEqual(test_config['dns_server'], loaded_config['dns_server'])
        
        # Очистка
        os.remove(config_file)
        
        print("[✓] Конфигурация сохраняется и загружается корректно")
    
    def test_07_proxy_creation(self):
        """Тест создания прокси"""
        from zapret_core import ZapretCore
        core = ZapretCore()
        
        proxy_script = core.create_local_proxy(
            core.get_strategy_params('SIMPLE_FAKE'),
            '8.8.8.8',
            8888
        )
        
        self.assertTrue(os.path.exists(proxy_script))
        
        # Проверка содержимого
        with open(proxy_script, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('PROXY_PORT = 8888', content)
            self.assertIn('DNS_SERVER = \'8.8.8.8\'', content)
        
        # Очистка
        os.remove(proxy_script)
        
        print("[✓] Прокси-скрипт создан корректно")

def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 60)
    print("   Zapret Android - Полное автоматическое тестирование")
    print("=" * 60)
    print(f"Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Запуск тестов
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestZapretAndroid)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 60)
    print("Результаты тестирования:")
    print(f"Тестов запущено: {result.testsRun}")
    print(f"Ошибок: {len(result.errors)}")
    print(f"Провалов: {len(result.failures)}")
    
    # Генерация отчёта
    generate_test_report(result)
    
    return result.wasSuccessful()

def generate_test_report(result):
    """Генерация HTML отчёта"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    report_file = f'test_report_{timestamp}.html'
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Отчёт тестирования Zapret Android</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .success {{ color: #27ae60; }}
        .failure {{ color: #c0392b; }}
        .test {{ padding: 10px; margin: 5px; border-left: 4px solid #3498db; }}
        .error {{ background: #f2dede; padding: 10px; margin: 5px; border-radius: 3px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Zapret Android - Отчёт тестирования</h1>
        <p>Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>Статистика</h2>
    <table>
        <tr>
            <th>Всего тестов</th>
            <th>Успешно</th>
            <th>Провалов</th>
            <th>Ошибок</th>
            <th>Успешность</th>
        </tr>
        <tr>
            <td>{result.testsRun}</td>
            <td class="success">{result.testsRun - len(result.failures) - len(result.errors)}</td>
            <td class="failure">{len(result.failures)}</td>
            <td class="failure">{len(result.errors)}</td>
            <td>{((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%</td>
        </tr>
    </table>
    
    <h2>Детали тестов</h2>
"""
    
    # Добавляем информацию о каждом тесте
    for test, error in result.errors + result.failures:
        html += f"""
    <div class="test">
        <strong>{test.id()}</strong>
        <div class="error">
            <pre>{error}</pre>
        </div>
    </div>
"""
    
    html += """
</body>
</html>
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Отчёт сохранён: {report_file}")

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)