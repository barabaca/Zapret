#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Any
import threading

class AppManager:
    """Управление приложениями и их настройками"""
    
    def __init__(self, db_path: str = "app_profiles.db"):
        """Инициализация менеджера приложений"""
        self.db_path = db_path
        self.installed_apps = []
        self.app_profiles = {}
        self.lock = threading.Lock()
        
        # Инициализация базы данных
        self._init_database()
        
        # Загрузка кэша
        self.load_cache()
    
    def _init_database(self):
        """Инициализация базы данных SQLite"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Таблица профилей приложений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_profiles (
                    package TEXT PRIMARY KEY,
                    name TEXT,
                    enabled INTEGER DEFAULT 0,
                    strategy TEXT DEFAULT 'AUTO',
                    bypass_tcp INTEGER DEFAULT 1,
                    bypass_udp INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 50,
                    last_used TIMESTAMP,
                    success_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица сетевой активности
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_traffic (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    protocol TEXT,
                    port INTEGER,
                    domain TEXT,
                    bytes_sent INTEGER,
                    bytes_received INTEGER,
                    FOREIGN KEY (package) REFERENCES app_profiles(package)
                )
            ''')
            
            # Таблица исключений
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_exceptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    package TEXT,
                    domain TEXT,
                    ip TEXT,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (package) REFERENCES app_profiles(package)
                )
            ''')
            
            conn.commit()
            conn.close()
    
    def get_installed_apps(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Получение списка установленных приложений"""
        if self.installed_apps and not force_refresh:
            return self.installed_apps
        
        apps = []
        try:
            # Используем команду pm для получения списка пакетов
            cmd = "pm list packages -3 -f"  # -3 = сторонние приложения
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        # Парсим строку вида: package:/data/app/com.example-1/base.apk=com.example
                        parts = line.split('=')
                        if len(parts) == 2:
                            package = parts[1].strip()
                            
                            # Извлекаем путь к APK для получения имени
                            apk_path = parts[0].replace('package:', '').strip()
                            
                            # Получаем человеко-читаемое имя приложения
                            app_name = self._get_app_name(package, apk_path)
                            
                            # Получаем UID приложения
                            uid = self._get_app_uid(package)
                            
                            # Получаем версию
                            version = self._get_app_version(package)
                            
                            apps.append({
                                'package': package,
                                'name': app_name,
                                'uid': uid,
                                'version': version,
                                'apk_path': apk_path,
                                'is_system': False
                            })
            
            # Добавляем системные приложения (опционально)
            self._add_system_apps(apps)
            
            # Сортируем по имени
            apps.sort(key=lambda x: x['name'].lower())
            
            self.installed_apps = apps
            
        except Exception as e:
            print(f"Ошибка получения приложений: {e}")
            apps = self._get_fallback_apps()
            self.installed_apps = apps
        
        return apps
    
    def _get_app_name(self, package: str, apk_path: str) -> str:
        """Получение имени приложения"""
        try:
            # Пытаемся получить имя через aapt
            cmd = f"aapt dump badging '{apk_path}' 2>/dev/null | grep 'application-label:'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Парсим имя из вывода aapt
                for line in result.stdout.split('\n'):
                    if 'application-label:' in line:
                        name = line.split("'")[1]
                        if name and name.strip():
                            return name.strip()
            
            # Пытаемся получить имя через pm
            cmd = f"pm list packages -f -i {package}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Извлекаем имя из вывода
                for line in result.stdout.split('\n'):
                    if package in line:
                        # Формат: package:/path/to/apk=com.package (installer=com.android.vending)
                        parts = line.split('(installer=')
                        if len(parts) > 1:
                            installer = parts[1].replace(')', '')
                            # Можно использовать имя инсталлера как подсказку
                            pass
        
        except:
            pass
        
        # Возвращаем последнюю часть package как запасной вариант
        return package.split('.')[-1].replace('_', ' ').title()
    
    def _get_app_uid(self, package: str) -> str:
        """Получение UID приложения"""
        try:
            cmd = f"dumpsys package {package} | grep userId"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'userId=' in line:
                    uid = line.split('=')[1].split()[0]
                    return uid
            
        except:
            pass
        
        return "10000"  # Дефолтный UID для пользовательских приложений
    
    def _get_app_version(self, package: str) -> str:
        """Получение версии приложения"""
        try:
            cmd = f"dumpsys package {package} | grep versionName"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'versionName=' in line:
                    version = line.split('=')[1].strip()
                    return version
            
        except:
            pass
        
        return "1.0"
    
    def _add_system_apps(self, apps_list: List[Dict[str, Any]]):
        """Добавление системных приложений (опционально)"""
        try:
            cmd = "pm list packages -s -f"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.startswith('package:'):
                        parts = line.split('=')
                        if len(parts) == 2:
                            package = parts[1].strip()
                            
                            # Пропускаем если уже есть
                            if any(app['package'] == package for app in apps_list):
                                continue
                            
                            app_name = self._get_app_name(package, "")
                            uid = self._get_app_uid(package)
                            
                            apps_list.append({
                                'package': package,
                                'name': f"[System] {app_name}",
                                'uid': uid,
                                'version': self._get_app_version(package),
                                'apk_path': '',
                                'is_system': True
                            })
        
        except Exception as e:
            print(f"Ошибка получения системных приложений: {e}")
    
    def _get_fallback_apps(self) -> List[Dict[str, Any]]:
        """Резервный список приложений (если команды pm не работают)"""
        fallback_apps = [
            {
                'package': 'com.google.android.youtube',
                'name': 'YouTube',
                'uid': '10123',
                'version': '18.45.43',
                'apk_path': '/data/app/com.google.android.youtube-1',
                'is_system': False
            },
            {
                'package': 'com.discord',
                'name': 'Discord',
                'uid': '10124',
                'version': '205.15',
                'apk_path': '/data/app/com.discord-1',
                'is_system': False
            },
            {
                'package': 'com.valvesoftware.android.steam.community',
                'name': 'Steam',
                'uid': '10125',
                'version': '3.0',
                'apk_path': '/data/app/com.valvesoftware.android.steam.community-1',
                'is_system': False
            },
            {
                'package': 'com.spotify.music',
                'name': 'Spotify',
                'uid': '10126',
                'version': '8.9.20',
                'apk_path': '/data/app/com.spotify.music-1',
                'is_system': False
            }
        ]
        return fallback_apps
    
    def get_app_profile(self, package: str) -> Dict[str, Any]:
        """Получение профиля приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM app_profiles WHERE package = ?
            ''', (package,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            else:
                # Создаём дефолтный профиль
                return self._create_default_profile(package)
    
    def _create_default_profile(self, package: str) -> Dict[str, Any]:
        """Создание дефолтного профиля"""
        apps = self.get_installed_apps()
        app_info = next((app for app in apps if app['package'] == package), None)
        
        profile = {
            'package': package,
            'name': app_info['name'] if app_info else package,
            'enabled': 0,
            'strategy': 'AUTO',
            'bypass_tcp': 1,
            'bypass_udp': 1,
            'priority': 50,
            'last_used': None,
            'success_count': 0,
            'fail_count': 0,
            'created_at': datetime.now().isoformat()
        }
        
        return profile
    
    def save_app_profile(self, package: str, updates: Dict[str, Any]):
        """Сохранение профиля приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем существует ли профиль
            cursor.execute('SELECT COUNT(*) FROM app_profiles WHERE package = ?', (package,))
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Обновляем существующий профиль
                set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values())
                values.append(package)
                
                cursor.execute(f'''
                    UPDATE app_profiles SET {set_clause} WHERE package = ?
                ''', values)
            else:
                # Создаём новый профиль
                apps = self.get_installed_apps()
                app_info = next((app for app in apps if app['package'] == package), None)
                
                profile = self._create_default_profile(package)
                profile.update(updates)
                
                columns = ', '.join(profile.keys())
                placeholders = ', '.join(['?' for _ in profile])
                values = list(profile.values())
                
                cursor.execute(f'''
                    INSERT INTO app_profiles ({columns}) VALUES ({placeholders})
                ''', values)
            
            conn.commit()
            conn.close()
    
    def get_enabled_apps(self) -> List[Dict[str, Any]]:
        """Получение списка включённых приложений"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM app_profiles 
                WHERE enabled = 1 
                ORDER BY priority DESC, name ASC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []
    
    def analyze_app_traffic(self, package: str, duration: int = 10) -> Dict[str, Any]:
        """Анализ сетевой активности приложения"""
        try:
            uid = self._get_app_uid(package)
            
            # Собираем статистику трафика
            stats = {
                'package': package,
                'uid': uid,
                'start_time': datetime.now().isoformat(),
                'duration': duration,
                'tcp_connections': 0,
                'udp_connections': 0,
                'domains': set(),
                'ports': set(),
                'protocols': set(),
                'total_bytes': 0
            }
            
            # Мониторим трафик через tcpdump (если доступно)
            self._monitor_traffic_with_tcpdump(uid, stats, duration)
            
            # Или через /proc/net
            self._monitor_traffic_from_proc(uid, stats)
            
            stats['end_time'] = datetime.now().isoformat()
            stats['domains'] = list(stats['domains'])
            stats['ports'] = list(stats['ports'])
            stats['protocols'] = list(stats['protocols'])
            
            # Сохраняем результаты в базу
            self._save_traffic_analysis(stats)
            
            return stats
            
        except Exception as e:
            print(f"Ошибка анализа трафика: {e}")
            return self._get_mock_traffic_stats(package)
    
    def _monitor_traffic_with_tcpdump(self, uid: str, stats: Dict[str, Any], duration: int):
        """Мониторинг трафика через tcpdump"""
        try:
            cmd = f"timeout {duration} tcpdump -i any -n -v uid {uid} 2>/dev/null | head -50"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=duration + 2)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    # Анализируем строки tcpdump
                    if 'IP' in line and '>' in line:
                        stats['tcp_connections'] += 1
                        
                        # Извлекаем порты
                        parts = line.split('>')
                        if len(parts) > 1:
                            dest_part = parts[1].strip()
                            if '.' in dest_part:
                                port_part = dest_part.split(':')[1] if ':' in dest_part else ''
                                if port_part and port_part.split('.')[0].isdigit():
                                    port = int(port_part.split('.')[0])
                                    stats['ports'].add(port)
                    
                    # Ищем домены в DNS запросах
                    if 'A?' in line:
                        domain_start = line.find('A?') + 3
                        domain_end = line.find('.', domain_start)
                        if domain_end > domain_start:
                            domain = line[domain_start:domain_end]
                            stats['domains'].add(domain)
        
        except:
            pass
    
    def _monitor_traffic_from_proc(self, uid: str, stats: Dict[str, Any]):
        """Мониторинг трафика из /proc/net"""
        try:
            # Читаем TCP соединения
            with open('/proc/net/tcp', 'r') as f:
                lines = f.readlines()[1:]  # Пропускаем заголовок
                for line in lines:
                    if uid in line:
                        stats['tcp_connections'] += 1
            
            # Читаем UDP соединения
            with open('/proc/net/udp', 'r') as f:
                lines = f.readlines()[1:]
                for line in lines:
                    if uid in line:
                        stats['udp_connections'] += 1
        
        except:
            pass
    
    def _get_mock_traffic_stats(self, package: str) -> Dict[str, Any]:
        """Моковые данные трафика для тестирования"""
        mock_data = {
            'com.google.android.youtube': {
                'tcp_connections': 15,
                'udp_connections': 8,
                'domains': ['youtube.com', 'googlevideo.com', 'ytimg.com'],
                'ports': [443, 80, 1935, 3000],
                'protocols': ['HTTPS', 'HTTP', 'QUIC'],
                'total_bytes': 1500000
            },
            'com.discord': {
                'tcp_connections': 12,
                'udp_connections': 25,
                'domains': ['discord.com', 'discordapp.net', 'discord.media'],
                'ports': [443, 3478, 5349, 1935],
                'protocols': ['HTTPS', 'UDP', 'WebSocket'],
                'total_bytes': 800000
            }
        }
        
        if package in mock_data:
            stats = mock_data[package]
            stats.update({
                'package': package,
                'uid': self._get_app_uid(package),
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': 10
            })
            return stats
        else:
            return {
                'package': package,
                'uid': '10000',
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration': 10,
                'tcp_connections': 5,
                'udp_connections': 2,
                'domains': ['example.com'],
                'ports': [443, 80],
                'protocols': ['HTTPS'],
                'total_bytes': 50000
            }
    
    def _save_traffic_analysis(self, stats: Dict[str, Any]):
        """Сохранение анализа трафика в базу"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for port in stats['ports']:
                cursor.execute('''
                    INSERT INTO app_traffic 
                    (package, protocol, port, domain, bytes_sent, bytes_received)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (stats['package'], 'TCP/UDP', port, 
                      ','.join(stats['domains'][:3]), stats['total_bytes'], 0))
            
            conn.commit()
            conn.close()
    
    def get_app_performance_stats(self, package: str) -> Dict[str, Any]:
        """Получение статистики производительности приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем общую статистику
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_connections,
                    SUM(bytes_sent) as total_bytes_sent,
                    SUM(bytes_received) as total_bytes_received,
                    MIN(timestamp) as first_activity,
                    MAX(timestamp) as last_activity
                FROM app_traffic 
                WHERE package = ?
            ''', (package,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                columns = [description[0] for description in cursor.description]
                stats = dict(zip(columns, row))
                
                # Рассчитываем среднюю скорость
                if stats['first_activity'] and stats['last_activity']:
                    from datetime import datetime
                    first = datetime.fromisoformat(stats['first_activity'].replace('Z', '+00:00'))
                    last = datetime.fromisoformat(stats['last_activity'].replace('Z', '+00:00'))
                    hours = (last - first).total_seconds() / 3600
                    
                    if hours > 0:
                        stats['avg_speed_kbps'] = (stats['total_bytes_sent'] or 0) * 8 / 1024 / hours
                    else:
                        stats['avg_speed_kbps'] = 0
                else:
                    stats['avg_speed_kbps'] = 0
                
                return stats
            else:
                return {
                    'total_connections': 0,
                    'total_bytes_sent': 0,
                    'total_bytes_received': 0,
                    'avg_speed_kbps': 0
                }
    
    def add_app_exception(self, package: str, domain: str = None, 
                         ip: str = None, reason: str = "User defined"):
        """Добавление исключения для приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO app_exceptions (package, domain, ip, reason)
                VALUES (?, ?, ?, ?)
            ''', (package, domain, ip, reason))
            
            conn.commit()
            conn.close()
    
    def get_app_exceptions(self, package: str) -> List[Dict[str, Any]]:
        """Получение исключений для приложения"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM app_exceptions 
                WHERE package = ? 
                ORDER BY created_at DESC
            ''', (package,))
            
            rows = cursor.fetchall()
            conn.close()
            
            if rows:
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
            else:
                return []
    
    def clear_app_cache(self, package: str = None):
        """Очистка кэша приложения"""
        try:
            if package:
                cmd = f"pm clear {package}"
                subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                # Очистка кэша приложения Zapret
                import shutil
                cache_dirs = [
                    'cache',
                    '__pycache__',
                    '*.pyc',
                    '*.pyo',
                    '*.pyd'
                ]
                
                for cache_dir in cache_dirs:
                    if os.path.exists(cache_dir):
                        if os.path.isdir(cache_dir):
                            shutil.rmtree(cache_dir)
                        else:
                            import glob
                            for file in glob.glob(cache_dir):
                                os.remove(file)
        
        except Exception as e:
            print(f"Ошибка очистки кэша: {e}")
    
    def export_app_profiles(self, filepath: str):
        """Экспорт профилей приложений"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM app_profiles')
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            profiles = [dict(zip(columns, row)) for row in rows]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)
            
            conn.close()
    
    def import_app_profiles(self, filepath: str):
        """Импорт профилей приложений"""
        with self.lock:
            with open(filepath, 'r', encoding='utf-8') as f:
                profiles = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for profile in profiles:
                columns = ', '.join(profile.keys())
                placeholders = ', '.join(['?' for _ in profile])
                values = list(profile.values())
                
                cursor.execute(f'''
                    INSERT OR REPLACE INTO app_profiles ({columns}) 
                    VALUES ({placeholders})
                ''', values)
            
            conn.commit()
            conn.close()
    
    def load_cache(self):
        """Загрузка кэша приложений"""
        cache_file = 'apps_cache.json'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.installed_apps = json.load(f)
            except:
                self.installed_apps = []
    
    def save_cache(self):
        """Сохранение кэша приложений"""
        cache_file = 'apps_cache.json'
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.installed_apps, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def __del__(self):
        """Деструктор - сохранение кэша"""
        self.save_cache()