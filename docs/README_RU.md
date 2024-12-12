# Обработчик для Sparkle-M

Приложения для получения и обработки собранных данных

## Доступные плагины
1. [Temperature]() - для сбора показателей с датчиков температуры.
2. [PU_Workload]() - для сбора показателей загруженности вычислительных мощностей.

## Зависимости
* `pycryptodome`
* `requests`
* `confluent-kafka`
* `SQLAlchemy`

## Запуск
```bash
# Создание виртуального окружения
python3 -m venv venv
# Активация окружения
source venv/bin/activate
# Устаноака зависимостей
pip3 install -r requirements.txt
# запуск
python3 main.py
```

### Организация файлов проекта
#### Файловая структура агента:
* `plugins` - каталог пакетов с плагинами.
* `Certificates` - каталог приватных RSA ключей.
* `sparkleM_core` - модуль для работы с БД.
* `main.py` - основной код программы.
* `requirements.py` - зависимости.

#### Файловая структура плагина:
* `__init__.py` - содержит импорт нужных для агента функций под нужными(стандартизированными) именами. 
* `manifest.py` - файл манифеста. Содержит информацию о плагине.
* `requirements.txt` - файл со списком зависимостей.
* `server.py` - Код плагина для сервера.
* `main.py` - код модуля (файлов может быть больше, и их имена могут быть любыми).

## Работа с БД

По умолчанию используется база данных sqlite3 (db.sqlite3 в каталоге проекта) 