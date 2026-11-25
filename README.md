# DT.NO1_files_downloaders
Download files from server DT.NO1 (watch faces, OTA, watch specs)

## 1. watchFace_download.py

___Description___ The program downloads watch faces available in the WearJoy app for a specific watch model (or multiple models).

___Usage:___ You need to enter the model numbers for which you wish to download watch faces into the program.

```
NUMBERS_LIST = [88237, 88050]
```
Next, the program will obtain an access token for you and save it to a file named `token.json`. It will then use this existing token for future operations. Do not delete the `token.json` file.
