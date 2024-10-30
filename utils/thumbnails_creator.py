import json
import base64

from utils.make_path import path_exists_make


def thumbnails_creator(manga_object):
    manga_id = manga_object["manga_id"]
    image_data_base64 = manga_object["thumbnail"]
    image_data = base64.b64decode(image_data_base64)

    path_exists_make("../thumbnails")

    with open(f"../thumbnails/{manga_id}.jpg", 'wb') as f:
        f.write(image_data)

    manga_object["thumbnail"] = f"{manga_id}.jpg"

    return manga_object

def test():
    with open('../eng_config/manga_library.json', 'r', encoding="utf-8") as f:
        manga_library = json.load(f)

        for key, value in manga_library.items():
            print(value)
            result = thumbnails_creator(value)
            manga_library[key] = result

    with open('../eng_config/manga_library.json', 'w', encoding="utf8") as f:
        json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
        f.write(json_tmp)

test()