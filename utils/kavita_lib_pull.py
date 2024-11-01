import requests
import os

def kavita_lib_pull(lib):
    KAVITA_URL = "" if os.environ.get("KAVITA_URL") is None else os.environ.get("KAVITA_URL")
    KAVITA_ADMIN_APIKEY = "" if os.environ.get("KAVITA_ADMIN_APIKEY") is None else os.environ.get("KAVITA_ADMIN_APIKEY")
    KAVITA_LIB_ID = "1" if os.environ.get("KAVITA_LIB_ID") is None else os.environ.get("KAVITA_LIB_ID")

    if not KAVITA_URL or not KAVITA_ADMIN_APIKEY:
        print("\n########## 未配置Kavita环境，跳过该操作 ##########")
        return

    authEndpoint = "/api/Plugin/authenticate"
    authUrl = f"{KAVITA_URL}{authEndpoint}?apiKey={KAVITA_ADMIN_APIKEY}&pluginName=pythonScanScript"

    try:
        response = requests.post(authUrl)
        response.raise_for_status()
        jwt = response.json()["token"]
    except requests.exceptions.RequestException as e:
        print("\n获取Kavita授权失败：", e)
        return

    # 获取指定lib id对应的所有series的信息
    headers = {
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
    }
    seriesEndPoint = "/api/Series/all-v2"
    seriesUrl = f"{KAVITA_URL}{seriesEndPoint}"
    body = {}

    try:
        response = requests.post(seriesUrl, headers=headers, json=body)
        kavitaLib = response.json()
    except requests.exceptions.RequestException as e:
        print("\n获取Kavita仓库失败： ", e)
        return

    for series in kavitaLib:
        folderPath = series["folderPath"]
        manga_id = folderPath.split("$")[1]
        kavitaLib_id = series["id"]
        lib[manga_id]["kavita_url"] =  f"{KAVITA_URL}/library/{KAVITA_LIB_ID}/series/{kavitaLib_id}"


    return lib