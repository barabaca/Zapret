#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import time
import sqlite3
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import threading

class StrategyType(Enum):
    """Типы стратегий обхода"""
    FAKE_TLS_AUTO = "FAKE_TLS_AUTO"
    FAKE_TLS_AUTO_ALT = "FAKE_TLS_AUTO_ALT"
    FAKE_TLS_AUTO_ALT2 = "FAKE_TLS_AUTO_ALT2"
    FAKE_TLS_AUTO_ALT3 = "FAKE_TLS_AUTO_ALT3"
    SIMPLE_FAKE = "SIMPLE_FAKE"
    SIMPLE_FAKE_ALT = "SIMPLE_FAKE_ALT"
    ALT = "ALT"
    ALT2 = "ALT2"
    ALT3 = "ALT3"
    ALT4 = "ALT4"
    ALT5 = "ALT5"
    ALT6 = "ALT6"
    ALT7 = "ALT7"
    ALT8 = "ALT8"
    ALT9 = "ALT9"
    ALT10 = "ALT10"
    AUTO = "AUTO"

class StrategyManager:
    """Управление стратегиями обхода DPI"""
    
    def __init__(self, db_path: str = "strategies.db"):
        """Инициализация менеджера стратегий"""
        self.db_path = db_path
        self.strategies = {}
        self.app_strategy_map = {}
        self.lock = threading.Lock()
        
        # Загрузка стратегий из Windows .bat файлов
        self._load_windows_strategies()
        
        # Инициализация базы данных
        self._init_database()
        
        # Загрузка сохранённых стратегий
        self.load_strategies()
    
    def _load_windows_strategies(self):
        """Загрузка стратегий из Windows .bat файлов"""
        # Эти стратегии адаптированы из предоставленных .bat файлов
        self.strategies = {
            StrategyType.FAKE_TLS_AUTO: {
                'name': 'FAKE TLS AUTO',
                'description': 'Полная автоматическая маскировка под TLS',
                'params': {
                    'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                    'udp_ports': '443,19294-19344,50000-50100',
                    'filters': [
                        {'type': 'udp', 'port': 443, 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 11},
                        {'type': 'udp', 'port': '19294-19344,50000-50100', 'l7': 'discord,stun', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'tcp', 'port': '2053,2083,2087,2096,8443', 'domains': 'discord.media', 'dpi': 'fake,multidisorder', 'repeats': 11},
                        {'type': 'tcp', 'port': 443, 'hostlist': 'list-google.txt', 'ip_id': 'zero', 'dpi': 'fake,multidisorder', 'repeats': 11},
                        {'type': 'tcp', 'port': '80,443', 'hostlist': 'list-general.txt', 'dpi': 'fake,multidisorder', 'repeats': 11}
                    ],
                    'effectiveness': 95,
                    'latency_impact': 'medium',
                    'bandwidth_impact': 'low'
                }
            },
            StrategyType.ALT9: {
                'name': 'ALT9 (Hostfakesplit)',
                'description': 'Подмена хоста с разделением пакетов',
                'params': {
                    'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                    'udp_ports': '443,19294-19344,50000-50100',
                    'filters': [
                        {'type': 'udp', 'port': 443, 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'udp', 'port': '19294-19344,50000-50100', 'l7': 'discord,stun', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'tcp', 'port': '2053,2083,2087,2096,8443', 'domains': 'discord.media', 'dpi': 'hostfakesplit', 'repeats': 4, 'mod': 'host=ozon.ru'},
                        {'type': 'tcp', 'port': 443, 'hostlist': 'list-google.txt', 'ip_id': 'zero', 'dpi': 'hostfakesplit', 'repeats': 4, 'mod': 'host=www.google.com'},
                        {'type': 'tcp', 'port': '80,443', 'hostlist': 'list-general.txt', 'dpi': 'hostfakesplit', 'repeats': 4, 'mod': 'host=ozon.ru'}
                    ],
                    'effectiveness': 90,
                    'latency_impact': 'low',
                    'bandwidth_impact': 'medium'
                }
            },
            StrategyType.SIMPLE_FAKE: {
                'name': 'SIMPLE FAKE',
                'description': 'Простая маскировка трафика',
                'params': {
                    'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                    'udp_ports': '443,19294-19344,50000-50100',
                    'filters': [
                        {'type': 'udp', 'port': 443, 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'udp', 'port': '19294-19344,50000-50100', 'l7': 'discord,stun', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'tcp', 'port': '2053,2083,2087,2096,8443', 'domains': 'discord.media', 'dpi': 'fake', 'repeats': 6, 'fooling': 'ts'},
                        {'type': 'tcp', 'port': 443, 'hostlist': 'list-google.txt', 'ip_id': 'zero', 'dpi': 'fake', 'repeats': 6, 'fooling': 'ts'},
                        {'type': 'tcp', 'port': '80,443', 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 6, 'fooling': 'ts'}
                    ],
                    'effectiveness': 85,
                    'latency_impact': 'very low',
                    'bandwidth_impact': 'very low'
                }
            },
            StrategyType.ALT: {
                'name': 'ALT (базовый)',
                'description': 'Базовый обход с fakedsplit',
                'params': {
                    'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                    'udp_ports': '443,19294-19344,50000-50100',
                    'filters': [
                        {'type': 'udp', 'port': 443, 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'udp', 'port': '19294-19344,50000-50100', 'l7': 'discord,stun', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'tcp', 'port': '2053,2083,2087,2096,8443', 'domains': 'discord.media', 'dpi': 'fake,fakedsplit', 'repeats': 6, 'fooling': 'ts'},
                        {'type': 'tcp', 'port': 443, 'hostlist': 'list-google.txt', 'ip_id': 'zero', 'dpi': 'fake,fakedsplit', 'repeats': 6, 'fooling': 'ts'},
                        {'type': 'tcp', 'port': '80,443', 'hostlist': 'list-general.txt', 'dpi': 'fake,fakedsplit', 'repeats': 6, 'fooling': 'ts'}
                    ],
                    'effectiveness': 88,
                    'latency_impact': 'low',
                    'bandwidth_impact': 'low'
                }
            },
            StrategyType.AUTO: {
                'name': 'AUTO',
                'description': 'Автоматический выбор лучшей стратегии',
                'params': {
                    'tcp_ports': '80,443',
                    'udp_ports': '443',
                    'filters': [
                        {'type': 'tcp', 'port': '80,443', 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 6},
                        {'type': 'udp', 'port': 443, 'hostlist': 'list-general.txt', 'dpi': 'fake', 'repeats': 6}
                    ],
                    'effectiveness': 0,  # Определяется динамически
                    'latency_impact': 'variable',
                    'bandwidth_impact': 'variable'
                }
            }
        }
    
    def _init_database(self):
        """Инициализация базы данных стратегий"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица стратегий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    type TEXT,
                    description TEXT,
                    params TEXT,
                    effectiveness REAL DEFAULT 0,
                    latency_impact TEXT,
                    bandwidth_impact TEXT,
                    last_used TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    total_usage INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица привязки стратегий к приложениям
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    app_package TEXT,
                    strategy_type TEXT,
                    priority INTEGER DEFAULT 50,
                    enabled INTEGER DEFAULT 1,
                    last_success TIMESTAMP,
                    success_rate REAL DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(app_package, strategy_type)
                )
            ''')
            
            # Таблица результатов тестирования
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_tests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_type TEXT,
                    test_target TEXT,
                    result INTEGER,  -- 1 = success, 0 = fail
                    ping_ms INTEGER,
                    download_mbps REAL,
                    upload_mbps REAL,
                    test_duration INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица обновлений стратегий
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_updates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_type TEXT,
                    old_params TEXT,
                    new_params TEXT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            # Заполняем базу данных начальными стратегиями
            self._populate_initial_strategies()
    
    def _populate_initial_strategies(self):
        """Заполнение базы данных начальными стратегиями"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for strategy_type, strategy_data in self.strategies.items():
                cursor.execute('''
                    INSERT OR IGNORE INTO strategies 
                    (name, type, description, params, effectiveness, latency_impact, bandwidth_impact)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_data['name'],
                    strategy_type.value,
                    strategy_data['description'],
                    json.dumps(strategy_data['params']),
                    strategy_data['params']['effectiveness'],
                    strategy_data['params']['latency_impact'],
                    strategy_data['params']['bandwidth_impact']
                ))
            
            conn.commit()
            conn.close()
    
    def load_strategies(self):
        """Загрузка стратегий из базы данных"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM strategies')
            rows = cursor.fetchall()
            
            for row in rows:
                strategy_id, name, strategy_type, description, params_json, effectiveness, \
                latency_impact, bandwidth_impact, last_used, success_count, \
                fail_count, total_usage, created_at = row
                
                try:
                    strategy_type_enum = StrategyType(strategy_type)
                    params = json.loads(params_json)
                    
                    self.strategies[strategy_type_enum] = {
                        'id': strategy_id,
                        'name': name,
                        'description': description,
                        'params': params,
                        'effectiveness': effectiveness,
                        'latency_impact': latency_impact,
                        'bandwidth_impact': bandwidth_impact,
                        'last_used': last_used,
                        'success_count': success_count,
                        'fail_count': fail_count,
                        'total_usage': total_usage,
                        'created_at': created_at
                    }
                except:
                    continue
            
            conn.close()
    
    def get_strategy(self, strategy_type: StrategyType) -> Optional[Dict[str, Any]]:
        """Получение стратегии по типу"""
        return self.strategies.get(strategy_type)
    
    def get_all_strategies(self) -> Dict[StrategyType, Dict[str, Any]]:
        """Получение всех стратегий"""
        return self.strategies.copy()
    
    def get_strategy_for_app(self, app_package: str, 
                            traffic_pattern: Optional[Dict[str, Any]] = None) -> StrategyType:
        """Получение оптимальной стратегии для приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем, есть ли сохранённая стратегия для этого приложения
            cursor.execute('''
                SELECT strategy_type, success_rate 
                FROM app_strategies 
                WHERE app_package = ? AND enabled = 1
                ORDER BY priority DESC, success_rate DESC
                LIMIT 1
            ''', (app_package,))
            
            row = cursor.fetchone()
            
            if row:
                strategy_type_str, success_rate = row
                
                # Если успешность выше 70%, используем сохранённую стратегию
                if success_rate >= 70:
                    try:
                        return StrategyType(strategy_type_str)
                    except:
                        pass
            
            conn.close()
        
        # Если нет сохранённой стратегии, определяем оптимальную
        return self._determine_optimal_strategy(app_package, traffic_pattern)
    
    def _determine_optimal_strategy(self, app_package: str, 
                                   traffic_pattern: Optional[Dict[str, Any]]) -> StrategyType:
        """Определение оптимальной стратегии на основе анализа"""
        
        # База знаний приложений и стратегий
        app_strategy_knowledge = {
            'com.google.android.youtube': StrategyType.FAKE_TLS_AUTO,
            'com.discord': StrategyType.ALT9,
            'com.valvesoftware.android.steam.community': StrategyType.ALT,
            'com.spotify.music': StrategyType.SIMPLE_FAKE,
            'com.netflix.mediaclient': StrategyType.FAKE_TLS_AUTO_ALT,
            'org.telegram.messenger': StrategyType.ALT4,
            'com.whatsapp': StrategyType.SIMPLE_FAKE,
            'com.instagram.android': StrategyType.ALT4,
            'com.facebook.katana': StrategyType.ALT4,
            'com.twitter.android': StrategyType.FAKE_TLS_AUTO,
            'com.twitch.tv.app': StrategyType.FAKE_TLS_AUTO_ALT3,
            'com.reddit.frontpage': StrategyType.ALT2
        }
        
        # Проверяем базу знаний
        if app_package in app_strategy_knowledge:
            return app_strategy_knowledge[app_package]
        
        # Анализируем имя пакета
        app_name_lower = app_package.lower()
        
        if any(keyword in app_name_lower for keyword in ['game', 'play', 'gaming']):
            # Для игр используем стратегии с низкой задержкой
            return StrategyType.ALT
        elif any(keyword in app_name_lower for keyword in ['video', 'stream', 'tv', 'movie']):
            # Для видео используем стратегии с хорошей пропускной способностью
            return StrategyType.FAKE_TLS_AUTO
        elif any(keyword in app_name_lower for keyword in ['music', 'audio', 'radio']):
            # Для аудио используем простые стратегии
            return StrategyType.SIMPLE_FAKE
        elif any(keyword in app_name_lower for keyword in ['browser', 'web', 'search']):
            # Для браузеров используем универсальные стратегии
            return StrategyType.ALT9
        elif any(keyword in app_name_lower for keyword in ['chat', 'message', 'social']):
            # Для чатов используем стабильные стратегии
            return StrategyType.ALT4
        else:
            # По умолчанию - автоопределение
            return StrategyType.AUTO
    
    def save_app_strategy(self, app_package: str, strategy_type: StrategyType,
                         success: bool = True):
        """Сохранение стратегии для приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем текущую статистику
            cursor.execute('''
                SELECT success_rate, usage_count 
                FROM app_strategies 
                WHERE app_package = ? AND strategy_type = ?
            ''', (app_package, strategy_type.value))
            
            row = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if row:
                current_success_rate, usage_count = row
                
                # Обновляем статистику
                new_usage_count = usage_count + 1
                
                if success:
                    # Увеличиваем успешность
                    new_success_count = int(current_success_rate * usage_count / 100) + 1
                    new_success_rate = (new_success_count / new_usage_count) * 100
                    last_success = now
                else:
                    # Уменьшаем успешность
                    new_success_count = int(current_success_rate * usage_count / 100)
                    new_success_rate = (new_success_count / new_usage_count) * 100
                    last_success = None
                
                cursor.execute('''
                    UPDATE app_strategies 
                    SET success_rate = ?, usage_count = ?, last_success = ?
                    WHERE app_package = ? AND strategy_type = ?
                ''', (new_success_rate, new_usage_count, last_success, 
                      app_package, strategy_type.value))
            
            else:
                # Создаём новую запись
                success_rate = 100 if success else 0
                last_success = now if success else None
                
                cursor.execute('''
                    INSERT INTO app_strategies 
                    (app_package, strategy_type, success_rate, usage_count, last_success)
                    VALUES (?, ?, ?, ?, ?)
                ''', (app_package, strategy_type.value, success_rate, 1, last_success))
            
            # Также обновляем общую статистику стратегии
            self._update_strategy_stats(strategy_type, success)
            
            conn.commit()
            conn.close()
    
    def _update_strategy_stats(self, strategy_type: StrategyType, success: bool):
        """Обновление общей статистики стратегии"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT success_count, fail_count, total_usage, effectiveness
                FROM strategies 
                WHERE type = ?
            ''', (strategy_type.value,))
            
            row = cursor.fetchone()
            
            if row:
                success_count, fail_count, total_usage, effectiveness = row
                
                # Обновляем счётчики
                if success:
                    new_success_count = success_count + 1
                    new_fail_count = fail_count
                else:
                    new_success_count = success_count
                    new_fail_count = fail_count + 1
                
                new_total_usage = total_usage + 1
                
                # Пересчитываем эффективность
                if new_total_usage > 0:
                    new_effectiveness = (new_success_count / new_total_usage) * 100
                else:
                    new_effectiveness = 0
                
                cursor.execute('''
                    UPDATE strategies 
                    SET success_count = ?, fail_count = ?, total_usage = ?, 
                        effectiveness = ?, last_used = ?
                    WHERE type = ?
                ''', (new_success_count, new_fail_count, new_total_usage,
                      new_effectiveness, datetime.now().isoformat(), strategy_type.value))
            
            conn.commit()
            conn.close()
    
    def test_strategy(self, strategy_type: StrategyType, 
                     test_target: str = "https://www.google.com") -> Dict[str, Any]:
        """Тестирование стратегии"""
        import requests
        import time
        
        test_results = {
            'strategy': strategy_type.value,
            'target': test_target,
            'success': False,
            'ping_ms': 0,
            'download_mbps': 0,
            'upload_mbps': 0,
            'duration': 0
        }
        
        try:
            start_time = time.time()
            
            # Пытаемся подключиться через стратегию
            # В реальной реализации здесь был бы вызов DPI обхода
            
            # Упрощённая проверка
            response = requests.get(test_target, timeout=10)
            
            end_time = time.time()
            duration = end_time - start_time
            
            if response.status_code == 200:
                test_results['success'] = True
                test_results['ping_ms'] = int(duration * 1000)
                
                # Оцениваем скорость (упрощённо)
                content_length = len(response.content)
                test_results['download_mbps'] = (content_length * 8 / duration) / 1_000_000
                test_results['upload_mbps'] = test_results['download_mbps'] * 0.3
                
                test_results['duration'] = int(duration)
                
                # Сохраняем результаты теста
                self._save_test_result(strategy_type, test_target, True, 
                                     test_results['ping_ms'],
                                     test_results['download_mbps'],
                                     test_results['upload_mbps'],
                                     test_results['duration'])
            
            else:
                test_results['success'] = False
                self._save_test_result(strategy_type, test_target, False, 0, 0, 0, 0)
        
        except Exception as e:
            test_results['success'] = False
            test_results['error'] = str(e)
            self._save_test_result(strategy_type, test_target, False, 0, 0, 0, 0)
        
        return test_results
    
    def _save_test_result(self, strategy_type: StrategyType, test_target: str,
                         success: bool, ping_ms: int, download_mbps: float,
                         upload_mbps: float, duration: int):
        """Сохранение результата тестирования"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO strategy_tests 
                (strategy_type, test_target, result, ping_ms, download_mbps, upload_mbps, test_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (strategy_type.value, test_target, 1 if success else 0,
                  ping_ms, download_mbps, upload_mbps, duration))
            
            conn.commit()
            conn.close()
    
    def get_strategy_stats(self, strategy_type: StrategyType) -> Dict[str, Any]:
        """Получение статистики стратегии"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    s.*,
                    COUNT(DISTINCT ast.app_package) as app_count,
                    AVG(ast.success_rate) as avg_app_success
                FROM strategies s
                LEFT JOIN app_strategies ast ON s.type = ast.strategy_type
                WHERE s.type = ?
                GROUP BY s.id
            ''', (strategy_type.value,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                stats = dict(zip(columns, row))
                
                # Дополнительная статистика из тестов
                stats['recent_tests'] = self._get_recent_tests(strategy_type, 5)
                stats['performance_trend'] = self._calculate_performance_trend(strategy_type)
                
                return stats
            else:
                return {}
    
    def _get_recent_tests(self, strategy_type: StrategyType, limit: int = 5) -> List[Dict[str, Any]]:
        """Получение последних тестов стратегии"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM strategy_tests 
                WHERE strategy_type = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (strategy_type.value, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []
    
    def _calculate_performance_trend(self, strategy_type: StrategyType) -> str:
        """Расчёт тренда производительности"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT result, timestamp 
                FROM strategy_tests 
                WHERE strategy_type = ? 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''', (strategy_type.value,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if len(rows) < 5:
                return "insufficient_data"
            
            # Анализируем последние 5 тестов
            recent_results = [row[0] for row in rows[:5]]
            success_rate = sum(recent_results) / len(recent_results) * 100
            
            if success_rate >= 90:
                return "excellent"
            elif success_rate >= 70:
                return "good"
            elif success_rate >= 50:
                return "fair"
            else:
                return "poor"
    
    def get_recommended_strategy(self, context: Dict[str, Any] = None) -> StrategyType:
        """Получение рекомендованной стратегии на основе контекста"""
        if not context:
            context = {}
        
        # Анализируем контекст
        network_type = context.get('network_type', 'wifi')  # wifi, mobile, vpn
        is_blocked = context.get('is_blocked', False)
        app_type = context.get('app_type', 'general')
        priority = context.get('priority', 'speed')  # speed, stability, stealth
        
        # Правила выбора на основе контекста
        if priority == 'speed':
            # Приоритет скорости - простые стратегии
            if network_type == 'wifi':
                return StrategyType.SIMPLE_FAKE
            else:
                return StrategyType.ALT
        elif priority == 'stability':
            # Приоритет стабильности - проверенные стратегии
            if is_blocked:
                return StrategyType.ALT9
            else:
                return StrategyType.FAKE_TLS_AUTO
        elif priority == 'stealth':
            # Приоритет скрытности - сложные стратегии
            return StrategyType.FAKE_TLS_AUTO_ALT3
        else:
            # По умолчанию - автоопределение
            return StrategyType.AUTO
    
    def export_strategies(self, filepath: str):
        """Экспорт всех стратегий"""
        export_data = {
            'strategies': self.strategies,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Конвертируем Enum ключи в строки
        strategies_dict = {}
        for key, value in self.strategies.items():
            strategies_dict[key.value] = value
        
        export_data['strategies'] = strategies_dict
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def import_strategies(self, filepath: str):
        """Импорт стратегий"""
        with open(filepath, 'r', encoding='utf-8') as f:
            import_data = json.load(f)
        
        imported_strategies = import_data.get('strategies', {})
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for strategy_type_str, strategy_data in imported_strategies.items():
                try:
                    strategy_type = StrategyType(strategy_type_str)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO strategies 
                        (name, type, description, params, effectiveness, 
                         latency_impact, bandwidth_impact)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy_data.get('name', ''),
                        strategy_type.value,
                        strategy_data.get('description', ''),
                        json.dumps(strategy_data.get('params', {})),
                        strategy_data.get('params', {}).get('effectiveness', 0),
                        strategy_data.get('params', {}).get('latency_impact', ''),
                        strategy_data.get('params', {}).get('bandwidth_impact', '')
                    ))
                    
                    # Обновляем кэш
                    self.strategies[strategy_type] = strategy_data
                
                except:
                    continue
            
            conn.commit()
            conn.close()
    
    def generate_strategy_report(self) -> str:
        """Генерация отчёта по стратегиям"""
        report = f"""
=== ОТЧЁТ ПО СТРАТЕГИЯМ ОБХОДА DPI ===
Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Всего стратегий: {len(self.strategies)}

СТРАТЕГИИ:
"""
        
        for strategy_type, strategy_data in sorted(self.strategies.items(), 
                                                  key=lambda x: x[1].get('effectiveness', 0), 
                                                  reverse=True):
            effectiveness = strategy_data.get('params', {}).get('effectiveness', 0)
            usage = strategy_data.get('total_usage', 0)
            
            report += f"""
{strategy_data.get('name', 'Unknown')} ({strategy_type.value}):
- Описание: {strategy_data.get('description', 'Нет описания')}
- Эффективность: {effectiveness:.1f}%
- Использовано: {usage} раз
- Влияние на задержку: {strategy_data.get('params', {}).get('latency_impact', 'N/A')}
- Влияние на пропускную способность: {strategy_data.get('params', {}).get('bandwidth_impact', 'N/A')}
"""
        
        # Статистика по приложениям
        report += "\nСТАТИСТИКА ПО ПРИЛОЖЕНИЯМ:\n"
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT app_package, strategy_type, success_rate, usage_count
                FROM app_strategies 
                WHERE usage_count > 0
                ORDER BY success_rate DESC
                LIMIT 10
            ''')
            
            rows = cursor.fetchall()
            
            for row in rows:
                app_package, strategy_type, success_rate, usage_count = row
                report += f"- {app_package}: {strategy_type} ({success_rate:.1f}%, {usage_count} использований)\n"
            
            conn.close()
        
        return report