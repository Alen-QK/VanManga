import requests
import json
import os

from main import KAVITA_BASE_URL, KAVITA_EXPOSE_URL, KAVITA_ADMIN_APIKEY


def kavita_lib_pull(ENV_PATH, lib):
    env_config = json.load(open(ENV_PATH), encoding="utf-8")
    KAVITA_BASE_URL = "" if env_config["KAVITA_BASE_URL"] is "" else env_config["KAVITA_BASE_URL"]
    KAVITA_EXPOSE_URL = "" if env_config["KAVITA_EXPOSE_URL"] is "" else env_config["KAVITA_EXPOSE_URL"]
    KAVITA_ADMIN_APIKEY = "" if env_config["KAVITA_ADMIN_APIKEY"] is "" else env_config["KAVITA_ADMIN_APIKEY"]
    KAVITA_LIB_ID = "1" if env_config["KAVITA_LIB_ID"] is "1" else env_config["KAVITA_LIB_ID"]

    # KAVITA_BASE_URL = "" if os.environ.get("KAVITA_BASE_URL") is None else os.environ.get("KAVITA_BASE_URL")
    # KAVITA_EXPOSE_URL = "" if os.environ.get("KAVITA_EXPOSE_URL") is None else os.environ.get("KAVITA_EXPOSE_URL")
    # KAVITA_ADMIN_APIKEY = "" if os.environ.get("KAVITA_ADMIN_APIKEY") is None else os.environ.get("KAVITA_ADMIN_APIKEY")
    # KAVITA_LIB_ID = "1" if os.environ.get("KAVITA_LIB_ID") is None else os.environ.get("KAVITA_LIB_ID")

    if not KAVITA_BASE_URL or not KAVITA_EXPOSE_URL or not KAVITA_ADMIN_APIKEY:
        print("########## 未配置Kavita环境，跳过该操作 ##########")
        return lib

    authEndpoint = "/api/Plugin/authenticate"
    authUrl = f"{KAVITA_BASE_URL}{authEndpoint}?apiKey={KAVITA_ADMIN_APIKEY}&pluginName=pythonScanScript"

    try:
        response = requests.post(authUrl)
        response.raise_for_status()
        jwt = response.json()["token"]
    except requests.exceptions.RequestException as e:
        print("获取Kavita授权失败：", e)
        return lib

    # 获取指定lib id对应的所有series的信息
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }
    seriesEndPoint = "/api/Series/all-v2"
    seriesUrl = f"{KAVITA_BASE_URL}{seriesEndPoint}"
    body = {}

    try:
        response = requests.post(seriesUrl, headers=headers, json=body)
        kavitaLib = response.json()
    except requests.exceptions.RequestException as e:
        print("获取Kavita仓库失败： ", e)
        return lib

    for series in kavitaLib:
        folderPath = series["folderPath"]

        if "$" not in folderPath:
            continue

        manga_id = folderPath.split("$")[1]
        kavitaLib_id = series["id"]

        try:
            lib[manga_id]["kavita_url"] = f"{KAVITA_EXPOSE_URL}/library/{KAVITA_LIB_ID}/series/{kavitaLib_id}"
        except Exception as e:
            print(e)
            continue

    return lib
