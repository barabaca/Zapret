#!/data/data/com.termux/files/usr/bin/bash
# Полная установка и тестирование в Termux

echo "=========================================="
echo "   Zapret Android - Полное тестирование   "
echo "=========================================="

# Обновление Termux
echo "[1] Обновление Termux..."
pkg update -y && pkg upgrade -y

# Установка зависимостей
echo "[2] Установка зависимостей..."
pkg install -y \
    python \
    git \
    cmake \
    make \
    clang \
    wget \
    curl \
    net-tools \
    proot \
    termux-api \
    termux-tools

# Установка Python библиотек
echo "[3] Установка Python библиотек..."
pip install --upgrade pip
pip install \
    kivy \
    buildozer \
    cython \
    requests \
    flask \
    psutil \
    scapy \
    pillow \
    pytest

# Клонирование проекта
echo "[4] Клонирование проекта..."
cd ~
if [ -d "zapret-android" ]; then
    echo "Удаление старой версии..."
    rm -rf zapret-android
fi

cd zapret-android

# Установка прав
echo "[5] Установка прав..."
chmod +x *.py
chmod +x scripts/*.sh

echo "[X] Генерация иконок..."
if [ ! -f "assets/icon.png" ]; then
    echo "Иконки не найдены, запускаю генератор..."
    pip install Pillow
    python icon_generator.py
else
    echo "Иконки уже существуют, пропускаю..."
fi

# Создание директорий
echo "[6] Создание структуры проекта..."
mkdir -p assets lists bin logs

# Создание иконки
echo "[7] Создание ресурсов..."
cat > assets/icon.png.base64 << 'EOF'
# Здесь будет base64 иконки
EOF

base64 -d assets/icon.png.base64 > assets/icon.png

# Запуск тестов
echo "[8] Запуск модульных тестов..."
python -m pytest tests/ -v --tb=short

# Тестирование стратегий
echo "[9] Тестирование стратегий обхода..."
python test_strategies.py --all

# Тестирование производительности
echo "[10] Тестирование производительности..."
python benchmark.py --time 30

# Создание APK
echo "[11] Подготовка к сборке APK..."
if [ -f "buildozer.spec" ]; then
    echo "Настройка buildozer..."
    buildozer init
    sed -i 's/# title = My Application/title = Zapret Android/' buildozer.spec
    sed -i 's/# package.name = myapp/package.name = zapretandroid/' buildozer.spec
    sed -i 's/# orientation = portrait/orientation = portrait/' buildozer.spec
    sed -i 's/# requirements = python3,kivy/requirements = python3,kivy,requests,psutil/' buildozer.spec
    
    echo "Сборка debug APK..."
    buildozer android debug
else
    echo "Файл buildozer.spec не найден!"
fi

# Генерация отчёта
echo "[12] Генерация отчёта..."
python generate_report.py --format html

echo ""
echo "=========================================="
echo "          ТЕСТИРОВАНИЕ ЗАВЕРШЕНО         "
echo "=========================================="
echo ""
echo "Результаты:"
echo "1. APK файл: ~/zapret-android/bin/zapretandroid-0.1-debug.apk"
echo "2. Отчёт: ~/zapret-android/test_report.html"
echo "3. Логи: ~/zapret-android/logs/"
echo ""
echo "Для установки APK на устройство:"
echo "adb install bin/zapretandroid-0.1-debug.apk"
echo ""
echo "Для запуска в Termux:"
echo "cd ~/zapret-android && python main.py"