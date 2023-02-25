import random
import re
import time

import requests
from bs4 import BeautifulSoup
from threading import current_thread

from modules.MangaSite import MangaSite
from modules.ua_producer import ua_producer
from modules.make_path import path_exists_make


class DGmanga(MangaSite):
    def __init__(self, manga_id):
        self.manga_id = manga_id
        self.target_folder_path = ''
        # self.GEF = False
        # self.GEC = 0
        # self.GWT = 0
        self.Current_idx = float('-inf')
    def check_manga_length(self):
        headers = {'User-Agent': ua_producer()}
        target_link = f'https://dogemanga.com/m/{self.manga_id}?l=zh'

        response = requests.get(target_link, headers=headers).text
        soup = BeautifulSoup(response, 'lxml')
        tab_content = soup.select('.tab-content > #site-manga__tab-pane-all')[0]
        # 它的长度之后对于last epi的计算有作用
        tab_content = tab_content.find_all('a', class_='site-manga-thumbnail__link')

        return len(tab_content)

    def generate_chapters_array(self, start, end):
        # todo 传参路径
        self.target_folder_path = f'./{self.manga_id}'
        path_exists_make(self.target_folder_path)

        session = requests.Session()
        chapters_array = self.comic_main_page(self.manga_id, session)
        chapters_array.reverse()
        chapters_array = chapters_array[start - 1:end]

        return chapters_array

    def comic_main_page(self, target, session):
        headers = {'User-Agent': ua_producer()}
        target_link = f'https://dogemanga.com/m/{target}?l=zh'

        response = session.get(target_link, headers=headers).text
        soup = BeautifulSoup(response, 'lxml')
        tab_content = soup.select('.tab-content > #site-manga__tab-pane-all')[0]
        # 它的长度之后对于last epi的计算有作用
        tab_content = tab_content.find_all('a', class_='site-manga-thumbnail__link')
        chapters_array = list()
        # 去掉尾部的换行
        cutTail = re.compile('^\s+|\s+$')
        # 去掉前面的emoji
        cutEmoji = re.compile(
            u'['u'\U0001F300-\U0001F64F' u'\U0001F680-\U0001F6FF' u'\u2600-\u2B55 \U00010000-\U0010ffff]+')

        for content in tab_content:
            link = content['href']
            title = content.find('span', class_='text-center').text
            title = cutTail.sub('', title)
            title = cutEmoji.sub('', title)
            chapters_array.append([title, link])

        return chapters_array

    def scrape_each_chapter(self, chapter, manga_library, Error_dict, his_length, idx):
        # self.GEF = g_error_flag
        # self.GEC = g_error_count
        # self.GWT = g_wait_time

        chapter_title = chapter[0]
        chapter_link = chapter[1]

        print(f"\n{chapter_title} downloading begin........\n")
        # 找出‘第 # 页’
        # findPage = re.compile('Page\s\d+$')
        findPage = re.compile('第\s\d+\s[页|頁]')

        headers = {'User-Agent': ua_producer()}
        response = requests.get(chapter_link, headers=headers)

        if response.status_code == 429:
            Error_dict['g_error_flag'] = True
            # 设定error_count的最大上限为5
            if Error_dict['g_error_count'] < 6:
                Error_dict['g_error_count'] += 1
            # 计算等待时间
            wait_time = Error_dict['g_wait_time'] * Error_dict['g_error_count'] + int(random.random() * 10)
            print('\n%s: 章节抓取遇到429错误，将开始等待%d s !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' % (chapter_title, wait_time))
            time.sleep(wait_time)
            Error_dict['g_error_flag'] = False
            print('\n重新开始抓取\n')
            self.scrape_each_chapter(chapter, manga_library, Error_dict, his_length, idx)
        else:
            soup = BeautifulSoup(response.text, 'lxml')
            site_reader = soup.find('div', class_='site-reader')
            img_array = list()
            # 匹配具有‘data-page-image-url’属性的图片tag
            img_collection = site_reader.find_all('img', attrs={'data-page-image-url': True})

            for img_tag in img_collection:
                img_page = findPage.findall(img_tag['alt'])
                img_id = img_tag['data-page-image-url'].split('/')
                img_array.append([img_page[0], img_id[-1]])

            session = requests.Session()
            print(f'DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD\n {chapter_title} {current_thread().getName()}')
            self.download_img(chapter_title, img_array, session, Error_dict)
            # td
            if self.Current_idx < idx:
                self.Current_idx = idx
                manga_library[self.manga_id]['last_epi'] = self.Current_idx + his_length
                manga_library[self.manga_id]['last_epi_name'] = chapter_title

                print('\n%s is downloaded !!!!!!!!\n' % chapter_title)

                return (self.Current_idx + his_length, chapter_title, True)
            else:
                # manga_library[self.manga_id]['last_epi_name'] = chapter_title

                print('\n%s is downloaded !!!!!!!!\n' % chapter_title)

                return (idx, chapter_title, False)

    def download_img(self, chapter_title, img_array, session, Error_dict):

        folder_path = self.target_folder_path + f'/{chapter_title}'
        path_exists_make(folder_path)
        headers = {'User-Agent': ua_producer()}

        for img in img_array:
            # 如果其他线程上的访问已经遭遇block，则当前线程上的单页抓取暂缓执行
            while Error_dict['g_error_flag']:
                print('page线程停止中')

            img_title = img[0]
            img_id = img[1]
            target_link = f'https://dogemanga.com/images/pages/{img_id}?l=zh'
            response = session.get(target_link, headers=headers)

            if response.status_code == 429:
                Error_dict['g_error_flag'] = True

                if Error_dict['g_error_count'] < 6:
                    Error_dict['g_error_count'] += 1

                wait_time = Error_dict['g_wait_time'] * Error_dict['g_error_count'] + int(random.random() * 10)
                print('\n%s: 单页抓取遇到429错误，将开始等待%d s !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' % (img_title, wait_time))
                time.sleep(wait_time)
                Error_dict['g_error_flag'] = False
                print('\n重新开始抓取\n')
                self.download_img(chapter_title, img_array, session, Error_dict)
            else:
                target_path = folder_path + ('/%s' % img_title) + '.jpg'

                with open(target_path, 'wb') as f:
                    f.write(response.content)

                print('%s %s downloaded' % (chapter_title, img_title))

                time.sleep(1 + int(random.random() * 1))