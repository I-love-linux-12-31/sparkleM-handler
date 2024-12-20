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
* `PyYAML`

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
#### Файловая структура обработчика:
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

Поддерживаемые базы данных:
* sqlite3 [по умолчанию]
* mysql
* oracle
* postgresql
* ...

При использовании других БД, может понадобиться установить доп зависимости для SQLAlchemy 
(например psycopg2 для postgresql). Подробнее можно прочитать в [документации к SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html)

По умолчанию используется база данных sqlite3 (db.sqlite3 в каталоге проекта)

Параметры БД указаны в файле SparkleM_core.py
```python
conn_str = f'sqlite:///{db_file.strip()}?check_same_thread=False'
```
Строка должна иметь вид ``dialect[+driver]://user:password@host/dbname[?key=value..]``


## Развёртывание kafka 

В примере указан адрес сервера как 172.16.0.2

**docker-compose.yaml**
```yaml
version: '2.1'

services:
  zoo1:
    image: confluentinc/cp-zookeeper:7.3.2
    hostname: zoo1
    container_name: zoo1
    ports:
      - "2181:2181"
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_SERVER_ID: 1
      ZOOKEEPER_SERVERS: zoo1:2888:3888

  kafka1:
    image: confluentinc/cp-kafka:7.3.2
    hostname: kafka1
    container_name: kafka1
    ports:
      - "9092:9092"
      - "29092:29092"
      - "9999:9999"
    environment:
      KAFKA_ADVERTISED_LISTENERS: INTERNAL://kafka1:19092,EXTERNAL://172.16.0.2:9092,DOCKER://host.docker.internal:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: INTERNAL:PLAINTEXT,EXTERNAL:PLAINTEXT,DOCKER:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
      KAFKA_ZOOKEEPER_CONNECT: "zoo1:2181"
      KAFKA_BROKER_ID: 1
      KAFKA_LOG4J_LOGGERS: "kafka.controller=INFO,kafka.producer.async.DefaultEventHandler=INFO,state.change.logger=INFO"
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_JMX_PORT: 9999
      KAFKA_JMX_HOSTNAME: 172.16.0.2
      KAFKA_AUTHORIZER_CLASS_NAME: kafka.security.authorizer.AclAuthorizer
      KAFKA_ALLOW_EVERYONE_IF_NO_ACL_FOUND: "true"
    depends_on:
      - zoo1
```

## Добавление конфигурации
1. Воспользуйтесь утилитой gen_config.py 
```bash
python3 gen_config.py
```
2. Поместите config.tar.xz в папку агента
3. Перезапустите/запустите агент
