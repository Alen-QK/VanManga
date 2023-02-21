import re
import requests
from bs4 import BeautifulSoup
from modules.download_img import download_img
from modules.ua_producer import ua_producer


def chapter_comic_page(chapter):
    chapter_title = chapter[0]
    chapter_link = chapter[1]
    print(chapter_title)
    # 找出‘Page #’
    findPage = re.compile('Page\s\d+$')

    headers = {'User-Agent': ua_producer(), "Accept-Language": "en-US"}
    response = requests.get(chapter_link, headers= headers).text
    soup = BeautifulSoup(response, 'lxml')
    site_reader = soup.find('div', class_= 'site-reader')
    img_array = list()
    # 匹配具有‘data-page-image-url’属性的图片tag
    img_collection = site_reader.find_all('img', attrs= {'data-page-image-url': True})

    for img_tag in img_collection:
        img_page = findPage.findall(img_tag['alt'])
        img_array.append([img_page[0], img_tag['data-page-image-url']])

    download_img(chapter_title, img_array)