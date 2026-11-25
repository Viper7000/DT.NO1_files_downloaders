# DT.NO1_files_downloaders
Download files from server DT.NO1 (watch faces, OTA, watch specs)

## 1. watchFace_download.py

___Description___ The program downloads watch faces available in the WearJoy app for a specific watch model (or multiple models).

___Usage:___ You need to enter the model numbers for which you wish to download watch faces into the program.

```
NUMBERS_LIST = [88237, 88050]
```
Next, the program will obtain an access token for you and save it to a file named `token.json`. It will then use this existing token for future operations. Do not delete the `token.json` file.

## 2. AdaptersInfo_download.py

___Description___ This program loads specifications for various watch models, as well as their images, which are available within the WearJoy application.

___Usage:___ You need to enter the start and end model numbers. The program will load all models within the specified range.

```
# === ЗАДАЙТЕ ВАШИ НОМЕРА ЗДЕСЬ ===
START_NUMBER = 88401  # Начальный номер, например 88000
END_NUMBER = 88500  # Конечный номер (включительно), например 88400
```

Program will obtain an access token for you and save it to a file named `token.json`. It will then use this existing token for future operations. Do not delete the `token.json` file.

## 3. Parser_OTA.py

___Description___ The program scans the specified range of models and generates a list of available OTA updates. The list includes the model number, model name, update version, release date, and file size.

___Usage:___ You need to enter the start and end model numbers. You can keep 88000 and 88450 and simply run the program.

```
# === НАСТРОЙКИ ===
START_NUMBER = 88000  # Начальный номер
END_NUMBER = 88450  # Конечный номер (включительно)
```
## 4. Downloader_OTA.py

___Description___ The program downloads the specified OTA updates to a folder

___Usage:___ You need to enter the model numbers for which you wish to download OTA updates to a folder `OUTPUT_DIR`

```
# === ЗАДАЙТЕ ВАШИ НОМЕРА ЗДЕСЬ ===
NUMBERS_LIST = [88237, 88359] 
OUTPUT_DIR = "downloads"
```
