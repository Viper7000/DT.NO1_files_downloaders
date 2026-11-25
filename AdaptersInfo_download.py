# -*- coding: utf-8 -*-
import os
import re
import json
import secrets
from urllib.parse import urlparse
import requests

# === ЗАДАЙТЕ ВАШИ НОМЕРА ЗДЕСЬ ===
START_NUMBER = 88401  # Начальный номер, например 88000
END_NUMBER = 88500  # Конечный номер (включительно), например 88400


TOKEN_FILE = "token.json"
LOGIN_URL = "https://dt1pro.wanruxia.com/xky-api/login/anonymous"
LIST_URL_TEMPLATE = "https://dt1pro.wanruxia.com/xky-api/adapter/findByDevicePlanAndNumber?number={model}"


def get_token() -> str:
    """Читает токен из token.json или запрашивает новый у сервера."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("token"):
                    print("[+] Токен успешно загружен из token.json")
                    return data["token"]
        except Exception as e:
            print(f"[!] Ошибка чтения {TOKEN_FILE}: {e}. Получаем новый токен...")

    # Генерация случайного 8-байтного hex-идентификатора (16 символов)
    device_id = secrets.token_hex(8)
    payload = {
        "deviceUniqueId": device_id,
        "app": 189174,
        "appVersion": "1.2.7"
    }
    headers = {
        "Content-Type": "application/json;charset=utf-8"
    }

    print(f"[*] Запрос нового токена для deviceUniqueId: {device_id}...")
    response = requests.post(LOGIN_URL, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    res_json = response.json()

    if not res_json.get("success") or "data" not in res_json:
        raise RuntimeError(f"Сервер вернул ошибку авторизации: {res_json}")

    user_data = res_json["data"]
    token_data = {
        "deviceUniqueId": user_data.get("deviceUniqueId", device_id),
        "token": user_data["token"],
        "registerTime": user_data.get("registerTime", "")
    }

    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, separators=(",", ":"))

    print("[+] Новый токен получен и сохранен в token.json")
    return token_data["token"]


def extract_adapter_list(raw_data) -> list:
    """Извлекает список словарей с циферблатами из ответа API."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        data_field = raw_data.get("data")
        if isinstance(data_field, list):
            return data_field
        if isinstance(data_field, dict):
            return data_field
    return []


def download_binary(url: str, save_path: str) -> bool:
    """Скачивает файл по URL и сохраняет на диск."""
    if not url:
        return False
    try:
        resp = requests.get(url, stream=True, timeout=30)
        resp.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"    [!] Ошибка скачивания {url}: {e}")
        return False


def process_model(model: str, token: str, manifest):
    """Скачивает список, циферблаты и формирует отчет для одной модели."""
    model_str = str(model).strip()

    url = LIST_URL_TEMPLATE.format(model=model_str)
    headers = {"token": token}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        raw_json = resp.json()
    except Exception as e:
        print(f"[!] Не удалось получить список для модели {model_str}: {e}")
        return

    adapter = extract_adapter_list(raw_json)
    if not adapter:
        print(f"[!] Файл информации для модели {model_str} пуст или имеет неизвестную структуру.")
        return

    # Сохраняем список в adapter_<модель>.json
    list_filename = f"adapter_{model_str}.json"
    with open(list_filename, "w", encoding="utf-8") as f:
        json.dump(raw_json, f, ensure_ascii=False, indent=4)
    print(f"[+] Список сохранен в {list_filename}")

    number = adapter.get("number", 0)
    name = adapter.get("name", "none")
    icon_url = adapter.get("icon", "")
    wifi = adapter.get("wifi", False)
    nfc = adapter.get("nfc", False)
    maps = adapter.get("maps", False)
    
    wifi_str = "wifi" if wifi else "-"
    nfc_str = "nfc" if nfc else "-"
    maps_str = "maps" if maps else "-"
    
    # 1. Достаем строку из ключа "ext" (если ключа нет, берем пустой JSON "{}")
    # Если "ext" отсутствует, равен None или пустой строке "", подставится "{}"
    ext_str = adapter.get("ext") or "{}"
    # 2. Превращаем JSON-строку в обычный словарь Python
    ext_dict = json.loads(ext_str)
    # 3. Безопасно забираем вложенный словарь "watch" и нужные значения
    watch_data = ext_dict.get("watch", {})
    watch_width = watch_data.get("width", "---")    # "466"
    watch_height = watch_data.get("height", "---")  # "466"
    watch_type = watch_data.get("type", "---") # "round"
    
    # 1. Пытаемся найти совпадение с самого начала строки
    match = re.match(r'[a-zA-Z0-9_-]+', name)
    # 2. Если нашли — забираем текст, если нет — ставим запасное имя
    clean_name = match.group(0) if match else "unknown"
    img_name = f"{number}_{clean_name}.png"

    img_path = os.path.join("Pic", img_name)

    print(f"[{number}] {name}  {watch_width}x{watch_height}  {watch_type}")

    if icon_url:
        download_binary(icon_url, img_path)
        line = f"[{number}]  {name:<20}{watch_width:>3}x{watch_height:<3}  {watch_type:<10}{wifi_str:<6}{nfc_str:<6}{maps_str:<6}\n"
        manifest.write(line)


def main():
    try:
        token = get_token()
    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА] Не удалось получить токен: {e}")
        return

    os.makedirs("Pic", exist_ok=True)
    print(f"Запуск сканирования диапазонов от {START_NUMBER} до {END_NUMBER}...")
    manifest_filename = f"manifest.txt"
    
    with open(manifest_filename, "w", encoding="utf-8") as manifest:
        for model in range(START_NUMBER, END_NUMBER + 1):
            process_model(model, token, manifest)

    print("\nВсе задачи выполнены.")


if __name__ == "__main__":
    main()
