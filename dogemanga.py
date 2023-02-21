import os
import re
import time
import requests
import random
import concurrent.futures
from bs4 import BeautifulSoup
from modules.ua_producer import ua_producer

g_error_flag = False
g_error_count = 0
g_wait_time = 40
# 漫画页面，抓取所有章节
def comic_main_page(target, session):
    headers = {'User-Agent': ua_producer()}
    target_link = f'https://dogemanga.com/m/{target}?l=zh'

    response = session.get(target_link, headers= headers).text
    soup = BeautifulSoup(response, 'lxml')
    tab_content = soup.select('.tab-content > #site-manga__tab-pane-all')[0]
    # 它的长度之后对于last epi的计算有作用
    tab_content = tab_content.find_all('a', class_= 'site-manga-thumbnail__link')
    chapters_array = list()
    # 去掉尾部的换行
    cutTail = re.compile('^\s+|\s+$')
    # 去掉前面的emoji
    cutEmoji = re.compile(
        u'['u'\U0001F300-\U0001F64F' u'\U0001F680-\U0001F6FF' u'\u2600-\u2B55 \U00010000-\U0010ffff]+')

    for content in tab_content:
        link = content['href']
        title = content.find('span', class_= 'text-center').text
        title = cutTail.sub('', title)
        title = cutEmoji.sub('', title)
        chapters_array.append([title, link])

    return chapters_array

# 单章节，抓取所有图片的必须信息
def chapter_comic_page(chapter):
    global g_error_flag
    global g_error_count
    global g_wait_time

    chapter_title = chapter[0]
    chapter_link = chapter[1]

    print(chapter_title)
    # 找出‘Page #’
    # findPage = re.compile('Page\s\d+$')
    findPage = re.compile('第\s\d+\s[页|頁]')

    headers = {'User-Agent': ua_producer()}
    response = requests.get(chapter_link, headers= headers)

    if response.status_code == 429:
        g_error_flag = True
        if g_error_count < 6:
            g_error_count += 1
        wait_time = g_wait_time * g_error_count + int(random.random() * 10)
        print('%s: 章节抓取遇到429错误，将开始等待%d s' % (chapter_title, wait_time))
        time.sleep(wait_time)
        g_error_flag = False
        print('重新开始抓取')
        chapter_comic_page(chapter)
    else:
        soup = BeautifulSoup(response.text, 'lxml')
        site_reader = soup.find('div', class_= 'site-reader')
        img_array = list()
        # 匹配具有‘data-page-image-url’属性的图片tag
        img_collection = site_reader.find_all('img', attrs= {'data-page-image-url': True})

        for img_tag in img_collection:
            img_page = findPage.findall(img_tag['alt'])
            img_id = img_tag['data-page-image-url'].split('/')
            img_array.append([img_page[0], img_id[-1]])

        session = requests.Session()
        download_img(chapter_title, img_array, session)
        print('%s is downloaded' % chapter_title)

# 抓取图片
def download_img(chapter_title, img_array, session):
    global g_error_flag
    global g_error_count
    global g_wait_time

    folder_path = ('./%s' % chapter_title)
    os.makedirs(folder_path, exist_ok= True)
    headers = {'User-Agent': ua_producer()}

    for img in img_array:
        while g_error_flag:
            print('page线程停止中')
        img_title = img[0]
        img_id = img[1]
        target_link = f'https://dogemanga.com/images/pages/{img_id}?l=zh'
        response = session.get(target_link, headers= headers)

        if response.status_code == 429:
            g_error_flag = True
            if g_error_count < 6:
                g_error_count += 1
            wait_time = g_wait_time * g_error_count + int(random.random() * 10)
            print('%s: 单页抓取遇到429错误，将开始等待%d s' % (img_title, wait_time))
            time.sleep(wait_time)
            g_error_flag = False
            print('重新开始抓取')
            download_img(chapter_title, img_array, session)
        else:
            target_path = folder_path + ('/%s' % img_title) + '.jpg'

            with open(target_path, 'wb') as f:
                f.write(response.content)

            print('%s %s downloaded' % (chapter_title, img_title))

            time.sleep(1 + int(random.random() * 1))

def entry(manga_id):
    global g_error_flag
    session = requests.Session()
    target = manga_id
    chapters_array = comic_main_page(target, session)
    chapters_array.reverse()
    count = 0
    total = len(chapters_array)

    with concurrent.futures.ThreadPoolExecutor(max_workers= 3) as executor:
        # executor.map(chapter_comic_page, chapters_array)
        for chapter in chapters_array:
            while g_error_flag:
                print('线程停止中')
            executor.submit(chapter_comic_page, chapter)
            time.sleep(2 + int(random.random() * 3))
    # for chapter in chapters_array:
    #     chapter_comic_page(chapter)
    #
    #     count += 1
    #     print('Complete %d chapters, %d is pending\n' % (count, total - count))
    #     time.sleep(2 + int(random.random() * 3))

    print('done')

# if __name__ == '__main__':
#     entry('TbCLIzv0')