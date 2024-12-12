import os
import importlib.util
import random
import tarfile
import yaml

from Crypto.PublicKey import RSA


def generate_keys():
    # Генерация пары ключей
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

def get_plugins():
    plugins = {}
    plugins_dir = './plugins'
    for item in os.listdir(plugins_dir):
        item_path = os.path.join(plugins_dir, item)
        if os.path.isdir(item_path):
            manifest_path = os.path.join(item_path, 'manifest.py')
            if os.path.exists(manifest_path):
                spec = importlib.util.spec_from_file_location("manifest", manifest_path)
                manifest = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(manifest)
                if hasattr(manifest, 'NAME'):
                    plugins[manifest.NAME] = item_path
    return plugins


def create_archive(selected_plugins, config):
    with tarfile.open('config.tar.xz', 'w:xz') as tar:
        for plugin in selected_plugins:
            tar.add(plugin, arcname=os.path.join('plugins', os.path.basename(plugin)))

        # Создаем пустые файлы для будущего добавления
        private_key, public_key = generate_keys()
        # print(public_key, private_key)
        with open("rsa_key.pub", "wb") as f:
            f.write(public_key)

        with open(f"certificates/rsa_key_{config['id']}", "wb") as f:
            f.write(private_key)

        with open("config.yaml", "wt") as f:
            yaml.safe_dump(config, stream=f)

        # open('key_123.pub', 'w').close()
        # open('config.yaml', 'w').close()

        tar.add('rsa_key.pub')
        tar.add('config.yaml')

    # Удаляем не нужные на обработчике файлы
    os.remove('rsa_key.pub')
    os.remove('config.yaml')


def main():


    plugins = get_plugins()

    print("Доступные плагины:")
    for i, (name, path) in enumerate(plugins.items(), 1):
        print(f"{i}. {name}")

    selected_indices = input("Выберите номера плагинов (через запятую): ").split(',')
    selected_plugins = [list(plugins.values())[int(i.strip()) - 1] for i in selected_indices]


    config = {
        'id': random.randint(1, 1_000_000),
        'mq_server_address': input("Адрес MQ сервера [127.0.0.1]: ") or '127.0.0.1',
        'mq_server_port': int(input("Порт MQ сервера  [9092]:",) or '9092'),
        'send_data_interval': int(input("Интервал отправки [300]:",) or '300'),
        'also_store_local': True,
        'required_plugins': [list(plugins.keys())[int(i.strip()) - 1] for i in selected_indices]

    }
    print()
    print("Конфигурация:")
    for key in config:
        print(f"{key}: {config[key]}")
    if input("Сохранить конфигурацию? [y/N]").upper() in ('Y', "YES", "ДА"):
        create_archive(selected_plugins, config)
        print("config.tar.xz создан успешно.")
    else:
        print("Отменено.")

if __name__ == "__main__":
    main()
