import os

import requests


def kavita_scan_folder(folder):
    KAVITA_BASE_URL = "" if os.environ.get("KAVITA_BASE_URL") is None else os.environ.get("KAVITA_BASE_URL")
    KAVITA_EXPOSE_URL = "" if os.environ.get("KAVITA_EXPOSE_URL") is None else os.environ.get("KAVITA_EXPOSE_URL")
    KAVITA_ADMIN_APIKEY = "" if os.environ.get("KAVITA_ADMIN_APIKEY") is None else os.environ.get("KAVITA_ADMIN_APIKEY")

    if not KAVITA_BASE_URL or not KAVITA_EXPOSE_URL or not KAVITA_ADMIN_APIKEY:
        print("########## 未配置Kavita环境，跳过该操作 ##########")
        return False

    authEndpoint = "/api/Plugin/authenticate"
    authUrl = f"{KAVITA_BASE_URL}{authEndpoint}?apiKey={KAVITA_ADMIN_APIKEY}&pluginName=pythonScanScript"

    try:
        response = requests.post(authUrl)
        response.raise_for_status()
        jwt = response.json()["token"]
    except requests.exceptions.RequestException as e:
        print("获取Kavita授权失败：", e)
        return False

    # 获取指定lib id对应的所有series的信息
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }

    folderScanPoint = "/api/Library/scan-folder"
    folderScanUrl = f"{KAVITA_BASE_URL}{folderScanPoint}"
    body = {
        "apiKey": KAVITA_ADMIN_APIKEY,
        "folderPath": f"/manga/{folder}"
    }

    try:
        response = requests.post(folderScanUrl, headers=headers, json=body)

        if response.status_code != 200:
            return False

        return True
    except requests.exceptions.RequestException as e:
        print("提交文件扫描失败： ", e)
        return False
