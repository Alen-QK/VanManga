import datetime
import requests
import json
import os

from main import env_config


def flaresolverr_bypasser(ENV_PATH, CF_dict, url):
    env_config = json.load(open(ENV_PATH), encoding="utf-8")

    retryCount = 0
    FLARESOLVERR_URL = env_config['FLARESOLVERR_URL']
    CF_dict["cf_activate"] = True

    headers = {"Content-Type": "application/json"}
    data = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000,
        "returnOnlyCookies": True,
    }
    response = requests.post(FLARESOLVERR_URL, headers=headers, json=data)

    # 与Bypasser连接的重试
    while json.loads(response.content)["status"] != "ok" and retryCount < 5:
        response = requests.post(
            FLARESOLVERR_URL, headers=headers, json=data
        )
        retryCount += 1

    if (
            json.loads(response.content)["status"] != "ok"
            and json.loads(response.content)["message"] != "Challenge solved!"
    ):
        print(
            f"########### 未能从Bypasser获取到cookies，运行任务失败，需要检查链接 ############"
        )
        return

    content = json.loads(response.content)
    solution = content["solution"]
    # 更新CF的相关信息，用于抓取任务
    for item in solution["cookies"]:
        if item["name"] == "cf_clearance":
            CF_dict["cf_clearance_value"] = item["value"]

    (
        CF_dict["cf_userAgent"],
        CF_dict["updateTime"],
    ) = (
        solution["userAgent"],
        datetime.datetime.now(),
    )

    return CF_dict