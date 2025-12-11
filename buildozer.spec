[app]

# Название приложения
title = Zapret Android

# Имя пакета (домен в обратном порядке)
package.name = com.zapret.android

# Имя домена
package.domain = com.zapret

# Версия приложения
version = 1.0.0

# Номер версии для маркета
version.code = 1

# Автор
author = Zapret Team

# Ориентация экрана
orientation = portrait

# Требуемая версия Android
android.api = 29
android.minapi = 21
android.ndk = 23b
android.sdk = 34

# Разрешения
android.permissions = INTERNET, ACCESS_NETWORK_STATE, ACCESS_WIFI_STATE
android.gradle_dependencies = 'com.android.support:appcompat-v7:28.0.0'

# Разрешения без запроса (для VPN)
android.allow_backup = True
android.usesCleartextTraffic = True

# Требования
requirements = python3, kivy, requests, psutil

# Иконка
icon.filename = assets/icon.png

# Заставка
presplash.filename = assets/presplash.png

# Исходный код
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,txt

# Главный файл
source.main = main.py

# Исключения
source.exclude_exts = spec,pyc

# Размеры окон
fullscreen = 0
resizable = 1
window.resizeable = 1

# Логирование
log_level = 2
log_filter = python

# Пакет выпуска
android.accept_sdk_license = True
android.release_artifact = .apk

# Архитектура
android.arch = arm64-v8a, armeabi-v7a

# Включение служб
android.allow_backup = true
android.usesCleartextTraffic = true

# Подпись (автогенерация)
android.sign = True
android.release_artifact = zapret-android-release.apk

# Оптимизация
android.add_compiler_flags = -O3
android.add_gradle_repositories = maven { url 'https://jitpack.io' }

# Дополнительные файлы
include_exts = json,txt

# Билд с отладочной информацией
# (закомментировать для релиза)
# build_type = debug