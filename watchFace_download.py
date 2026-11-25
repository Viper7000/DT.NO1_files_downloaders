# -*- coding: utf-8 -*-
import os
import json
import secrets
from urllib.parse import urlparse
import requests

# === ЗАДАЙТЕ ВАШИ НОМЕРА ЗДЕСЬ ===
NUMBERS_LIST = [88237, 88050]
# Можно указывать как числами, так и строками ["88000", "88001"]

TOKEN_FILE = "token.json"
LOGIN_URL = "https://dt1pro.wanruxia.com/xky-api/login/anonymous"
LIST_URL_TEMPLATE = "https://dt1pro.wanruxia.com/xky-api/watchFace/adapter/10/{model}"


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


def extract_watchfaces_list(raw_data) -> list:
    """Извлекает список словарей с циферблатами из ответа API."""
    if isinstance(raw_data, list):
        return raw_data
    if isinstance(raw_data, dict):
        data_field = raw_data.get("data")
        if isinstance(data_field, list):
            return data_field
        if isinstance(data_field, dict):
            for key in ("list", "records", "rows", "items"):
                if isinstance(data_field.get(key), list):
                    return data_field[key]
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


def format_names(file_name: str, preview_url: str) -> tuple[str, str]:
    """
    Формирует имена для превью и файла циферблата:
    - Превью: убираем всё начиная с '_', добавляем расширение из preview_url -> Clock5285.png
    - Файл: убираем всё после 'res' (без расширения) -> Clock5285_res
    """
    # Имя картинки
    base_prefix = file_name.split("_")[0]
    parsed_path = urlparse(preview_url).path
    _, preview_ext = os.path.splitext(parsed_path)
    if not preview_ext:
        preview_ext = ".png"
    img_name = f"{base_prefix}{preview_ext}"

    # Имя основного файла
    if "res" in file_name:
        res_idx = file_name.index("res")
        wf_name = file_name[:res_idx + 3]
    else:
        wf_name = os.path.splitext(file_name)[0]

    return img_name, wf_name


def process_model(model: str, token: str):
    """Скачивает список, циферблаты и формирует отчет для одной модели."""
    model_str = str(model).strip()
    print(f"\n================ МОДЕЛЬ: {model_str} ================")

    url = LIST_URL_TEMPLATE.format(model=model_str)
    headers = {"token": token}

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        raw_json = resp.json()
    except Exception as e:
        print(f"[!] Не удалось получить список для модели {model_str}: {e}")
        return

    # Сохраняем список в list_<модель>.json
    list_filename = f"list_{model_str}.json"
    with open(list_filename, "w", encoding="utf-8") as f:
        json.dump(raw_json, f, ensure_ascii=False, indent=4)
    print(f"[+] Список сохранен в {list_filename}")

    watchfaces = extract_watchfaces_list(raw_json)
    if not watchfaces:
        print(f"[!] Список циферблатов для модели {model_str} пуст или имеет неизвестную структуру.")
        return

    # Создаем папку модели
    os.makedirs(model_str, exist_ok=True)
    manifest_filename = f"manifest_{model_str}.txt"
    downloaded_count = 0

    with open(manifest_filename, "w", encoding="utf-8") as manifest:
        total_items = len(watchfaces)
        for idx, wf in enumerate(watchfaces, start=1):
            file_name = wf.get("fileName", "")
            preview_url = wf.get("preview", "")
            file_url = wf.get("file", "")
            file_size = wf.get("fileSize", 0)
            installs = wf.get("installs", 0)

            if not file_name or not file_url:
                continue

            img_name, wf_name = format_names(file_name, preview_url)
            img_path = os.path.join(model_str, img_name)
            wf_path = os.path.join(model_str, wf_name)

            print(f"[{idx}/{total_items}] {wf_name} ({img_name})...")

            if preview_url:
                download_binary(preview_url, img_path)

            if download_binary(file_url, wf_path):
                downloaded_count += 1
                # 20 символов название (влево), 10 символов размер (вправо), 8 символов installs (вправо)
                line = f"{wf_name:<20}{file_size:>10}{installs:>8}\n"
                manifest.write(line)

        manifest.write("--------------------------------------\n")
        manifest.write(f"Total files: {downloaded_count}\n")

    print(f"[+] Готово! Скачано файлов: {downloaded_count}. Отчет: {manifest_filename}")


def main():
    try:
        token = get_token()
    except Exception as e:
        print(f"[КРИТИЧЕСКАЯ ОШИБКА] Не удалось получить токен: {e}")
        return

    for model in NUMBERS_LIST:
        process_model(model, token)

    print("\nВсе задачи выполнены.")


if __name__ == "__main__":
    main()
