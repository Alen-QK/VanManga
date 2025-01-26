import requests
import json
from bs4 import BeautifulSoup
from utils.ua_producer import ua_producer

manga_lib = json.load(open("./dev_config/manga_library.json", encoding="utf-8"))

searchInput = "98921782"
result = []
for key, value in manga_lib.items():
    manga_name = value['manga_name']
    artist = value['artist_name']
    manga_id = value['manga_id']

    if searchInput in manga_name or searchInput in artist or searchInput in manga_id:
        result.append(value)

print(result)
print("done")
