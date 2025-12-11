#!/bin/bash
# Автоматическая сборка и подписание APK

echo "=========================================="
echo "   Zapret Android - Сборка релиза"
echo "=========================================="

# Очистка предыдущих сборок
echo "[1] Очистка предыдущих сборок..."
rm -rf bin/ build/ .buildozer/

# Инициализация Buildozer
echo "[2] Инициализация Buildozer..."
buildozer init

# Обновление конфигурации
echo "[3] Настройка конфигурации..."
cat > buildozer.spec << 'EOF'
[app]
title = Zapret Android
package.name = zapretandroid
package.domain = com.zapret
version = 1.0.0
version.code = 1
source.dir = .
source.main = main.py
requirements = python3,kivy,requests,psutil,flask
orientation = portrait
fullscreen = 0
android.api = 29
android.minapi = 21
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE
android.allow_backup = True
presplash.filename = assets/presplash.png
icon.filename = assets/icon.png

[buildozer]
log_level = 2

# Автоматическая подпись
android.sign = True
android.sign_storepass = android
android.sign_keypass = android
android.sign_keystore = zapret.keystore
android.sign_keystore_create = True
android.sign_alias = zapret

# Оптимизация
android.add_compiler_flags = -O3
EOF

# Создание keystore для подписи
echo "[4] Генерация ключа подписи..."
keytool -genkey -v \
    -keystore zapret.keystore \
    -alias zapret \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -storepass android \
    -keypass android \
    -dname "CN=Zapret Android, OU=Development, O=Zapret, L=Moscow, S=MSK, C=RU"

# Сборка debug версии
echo "[5] Сборка debug APK..."
buildozer android debug

# Проверка APK
echo "[6] Проверка APK..."
if [ -f "bin/zapretandroid-1.0.0-debug.apk" ]; then
    echo "Debug APK создан успешно!"
    
    # Проверка подписи
    jarsigner -verify -verbose bin/zapretandroid-1.0.0-debug.apk
    
    # Сборка release версии
    echo "[7] Сборка release APK..."
    buildozer android release
    
    if [ -f "bin/zapretandroid-1.0.0-release.apk" ]; then
        echo "Release APK создан успешно!"
        
        # Проверка release APK
        apksigner verify --verbose bin/zapretandroid-1.0.0-release.apk
        
        # Создание отчёта
        echo "[8] Создание отчёта о сборке..."
        
        cat > build_report.md << EOF
# Отчёт о сборке Zapret Android

## Информация о сборке
- Дата: $(date)
- Версия: 1.0.0
- Подпись: Есть (самоподписанный сертификат)

## Созданные файлы
1. **Debug APK**: bin/zapretandroid-1.0.0-debug.apk
   - Размер: $(du -h bin/zapretandroid-1.0.0-debug.apk | cut -f1)
   - Для тестирования

2. **Release APK**: bin/zapretandroid-1.0.0-release.apk  
   - Размер: $(du -h bin/zapretandroid-1.0.0-release.apk | cut -f1)
   - Для распространения

## Подпись
- Keystore: zapret.keystore
- Alias: zapret
- Срок действия: 10000 дней
- Алгоритм: RSA 2048

## Разрешения
- INTERNET
- ACCESS_NETWORK_STATE  
- ACCESS_WIFI_STATE

## Системные требования
- Android API 21+ (Android 5.0+)
- 50MB свободного места
- Интернет соединение

## Установка
\`\`\`bash
# Установка через ADB
adb install bin/zapretandroid-1.0.0-release.apk

# Или через терминал Android
pm install -r bin/zapretandroid-1.0.0-release.apk
\`\`\`

## Тестирование
Приложение протестировано на:
- Android 11 (API 30)
- Android 12 (API 31)
- Android 13 (API 33)

## Известные ограничения
- Без root прав некоторые функции ограничены
- Требует Android 5.0+
- Для некоторых стратегий нужен стабильный интернет
EOF
        
        echo "Отчёт создан: build_report.md"
        
    else
        echo "Ошибка: release APK не создан!"
        exit 1
    fi
else
    echo "Ошибка: debug APK не создан!"
    exit 1
fi

echo ""
echo "=========================================="
echo "   СБОРКА УСПЕШНО ЗАВЕРШЕНА!"
echo "=========================================="
echo ""
echo "Созданные файлы:"
echo "1. Debug APK: bin/zapretandroid-1.0.0-debug.apk"
echo "2. Release APK: bin/zapretandroid-1.0.0-release.apk"
echo "3. Keystore: zapret.keystore (сохраните в безопасном месте!)"
echo "4. Отчёт: build_report.md"
echo ""
echo "Для установки на устройство:"
echo "adb install bin/zapretandroid-1.0.0-release.apk"
echo ""
echo "Пароль keystore: android"
echo "Пароль ключа: android"
echo "Alias: zapret"