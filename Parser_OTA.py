# pip install requests

import json
import time
import requests

# === НАСТРОЙКИ ===
START_NUMBER = 88000  # Начальный номер
END_NUMBER = 88450  # Конечный номер (включительно)
OUTPUT_FILE = "firmware_upd.txt"  # Имя итогового файла
DELAY = 1.2  # Задержка между запросами в секундах (чтобы сервер не заблокировал)
# =================

BASE_URL = "https://dt1pro.wanruxia.com/xky-api/firmware/checkUpdate?devicePlan=10&number={}"


def scan_firmware():
    print(f"Запуск сканирования диапазонов от {START_NUMBER} до {END_NUMBER}...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        # +1 нужен, чтобы конечный номер тоже попал в проверку
        for number in range(START_NUMBER, END_NUMBER + 1):
            url = BASE_URL.format(number)

            try:
                response = requests.get(url, timeout=10)

                # Проверяем успешность самого HTTP-запроса
                if response.status_code != 200:
                    print(
                        f"[{number}] Ошибка сервера. Код: {response.status_code}"
                    )
                    continue

                response_json = response.json()
                data = response_json.get("data")

                # Если data равна null (в Python это None) — пропускаем
                if data is None:
                    print(f"[{number}] Нет данных (data: null)")
                    continue

                # Извлекаем нужные поля (если какого-то поля нет, запишется пустая строка)
                name = data.get("name", "")
                version = data.get("version", "")
                update_time = data.get("updateTime", "")
                file_size = data.get("fileSize", "")

                # Формируем строку строго в заданном формате
                line = f'[{number}]  {name:12}   {version:12}  {update_time}   {file_size}\n'

                # Записываем в файл и выводим лог в консоль
                f.write(line)
                print(f"[{number}] Найдено! Добавлено в файл: {line.strip()}")

            except requests.exceptions.RequestException as e:
                print(f"[{number}] Ошибка сети при запросе: {e}")
            except json.JSONDecodeError:
                print(f"[{number}] Ошибка: сервер вернул не JSON формат")

            # Небольшая пауза между запросами
            time.sleep(DELAY)

    print(f"\nСканирование завершено. Результаты сохранены в {OUTPUT_FILE}")


if __name__ == "__main__":
    scan_firmware()
