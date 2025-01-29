import json
import base64
import os

from make_path import path_exists_make

def thumbnails_creator1(manga_object):
    manga_id = manga_object["manga_id"]
    image_data_base64 = manga_object["thumbnail"]
    image_data = base64.b64decode(image_data_base64)
    SERVER_BASE_URL = os.environ.get("MANGA_BASE_WEBSOCKET_URL") if os.environ.get(
        "MANGA_BASE_WEBSOCKET_URL") else "http://localhost:5000"

    # path_exists_make("../thumbnails")
    path_exists_make("/vanmanga/thumbnails")

    # with open(f"../thumbnails/{manga_id}.jpg", 'wb') as f:
    #     f.write(image_data)
    with open(f"/vanmanga/thumbnails/{manga_id}.jpg", 'wb') as f:
        f.write(image_data)

    manga_object["thumbnail"] = f"{SERVER_BASE_URL}/api/dogemanga/thumbnail?mid={manga_id}"

    return manga_object

def test():
    with open('/vanmanga/eng_config/manga_library.json', 'r', encoding="utf-8") as f:
        manga_library = json.load(f)

        for key, value in manga_library.items():
            result = thumbnails_creator1(value)
            manga_library[key] = result

    with open('/vanmanga/eng_config/manga_library.json', 'w', encoding="utf8") as f:
        json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
        f.write(json_tmp)

test()
print("done")