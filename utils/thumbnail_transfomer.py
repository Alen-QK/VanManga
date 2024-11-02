import json

from utils.thumbnails_creator import thumbnails_creator


def test():
    with open('/vanmanga/eng_config/manga_library.json', 'r', encoding="utf-8") as f:
        manga_library = json.load(f)

        for key, value in manga_library.items():
            print(value)
            result = thumbnails_creator(value)
            manga_library[key] = result

    with open('/vanmanga/eng_config/manga_library.json', 'w', encoding="utf8") as f:
        json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
        f.write(json_tmp)

test()