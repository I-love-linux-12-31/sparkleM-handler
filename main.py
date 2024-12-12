# SparkleM handler
# dec 2024 Yaroslav Kuznetsov
import datetime
import importlib
import json
import base64
import os.path
import os

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

from confluent_kafka import Consumer, KafkaException, KafkaError

import sparkleM_core


os.environ["SPARKLE_M_SERVER"] = "1"

session: sparkleM_core.Session = None


# Конфигуратор Consumer Kafka
def kafka_consumer_config():
    return {
        'bootstrap.servers': '172.16.0.2:9092',  # Укажите адрес вашего брокера Kafka
        'group.id': 'handlers',  # Укажите уникальное имя для группы потребителей
        # 'auto.offset.reset': 'earliest'  # Начать с самого первого сообщения
    }


plugins = {}
plugins_dir = './plugins'
PLUGIN_REQUIRED_ATTRS = ["NAME", "VERSION", "AUTHOR", "DataFrame"]


def reload_plugins():
    global plugins
    plugins.clear()

    for package_name in os.listdir(plugins_dir):
        package_path = os.path.join(plugins_dir, package_name)
        if os.path.isdir(package_path):
            try:
                package = importlib.import_module(f'plugins.{package_name}')

                if all({hasattr(package, attr) for attr in PLUGIN_REQUIRED_ATTRS}):
                    if package.NAME in plugins:
                        print(F"[\033[33mWARN\033[0m]: Обнаружен плагин, с уже занятым именем, но отличным пакетом. Будет использована более новая версия плагина(согласно манифесту)")
                        if plugins[package.NAME].VERSION <= package.VERSION:
                            plugins[package.NAME] = package
                    else:
                        plugins[package.NAME] = package
                    print(f"+ {package.NAME}, {package.VERSION} от {package.AUTHOR}")
                else:
                    print(f"В пакете {package_name} отсутствует один из обязательных аттрибутов: "
                          f"{', '.join(attr for attr in PLUGIN_REQUIRED_ATTRS if not hasattr(package, attr))}")
            except ImportError as e:
                print(f"Не удалось импортировать пакет {package_name}: {e}")
            except AttributeError as e:
                print(f"В пакете {package_name} отсутствует аттрибут или манифест некорректен: {e}")
            except Exception as e:
                print(f"При загрузке пакета {package_name} произошла ошибка: {e}")
    print("Импортированные плагины:", plugins)




# Функция для обработки полученного сообщения
def process_message(message):
    # Декодируем сообщение из JSON
    decoded_message = json.loads(message)

    # Декодируем payload из base64 обратно в байты
    payload = base64.b64decode(decoded_message['payload'].encode('utf-8'))
    key_name = F"certificates/rsa_key_{decoded_message['config_id']}"
    if os.path.exists(key_name):
        with open(key_name, 'rb') as key_file:
            private_key = key_file.read()

            key = RSA.import_key(private_key)
            cipher = PKCS1_OAEP.new(key)
            decrypted_message = cipher.decrypt(payload)
            decoded_payload =  json.loads(decrypted_message.decode())

            dt = datetime.datetime.fromisoformat(decoded_message["datetime"])
            if decoded_payload['plugin'] in plugins:
                plugins[decoded_payload['plugin']].server.add_dataframe(
                    dt,
                    decoded_message['hostname'],
                    decoded_payload['key'],
                    decoded_payload['value'],
                    session=session
                )
            else:
                print(F"[\033[31mERR\033[0m] Плагин {decoded_payload['plugin']} не установлен. Невозможно обработать данные!")

    else:
        print("Bad config id: ", decoded_message['config_id'])
        decoded_payload = None


    # Печатаем декодированное сообщение (Для отладки)
    print("Received message:")
    print(f"Config ID: {decoded_message['config_id']}")
    print(f"Hostname: {decoded_message['hostname']}")
    print(f"Datetime: {decoded_message['datetime']}")
    print(f"Decoded Payload: {decoded_payload}")


# Функция для получения сообщений из Kafka
def consume_from_kafka():
    # Создаем Consumer
    consumer = Consumer(kafka_consumer_config())

    # Подписываемся на топик
    consumer.subscribe(['telemetry'])

    try:
        while True:
            # Получаем сообщение
            msg = consumer.poll(timeout=1.0)  # Ожидаем максимум 1 секунду

            if msg is None:
                # Если нет сообщений, продолжаем ожидать
                continue
            if msg.error():
                # Если ошибка, выводим её
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    print(f"End of partition reached: {msg.topic()}/{msg.partition()} [{msg.offset()}]")
                else:
                    raise KafkaException(msg.error())
            else:
                # Обрабатываем полученное сообщение
                process_message(msg.value().decode('utf-8'))  # Декодируем байты в строку UTF-8
                # break  # Выход из цикла после получения одного сообщения
                session.commit()

    except KeyboardInterrupt:
        print("Выход...")
    finally:
        # Завершаем работу consumer
        consumer.close()


def main():
    global session

    reload_plugins()

    class AllModules:
        def __init__(self):
            self._attributes = {}

        def __setattr__(self, name, value):
            if name == '_attributes':
                super().__setattr__(name, value)
            else:
                self._attributes[name] = value

        def __getattr__(self, name):
            return self._attributes.get(name, None)

        def __str__(self):
            return str(self._attributes)

    __all_modules = AllModules()  # Используемые классы для SQLAlchemy
    for pkg in plugins.values():
        setattr(__all_modules, F"{pkg.NAME}_DataFrame", pkg.server.DataFrame)

    sparkleM_core.global_init("db.sqlite3", __all_modules)
    session = sparkleM_core.create_session()

    # Запуск получения сообщений
    consume_from_kafka()


if __name__ == '__main__':
    main()
