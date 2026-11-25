import os
import requests

# === ЗАДАЙТЕ ВАШИ НОМЕРА ЗДЕСЬ ===
NUMBERS_LIST = [88237, 88359]  
# Можно указывать как числами, так и строками ["88000", "88001"]

# Конфигурация
URL_TEMPLATE = "https://dt1pro.wanruxia.com/xky-api/firmware/checkUpdate?devicePlan=10&number={}"
OUTPUT_DIR = "downloads"

# Создаем папку для скачивания, если ее нет
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def process_numbers():
    print(f"Найдено номеров для обработки: {len(NUMBERS_LIST)}")

    for num in NUMBERS_LIST:
        api_url = URL_TEMPLATE.format(num)
        print(f"\n[+] Обработка номера: {num}")
        
        try:
            # 1. Запрос к API для получения JSON
            response = requests.get(api_url, timeout=10)
            
            if response.status_code != 200:
                print(f"    Ошибка API (Статус: {response.status_code})")
                continue
                
            data = response.json()
            
            # Проверяем успешность ответа от сервера (зависит от структуры вашего API)
            # Если структура отличается, скорректируйте ключи данных ниже
            if not data or "data" not in data:
                # Если данные лежат в корне JSON:
                res_data = data
            else:
                # Если данные лежат внутри объекта {"data": {...}}
                res_data = data.get("data", {})

            # Извлекаем ссылки и имена файлов
            file_url = res_data.get("file") or res_data.get("fileUrl")
            origin_name = res_data.get("originFileName") or res_data.get("fileName")

            if not file_url or not origin_name:
                print(f"    Предупреждение: Для номера {num} обновления или файлы не найдены.")
                continue

            # Полный путь к файлу на диске
            file_path = os.path.join(OUTPUT_DIR, origin_name)

            # === ПРОВЕРКА НА СУЩЕСТВОВАНИЕ ФАЙЛА ===
            if os.path.exists(file_path):
                print(f"    [Пропущено] Файл '{origin_name}' уже скачан ранее.")
                continue

            # 2. Скачивание .bin файла
            print(f"    Найден файл: {origin_name}")
            print(f"    Скачивание...")
            
            file_response = requests.get(file_url, stream=True, timeout=30)
            if file_response.status_code == 200:
                file_path = os.path.join(OUTPUT_DIR, origin_name)
                
                with open(file_path, "wb") as bin_file:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        bin_file.write(chunk)
                        
                print(f"    [Успешно] Сохранен как: {file_path}")
            else:
                print(f"    Ошибка при скачивании файла (Статус: {file_response.status_code})")

        except requests.exceptions.RequestException as e:
            print(f"    Ошибка сети/запроса: {e}")
        except ValueError:
            print("    Ошибка: Ответ сервера не является валидным JSON")
        except Exception as e:
            print(f"    Произошла непредвиденная ошибка: {e}")

if __name__ == "__main__":
    process_numbers()
