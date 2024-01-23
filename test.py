import requests
import json
from bs4 import BeautifulSoup
from modules.ua_producer import ua_producer

manga_lib = json.load(open("./manga_library.json"))


def update_helper(manga_id):
    headers = {"User-Agent": ua_producer()}
    target_link = f"https://dogemanga.com/m/{manga_id}?l=zh"

    response = requests.get(target_link, headers=headers).text
    soup = BeautifulSoup(response, "lxml")

    site_main_content = soup.find("div", class_="site-main-content")
    site_card = site_main_content.find("div", class_="site-card")
    manga_status = site_card.find("small", class_="text-muted").text.split("\n")
    serialization_text, recent_update = (
        manga_status[1].split("：")[1],
        manga_status[3].split("：")[1],
    )
    print(serialization_text)
    serialization = 0 if serialization_text == "連載中" else 1

    return serialization


for manga_id, manga_content in manga_lib.items():
    serial_status = update_helper(manga_id)
    print(manga_content["manga_name"] + "\n")
    manga_content["serialization"] = serial_status

with open("./manga_library.json", "w", encoding="utf8") as f:
    json_tmp = json.dumps(manga_lib, indent=4, ensure_ascii=False)
    f.write(json_tmp)

print("done")
