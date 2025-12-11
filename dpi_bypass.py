#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import ssl
import struct
import hashlib
import random
import time
from typing import Tuple, Optional, Dict, Any
import threading
from enum import Enum

class DPIStrategy(Enum):
    """Стратегии обхода DPI"""
    FAKE_TLS = "fake_tls"
    FAKE_QUIC = "fake_quic"
    MULTISPLIT = "multisplit"
    HOST_FAKE_SPLIT = "host_fake_split"
    SYNDATA = "syndata"
    FAKE_DSPLIT = "fake_dsplit"
    MULTIDISORDER = "multidisorder"
    AUTO = "auto"

class DPIBypass:
    """Основной класс для обхода DPI"""
    
    def __init__(self):
        # Шаблоны для подмены (аналоги Windows версии)
        self.templates = {
            'tls_clienthello_www_google_com': self._generate_tls_client_hello,
            'quic_initial_www_google_com': self._generate_quic_initial,
            'tls_clienthello_4pda_to': self._generate_tls_4pda,
        }
        
        # Конфигурация стратегий
        self.strategy_configs = {
            DPIStrategy.FAKE_TLS: {
                'repeats': 6,
                'fooling': ['ts'],
                'mod': 'none'
            },
            DPIStrategy.FAKE_QUIC: {
                'repeats': 6,
                'autottl': 2,
                'cutoff': 'n2'
            },
            DPIStrategy.MULTISPLIT: {
                'repeats': 8,
                'split_seqovl': 681,
                'split_pos': 1,
                'fooling': ['ts']
            },
            DPIStrategy.HOST_FAKE_SPLIT: {
                'repeats': 4,
                'fooling': ['ts', 'md5sig'],
                'mod': 'host=ozon.ru'
            }
        }
        
        self.active = False
        self.current_strategy = DPIStrategy.AUTO
        
    def _generate_tls_client_hello(self, sni: str = "www.google.com") -> bytes:
        """Генерация TLS ClientHello пакета"""
        # Упрощённая версия TLS ClientHello
        # В реальной реализации нужно точное соответствие Windows-шаблонам
        
        # TLS Record Layer
        record_type = b'\x16'  # Handshake
        version = b'\x03\x03'  # TLS 1.2
        
        # Handshake Protocol
        handshake_type = b'\x01'  # ClientHello
        length = b'\x00\x00\xa0'  # Длина
        
        # Client Version
        client_version = b'\x03\x03'  # TLS 1.2
        
        # Random (32 bytes)
        random_bytes = random.randbytes(32)
        
        # Session ID
        session_id_len = b'\x00'
        
        # Cipher Suites
        cipher_suites = b'\x00\x2a'  # 42 cipher suites
        cipher_list = b'\x13\x02\x13\x03\x13\x01\xc0\x2c\xc0\x30\xcc\xa9\xcc\xa8\xc0\x2b\xc0\x2f'
        
        # Compression Methods
        compression = b'\x01\x00'
        
        # Extensions
        extensions_len = b'\x00\x5c'  # 92 bytes
        
        # SNI Extension
        sni_ext = b'\x00\x00'  # server_name extension
        sni_len = b'\x00\x18'  # 24 bytes
        sni_list_len = b'\x00\x16'  # 22 bytes
        sni_type = b'\x00'  # host_name
        sni_host_len = b'\x00\x13'  # 19 bytes
        sni_host = sni.encode('utf-8').ljust(19, b'\x00')
        
        # Assemble packet
        extensions = sni_ext + sni_len + sni_list_len + sni_type + sni_host_len + sni_host
        
        # Build ClientHello
        client_hello = (
            client_version + random_bytes + session_id_len + 
            cipher_suites + cipher_list + compression + extensions_len + extensions
        )
        
        # Build Handshake
        handshake = handshake_type + struct.pack('!I', len(client_hello))[1:] + client_hello
        
        # Build Record
        record = record_type + version + struct.pack('!H', len(handshake)) + handshake
        
        return record
    
    def _generate_quic_initial(self) -> bytes:
        """Генерация QUIC Initial пакета"""
        # Упрощённая QUIC Initial packet
        # В реальной реализации нужно точное соответствие Windows-шаблонам
        
        # QUIC Header
        header_form = 0x80  # Long header
        fixed_bit = 0x40
        packet_type = 0x00  # Initial
        version = 0x00000001  # QUIC v1
        
        dest_conn_id_len = 8
        dest_conn_id = random.randbytes(dest_conn_id_len)
        src_conn_id_len = 0
        
        # Token Length
        token_len = 0
        
        # Length
        length = 1200
        
        # Packet Number
        packet_number = 0
        
        # Build header
        header = bytes([
            header_form | fixed_bit | packet_type,
            (dest_conn_id_len << 4) | src_conn_id_len
        ])
        
        header += struct.pack('!I', version)
        header += bytes([dest_conn_id_len]) + dest_conn_id
        header += bytes([src_conn_id_len])
        header += struct.pack('!H', token_len)
        header += struct.pack('!H', length)
        header += struct.pack('!B', packet_number)
        
        # Payload (Crypto frames)
        crypto_offset = 0
        crypto_length = 100
        
        crypto_frame = bytes([0x06])  # CRYPTO frame type
        crypto_frame += self._encode_var_int(crypto_offset)
        crypto_frame += self._encode_var_int(crypto_length)
        crypto_frame += random.randbytes(crypto_length)
        
        return header + crypto_frame
    
    def _generate_tls_4pda(self) -> bytes:
        """Генерация TLS ClientHello для 4pda (альтернативный шаблон)"""
        # Аналогично Google, но с другими параметрами
        return self._generate_tls_client_hello("4pda.to")
    
    def _encode_var_int(self, value: int) -> bytes:
        """Кодирование переменного целого (QUIC)"""
        if value <= 63:
            return bytes([value])
        elif value <= 16383:
            return struct.pack('!H', value | 0x4000)
        elif value <= 1073741823:
            return struct.pack('!I', value | 0x80000000)
        else:
            return struct.pack('!Q', value | 0xC000000000000000)
    
    def apply_strategy(self, data: bytes, strategy: DPIStrategy, 
                      params: Optional[Dict[str, Any]] = None) -> bytes:
        """Применение стратегии обхода к данным"""
        if strategy == DPIStrategy.AUTO:
            strategy = self._detect_best_strategy(data)
        
        if strategy == DPIStrategy.FAKE_TLS:
            return self._apply_fake_tls(data, params)
        elif strategy == DPIStrategy.FAKE_QUIC:
            return self._apply_fake_quic(data, params)
        elif strategy == DPIStrategy.MULTISPLIT:
            return self._apply_multisplit(data, params)
        elif strategy == DPIStrategy.HOST_FAKE_SPLIT:
            return self._apply_host_fake_split(data, params)
        elif strategy == DPIStrategy.SYNDATA:
            return self._apply_syndata(data, params)
        elif strategy == DPIStrategy.FAKE_DSPLIT:
            return self._apply_fake_dsplit(data, params)
        elif strategy == DPIStrategy.MULTIDISORDER:
            return self._apply_multidisorder(data, params)
        else:
            return data
    
    def _detect_best_strategy(self, data: bytes) -> DPIStrategy:
        """Автоматическое определение лучшей стратегии"""
        # Анализируем данные для определения типа трафика
        
        if len(data) < 10:
            return DPIStrategy.FAKE_TLS
        
        # Проверяем на TLS
        if data[0] == 0x16 and data[1:3] in [b'\x03\x01', b'\x03\x02', b'\x03\x03']:
            return DPIStrategy.FAKE_TLS
        
        # Проверяем на QUIC
        if data[0] & 0x80 and (data[0] & 0x30) == 0x00:
            return DPIStrategy.FAKE_QUIC
        
        # Проверяем на HTTP
        if b'HTTP' in data[:10] or b'GET' in data[:10] or b'POST' in data[:10]:
            return DPIStrategy.HOST_FAKE_SPLIT
        
        # По умолчанию - MULTISPLIT
        return DPIStrategy.MULTISPLIT
    
    def _apply_fake_tls(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии FAKE TLS"""
        config = self.strategy_configs[DPIStrategy.FAKE_TLS]
        
        if params and 'sni' in params:
            sni = params['sni']
        else:
            sni = "www.google.com"
        
        # Генерируем фейковый TLS ClientHello
        fake_tls = self._generate_tls_client_hello(sni)
        
        # Определяем сколько раз повторить
        repeats = params.get('repeats', config['repeats'])
        
        # Для TCP пакетов вставляем фейковый TLS перед данными
        result = b''
        for _ in range(repeats):
            result += fake_tls
        
        # Добавляем оригинальные данные
        result += data
        
        # Применяем дополнительные техники обмана
        if 'fooling' in config and 'ts' in config['fooling']:
            result = self._apply_timestamp_fooling(result)
        
        return result
    
    def _apply_fake_quic(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии FAKE QUIC"""
        config = self.strategy_configs[DPIStrategy.FAKE_QUIC]
        
        # Генерируем фейковый QUIC пакет
        fake_quic = self._generate_quic_initial()
        
        repeats = params.get('repeats', config['repeats'])
        
        result = b''
        for _ in range(repeats):
            result += fake_quic
        
        result += data
        
        # Применяем TTL манипуляции
        if config.get('autottl'):
            result = self._apply_ttl_manipulation(result, config['autottl'])
        
        return result
    
    def _apply_multisplit(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии MULTISPLIT"""
        config = self.strategy_configs[DPIStrategy.MULTISPLIT]
        
        split_seqovl = params.get('split_seqovl', config.get('split_seqovl', 681))
        split_pos = params.get('split_pos', config.get('split_pos', 1))
        
        # Разбиваем данные на части
        parts = []
        pos = 0
        data_len = len(data)
        
        while pos < data_len:
            # Определяем размер части
            part_size = min(split_seqovl, data_len - pos)
            
            # Извлекаем часть
            part = data[pos:pos + part_size]
            
            # Применяем смещение если нужно
            if split_pos > 1 and len(parts) > 0:
                # Добавляем overlap с предыдущей частью
                overlap = min(split_pos, len(parts[-1]))
                part = parts[-1][-overlap:] + part
            
            parts.append(part)
            pos += part_size
        
        # Собираем обратно с дополнительными заголовками
        result = b''
        for i, part in enumerate(parts):
            # Добавляем номер последовательности
            seq_header = struct.pack('!I', i)
            result += seq_header + part
            
            # Добавляем дублирование если нужно
            if config.get('repeats', 1) > 1:
                for _ in range(config['repeats'] - 1):
                    result += seq_header + part
        
        return result
    
    def _apply_host_fake_split(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии HOST FAKE SPLIT"""
        config = self.strategy_configs[DPIStrategy.HOST_FAKE_SPLIT]
        
        # Извлекаем хост из параметров
        if params and 'mod' in params:
            mod_parts = params['mod'].split('=')
            if len(mod_parts) > 1 and mod_parts[0] == 'host':
                fake_host = mod_parts[1]
            else:
                fake_host = "ozon.ru"
        else:
            fake_host = config.get('mod', 'host=ozon.ru').split('=')[1]
        
        # Для HTTP трафика подменяем Host header
        if b'Host:' in data:
            # Находим и заменяем Host header
            host_start = data.find(b'Host:')
            host_end = data.find(b'\r\n', host_start)
            
            if host_end > host_start:
                original_host_line = data[host_start:host_end]
                new_host_line = f"Host: {fake_host}".encode('utf-8')
                
                result = data[:host_start] + new_host_line + data[host_end:]
            else:
                result = data
        else:
            # Для HTTPS подменяем SNI в TLS
            result = self._apply_fake_tls(data, {'sni': fake_host})
        
        # Применяем дополнительные техники обмана
        if 'fooling' in config:
            for fooling_tech in config['fooling']:
                if fooling_tech == 'ts':
                    result = self._apply_timestamp_fooling(result)
                elif fooling_tech == 'md5sig':
                    result = self._apply_md5_signature(result)
        
        return result
    
    def _apply_syndata(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии SYNDATA"""
        # Генерируем синтетические данные для заполнения
        syn_data = random.randbytes(random.randint(100, 500))
        
        # Вставляем синтетические данные перед реальными
        result = syn_data + data
        
        # Добавляем случайные задержки между пакетами
        if params and params.get('add_delay'):
            delay_header = struct.pack('!I', random.randint(1, 100))
            result = delay_header + result
        
        return result
    
    def _apply_fake_dsplit(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии FAKE DSPLIT"""
        # Комбинация FAKE и DSPLIT
        fake_part = self._generate_tls_client_hello()
        
        # Разбиваем данные
        split_point = min(len(data) // 2, 500)
        part1 = data[:split_point]
        part2 = data[split_point:]
        
        # Чередуем фейковые и реальные части
        result = fake_part + part1 + fake_part + part2
        
        return result
    
    def _apply_multidisorder(self, data: bytes, params: Optional[Dict[str, Any]]) -> bytes:
        """Применение стратегии MULTIDISORDER"""
        # Разбиваем на части и перемешиваем порядок
        part_size = 100
        parts = [data[i:i+part_size] for i in range(0, len(data), part_size)]
        
        # Перемешиваем части
        random.shuffle(parts)
        
        # Добавляем номер последовательности к каждой части
        result = b''
        for i, part in enumerate(parts):
            seq_num = struct.pack('!H', i)
            result += seq_num + part
        
        return result
    
    def _apply_timestamp_fooling(self, data: bytes) -> bytes:
        """Добавление манипуляций с временными метками"""
        # Добавляем фейковые TCP timestamp options
        timestamp_option = b'\x08\x0a' + struct.pack('!II', 
            int(time.time() * 1000), 
            int(time.time() * 1000) - 1000
        )
        
        # Вставляем в начало пакета
        return timestamp_option + data
    
    def _apply_md5_signature(self, data: bytes) -> bytes:
        """Добавление MD5 подписи"""
        # Создаём MD5 хэш от данных
        md5_hash = hashlib.md5(data).digest()
        
        # Добавляем как заголовок
        return md5_hash + data
    
    def _apply_ttl_manipulation(self, data: bytes, ttl_value: int) -> bytes:
        """Манипуляции с TTL (Time To Live)"""
        # Для IP пакетов можно манипулировать TTL полем
        # В упрощённой реализации добавляем TTL как заголовок
        ttl_header = struct.pack('!B', ttl_value)
        return ttl_header + data
    
    def create_proxy_server(self, listen_port: int, target_host: str, 
                           target_port: int, strategy: DPIStrategy):
        """Создание прокси-сервера с обходом DPI"""
        
        class DPIProxyServer:
            def __init__(self, bypass_engine, strategy):
                self.bypass = bypass_engine
                self.strategy = strategy
                self.running = False
                self.server_socket = None
            
            def start(self, listen_port, target_host, target_port):
                self.running = True
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(('127.0.0.1', listen_port))
                self.server_socket.listen(5)
                
                print(f"DPI Proxy запущен на порту {listen_port}")
                
                while self.running:
                    try:
                        client_socket, addr = self.server_socket.accept()
                        thread = threading.Thread(
                            target=self.handle_client,
                            args=(client_socket, target_host, target_port)
                        )
                        thread.daemon = True
                        thread.start()
                    except:
                        break
            
            def handle_client(self, client_socket, target_host, target_port):
                try:
                    # Получаем данные от клиента
                    client_data = client_socket.recv(4096)
                    
                    if client_data:
                        # Применяем DPI обход
                        bypassed_data = self.bypass.apply_strategy(
                            client_data, self.strategy
                        )
                        
                        # Устанавливаем соединение с целевым сервером
                        remote_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        remote_socket.connect((target_host, target_port))
                        
                        # Отправляем модифицированные данные
                        remote_socket.send(bypassed_data)
                        
                        # Проксируем данные в обе стороны
                        self._proxy_loop(client_socket, remote_socket)
                
                except Exception as e:
                    print(f"Ошибка обработки клиента: {e}")
                finally:
                    client_socket.close()
            
            def _proxy_loop(self, client_socket, remote_socket):
                """Проксирование данных между клиентом и сервером"""
                sockets = [client_socket, remote_socket]
                
                while self.running:
                    try:
                        # Используем select для мультиплексирования
                        readable, _, _ = select.select(sockets, [], [], 1)
                        
                        for sock in readable:
                            data = sock.recv(4096)
                            
                            if not data:
                                return
                            
                            if sock is client_socket:
                                # Данные от клиента - применяем DPI обход
                                bypassed_data = self.bypass.apply_strategy(data, self.strategy)
                                remote_socket.send(bypassed_data)
                            else:
                                # Данные от сервера - отправляем как есть
                                client_socket.send(data)
                    
                    except:
                        break
            
            def stop(self):
                self.running = False
                if self.server_socket:
                    self.server_socket.close()
        
        # Создаём и возвращаем экземпляр прокси
        proxy = DPIProxyServer(self, strategy)
        return proxy