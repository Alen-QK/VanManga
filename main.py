import os
import re
import requests
from bs4 import BeautifulSoup

target = 'https://dogemanga.com/m/2X_-40f-'
response = requests.get(target).text
soup = BeautifulSoup(response, 'lxml')
tab_content = soup.find_all('a', class_='site-manga-thumbnail__link')
chapters_array = list()
# 去掉尾部的换行
cutTail = re.compile('^\s+|\s+$')
# 去掉前面的emoji
cutEmoji = re.compile(u'['u'\U0001F300-\U0001F64F' u'\U0001F680-\U0001F6FF' u'\u2600-\u2B55 \U00010000-\U0010ffff]+')

for content in tab_content:
    link = content['href']
    title = content.find('span', class_='text-center').text
    title = cutTail.sub('', title)
    title = cutEmoji.sub('', title)
    chapters_array.append([title, link])

def chapter_comic_page(chapter):
    chapter_title = chapter[0]
    chapter_link = chapter[1]
    print(chapter_title)
    # 找出‘Page #’
    findPage = re.compile('Page\s\d+$')

    response = requests.get(chapter_link).text
    soup = BeautifulSoup(response, 'lxml')
    site_reader = soup.find('div', class_= 'site-reader')
    img_array = list()
    # 匹配具有‘data-page-image-url’属性的图片tag
    img_collection = site_reader.find_all('img', attrs= {'data-page-image-url': True})

    for img_tag in img_collection:
        img_page = findPage.findall(img_tag['alt'])
        img_array.append([img_page[0], img_tag['data-page-image-url']])

    download_img(chapter_title, img_array)

def download_img(chapter_title, img_array):
    folder_path = ('./%s' % chapter_title)
    os.makedirs(folder_path, exist_ok= True)

    for img in img_array:
        response = requests.get(img[1])
        target_path = folder_path + ('/%s' % img[0]) + '.jpg'
        with open(target_path, 'wb') as f:
            f.write(response.content)

for chapter in chapters_array:
    chapter_comic_page(chapter)

print('done')