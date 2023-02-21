import os
import requests
from modules.ua_producer import ua_producer


def download_img(chapter_title, img_array):
    folder_path = ('./%s' % chapter_title)
    os.makedirs(folder_path, exist_ok= True)

    for img in img_array:
        headers = {'User-Agent': ua_producer(), "Accept-Language": "en-US"}
        response = requests.get(img[1], headers= headers)
        target_path = folder_path + ('/%s' % img[0]) + '.jpg'
        with open(target_path, 'wb') as f:
            f.write(response.content)