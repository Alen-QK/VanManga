import json
import os

import requests

from bs4 import BeautifulSoup
from DrissionPage import SessionPage


def update_helper(manga_id, clearance, userAgent):
    target_link = f"https://dogemanga.com/m/{manga_id}?l=zh"
    drissionSession = SessionPage()
    response = None

    if clearance != "":
        headers = {"User-Agent": userAgent}
        cookie = {"cf_clearance": clearance}
        drissionSession.get(target_link, headers=headers, cookies=cookie)
        response = drissionSession.response
    else:
        drissionSession.get(target_link)
        response = drissionSession.response

    soup = BeautifulSoup(response.text, "lxml")

    site_main_content = soup.find("div", class_="site-main-content")
    site_card = site_main_content.find("div", class_="site-card")
    manga_status = site_card.find("small", class_="text-muted").text.split("\n")

    serialization = 1

    for ele in manga_status:
        if "連載中" in ele:
            serialization = 0
            break

    return serialization


def serialization_make():
    manga_lib = json.load(open("/vanmanga/eng_config/manga_library.json", encoding="utf-8"))
    bypasser = cf_bypasser()

    if not bypasser:
        for manga_id, manga_content in manga_lib.items():
            serial_status = update_helper(manga_id, "", "")
            print(manga_content["manga_name"] + "\n")
            manga_content["serialization"] = serial_status
            manga_content["download_switch"] = serial_status
    else:
        for manga_id, manga_content in manga_lib.items():
            serial_status = update_helper(manga_id, bypasser[0], bypasser[1])
            print(manga_content["manga_name"] + "\n")
            manga_content["serialization"] = serial_status
            manga_content["download_switch"] = serial_status

    with open("/vanmanga/eng_config/manga_library.json", "w", encoding="utf-8") as f:
        json_tmp = json.dumps(manga_lib, indent=4, ensure_ascii=False)
        f.write(json_tmp)

    print("done")

def cf_bypasser():
    FLARESOLVERR_URL = os.environ.get('FLARESOLVERR_URL') if os.environ.get("FLARESOLVERR_URL") else None

    if not FLARESOLVERR_URL:
        return False

    url = "https://dogemanga.com"
    drissionSession = SessionPage()
    drissionSession.get(url)
    response = drissionSession.response

    if response.status_code == 403 or "?__cf_chl_rt_tk" in response.text:
        clearance = ""
        browser = ""
        headers = {"Content-Type": "application/json"}
        data = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "returnOnlyCookies": True,
        }
        response = requests.post(FLARESOLVERR_URL, headers=headers, json=data)
        content = json.loads(response.content)
        solution = content["solution"]
        # 更新CF的相关信息，用于抓取任务
        for item in solution["cookies"]:
            if item["name"] == "cf_clearance":
                clearance = item["value"]

        browser = solution["userAgent"]

        return [clearance, browser]
    else:
        return False

serialization_make()