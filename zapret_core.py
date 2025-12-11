import os
import json
import subprocess
import threading
import time
import requests
from urllib.parse import urlparse
import socket

class ZapretCore:
    """Ядро системы обхода DPI"""
    
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.lists_dir = os.path.join(self.base_dir, 'lists')
        self.bin_dir = os.path.join(self.base_dir, 'bin')
        self.config_file = os.path.join(self.base_dir, 'config.json')
        
        # Создаём директории
        os.makedirs(self.lists_dir, exist_ok=True)
        os.makedirs(self.bin_dir, exist_ok=True)
        
        # Загрузка конфигурации
        self.config = self.load_config()
        
        # Статус
        self.is_running = False
        self.process = None
        
        # Инициализация списков
        self.init_lists()
    
    def load_config(self):
        """Загрузка конфигурации"""
        default_config = {
            'strategy': 'AUTO',
            'dns_server': '8.8.8.8',
            'proxy_port': 8080,
            'game_filter': False,
            'update_interval': 86400,  # 24 часа
            'last_update': 0
        }
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Объединяем с дефолтными значениями
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except:
            return default_config
    
    def save_config(self):
        """Сохранение конфигурации"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def init_lists(self):
        """Инициализация списков доменов и IP"""
        lists = {
            'list-general.txt': [
                'youtube.com',
                'youtubei.googleapis.com',
                'googlevideo.com',
                'discord.com',
                'discordapp.net',
                'discord.media',
                'discord.gift',
                'steamcommunity.com',
                'steampowered.com',
                'valvesoftware.com'
            ],
            'list-google.txt': [
                'google.com',
                'googleapis.com',
                'gstatic.com'
            ],
            'list-exclude.txt': [
                # Исключения
            ],
            'ipset-all.txt': [
                '203.0.113.113/32'  # Заглушка
            ],
            'ipset-exclude.txt': [
                # Исключения IP
            ]
        }
        
        for filename, content in lists.items():
            filepath = os.path.join(self.lists_dir, filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content))
    
    def update_lists(self):
        """Автоматическое обновление списков из интернета"""
        sources = {
            'list-general.txt': 'https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/main/lists/list-general.txt',
            'ipset-all.txt': 'https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/main/lists/ipset-all.txt'
        }
        
        for filename, url in sources.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    filepath = os.path.join(self.lists_dir, filename)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    print(f"Updated {filename}")
            except Exception as e:
                print(f"Failed to update {filename}: {e}")
        
        # Обновляем время последнего обновления
        self.config['last_update'] = time.time()
        self.save_config()
    
    def auto_detect_strategy(self, app_package):
        """Автоматическое определение стратегии для приложения"""
        # База знаний стратегий
        strategy_db = {
            'com.google.android.youtube': 'FAKE_TLS_AUTO',
            'com.discord': 'ALT9',
            'com.valvesoftware.android.steam.community': 'ALT',
            'com.spotify.music': 'SIMPLE_FAKE',
            'com.netflix.mediaclient': 'FAKE_TLS_AUTO_ALT',
            'com.instagram.android': 'ALT4',
            'com.facebook.katana': 'ALT4',
            'com.whatsapp': 'SIMPLE_FAKE',
            'org.telegram.messenger': 'FAKE_TLS_AUTO'
        }
        
        # Если приложение известно - возвращаем стратегию
        if app_package in strategy_db:
            return strategy_db[app_package]
        
        # Анализ приложения
        try:
            # Получаем информацию о приложении
            cmd = f"pm list packages -f {app_package}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            # Анализ на основе имени
            app_name = app_package.lower()
            
            if 'game' in app_name or 'play' in app_name:
                return 'ALT'  # Для игр
            elif 'video' in app_name or 'stream' in app_name:
                return 'FAKE_TLS_AUTO'  # Для видео
            elif 'browser' in app_name or 'web' in app_name:
                return 'ALT9'  # Для браузеров
            else:
                return 'AUTO'  # Автоматический выбор
                
        except:
            return 'AUTO'
    
    def get_strategy_params(self, strategy_name):
        """Получение параметров стратегии на основе Windows-версии"""
        
        # Параметры из Windows .bat файлов
        strategies = {
            'FAKE_TLS_AUTO': {
                'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                'udp_ports': '443,19294-19344,50000-50100',
                'params': [
                    '--filter-udp=443 --hostlist="lists/list-general.txt" --dpi-desync=fake --dpi-desync-repeats=11',
                    '--filter-udp=19294-19344,50000-50100 --filter-l7=discord,stun --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=fake,multidisorder --dpi-desync-repeats=11',
                    '--filter-tcp=443 --hostlist="lists/list-google.txt" --ip-id=zero --dpi-desync=fake,multidisorder --dpi-desync-repeats=11',
                    '--filter-tcp=80,443 --hostlist="lists/list-general.txt" --dpi-desync=fake,multidisorder --dpi-desync-repeats=11'
                ]
            },
            'ALT9': {
                'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                'udp_ports': '443,19294-19344,50000-50100',
                'params': [
                    '--filter-udp=443 --hostlist="lists/list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-udp=19294-19344,50000-50100 --filter-l7=discord,stun --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=hostfakesplit --dpi-desync-repeats=4',
                    '--filter-tcp=443 --hostlist="lists/list-google.txt" --ip-id=zero --dpi-desync=hostfakesplit --dpi-desync-repeats=4',
                    '--filter-tcp=80,443 --hostlist="lists/list-general.txt" --dpi-desync=hostfakesplit --dpi-desync-repeats=4'
                ]
            },
            'SIMPLE_FAKE': {
                'tcp_ports': '80,443,2053,2083,2087,2096,8443',
                'udp_ports': '443,19294-19344,50000-50100',
                'params': [
                    '--filter-udp=443 --hostlist="lists/list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-udp=19294-19344,50000-50100 --filter-l7=discord,stun --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-tcp=2053,2083,2087,2096,8443 --hostlist-domains=discord.media --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-tcp=443 --hostlist="lists/list-google.txt" --ip-id=zero --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-tcp=80,443 --hostlist="lists/list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6'
                ]
            },
            'AUTO': {
                'tcp_ports': '80,443',
                'udp_ports': '443',
                'params': [
                    '--filter-tcp=80,443 --hostlist="lists/list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6',
                    '--filter-udp=443 --hostlist="lists/list-general.txt" --dpi-desync=fake --dpi-desync-repeats=6'
                ]
            }
        }
        
        return strategies.get(strategy_name, strategies['AUTO'])
    
    def create_local_proxy(self, strategy_params, dns_server, proxy_port):
        """Создание локального прокси для обхода DPI"""
        # Здесь будет реализация прокси на Python
        # Это упрощённая версия для примера
        
        proxy_script = f'''
import socket
import threading
import ssl

PROXY_PORT = {proxy_port}
DNS_SERVER = '{dns_server}'

class DPIProxy:
    def __init__(self):
        self.running = True
        
    def start(self):
        # Создаём сокет
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', PROXY_PORT))
        server.listen(5)
        
        print(f"Прокси запущен на порту {{PROXY_PORT}}")
        
        while self.running:
            client, addr = server.accept()
            thread = threading.Thread(target=self.handle_client, args=(client,))
            thread.start()
    
    def handle_client(self, client):
        try:
            # Получаем запрос
            request = client.recv(4096)
            
            if request:
                # Применяем DPI обход
                modified_request = self.apply_dpi_bypass(request)
                
                # Отправляем на целевой сервер
                target_host = self.extract_host(request)
                remote = socket.create_connection((target_host, 443))
                
                # Если HTTPS - оборачиваем в SSL
                if b'CONNECT' in request:
                    client.send(b'HTTP/1.1 200 Connection Established\\r\\n\\r\\n')
                    remote = ssl.wrap_socket(remote)
                
                remote.send(modified_request)
                
                # Проксируем данные
                self.proxy_data(client, remote)
                
        except Exception as e:
            print(f"Ошибка: {{e}}")
        finally:
            client.close()
    
    def apply_dpi_bypass(self, data):
        """Применение методов обхода DPI"""
        # Здесь реализация стратегий обхода
        # Например, подмена SNI, добавление фейковых заголовков и т.д.
        return data
    
    def extract_host(self, data):
        """Извлечение хоста из запроса"""
        # Упрощённая реализация
        return DNS_SERVER

if __name__ == '__main__':
    proxy = DPIProxy()
    proxy.start()
'''
        
        # Сохраняем скрипт прокси
        proxy_path = os.path.join(self.bin_dir, 'dpi_proxy.py')
        with open(proxy_path, 'w', encoding='utf-8') as f:
            f.write(proxy_script)
        
        return proxy_path
    
    def start(self, strategy='AUTO', dns_server='8.8.8.8', proxy_port=8080, game_filter=False):
        """Запуск системы обхода"""
        try:
            # Получаем параметры стратегии
            strategy_params = self.get_strategy_params(strategy)
            
            # Создаём локальный прокси
            proxy_script = self.create_local_proxy(strategy_params, dns_server, proxy_port)
            
            # Запускаем прокси в отдельном процессе
            self.process = subprocess.Popen(
                ['python3', proxy_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Настраиваем перенаправление трафика через прокси
            self.setup_proxy_redirect(proxy_port)
            
            # Настраиваем DNS
            self.set_dns(dns_server)
            
            self.is_running = True
            
            # Обновляем конфиг
            self.config['strategy'] = strategy
            self.config['dns_server'] = dns_server
            self.config['proxy_port'] = proxy_port
            self.config['game_filter'] = game_filter
            self.save_config()
            
            return True
            
        except Exception as e:
            print(f"Ошибка запуска: {e}")
            return False
    
    def stop(self):
        """Остановка системы"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=5)
            
            # Восстанавливаем настройки сети
            self.restore_network_settings()
            
            self.is_running = False
            return True
            
        except Exception as e:
            print(f"Ошибка остановки: {e}")
            return False
    
    def setup_proxy_redirect(self, port):
        """Настройка перенаправления трафика через прокси"""
        # В Android без root это делается через VPNService
        # Здесь упрощённая реализация
        
        # Создаём iptables правила (требует root)
        try:
            # Разрешаем локальный трафик
            subprocess.run(['iptables', '-A', 'OUTPUT', '-d', '127.0.0.1', '-j', 'ACCEPT'], 
                          check=False)
            
            # Перенаправляем HTTP/HTTPS трафик
            subprocess.run(['iptables', '-t', 'nat', '-A', 'OUTPUT', '-p', 'tcp', 
                          '--dport', '80', '-j', 'REDIRECT', '--to-port', str(port)], 
                          check=False)
            subprocess.run(['iptables', '-t', 'nat', '-A', 'OUTPUT', '-p', 'tcp',
                          '--dport', '443', '-j', 'REDIRECT', '--to-port', str(port)],
                          check=False)
            
        except:
            # Без root используем другой подход
            pass
    
    def set_dns(self, dns_server):
        """Установка DNS сервера"""
        try:
            # Для Android без root
            subprocess.run(['settings', 'put', 'global', 'private_dns_mode', 'hostname'],
                          check=False)
            subprocess.run(['settings', 'put', 'global', 'private_dns_specifier', dns_server],
                          check=False)
        except:
            pass
    
    def restore_network_settings(self):
        """Восстановление сетевых настроек"""
        try:
            # Очищаем iptables правила
            subprocess.run(['iptables', '-F'], check=False)
            subprocess.run(['iptables', '-t', 'nat', '-F'], check=False)
            
            # Восстанавливаем DNS
            subprocess.run(['settings', 'put', 'global', 'private_dns_mode', 'off'],
                          check=False)
        except:
            pass
    
    def test_strategy(self, strategy):
        """Тестирование стратегии"""
        try:
            # Тестируем подключение к тестовому сайту
            test_url = 'https://www.google.com'
            
            # Запускаем прокси с тестовой стратегией
            test_proxy = self.create_local_proxy(
                self.get_strategy_params(strategy),
                '8.8.8.8',
                9999
            )
            
            # Запускаем временный прокси
            process = subprocess.Popen(['python3', test_proxy],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
            
            time.sleep(2)  # Даём время на запуск
            
            # Пытаемся подключиться через прокси
            import urllib.request
            proxy_handler = urllib.request.ProxyHandler({'https': '127.0.0.1:9999'})
            opener = urllib.request.build_opener(proxy_handler)
            
            try:
                response = opener.open(test_url, timeout=10)
                success = response.getcode() == 200
            except:
                success = False
            
            # Останавливаем прокси
            process.terminate()
            process.wait()
            
            return success
            
        except:
            return False