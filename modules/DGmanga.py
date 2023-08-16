import base64
import random
import re
import gevent
import gevent
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
from threading import current_thread

from modules.MangaSite import MangaSite
from modules.ua_producer import ua_producer
from modules.make_path import path_exists_make
from modules.generate_file_path import do_zip_compress
from modules.chapter_title_reformat import chapter_title_reformat


class DGmanga(MangaSite):
    def __init__(self, manga_id):
        self.manga_id = manga_id
        self.target_folder_path = ''
        self.Current_idx = float('-inf')

    def search_manga(self, search_name):
        headers = {'User-Agent': ua_producer()}
        url = f'https://dogemanga.com/?q={search_name}&l=zh'
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'lxml')

        site_scroll_row = soup.find('div', class_='site-scroll__row')

        try:
            site_cards = site_scroll_row.find_all('div', class_='site-card')
            # 限制只返回前十个结果
            max_amount = min(10, len(site_cards))
            results = list()
            session = requests.Session()

            for i in range(max_amount):
                manga_dict = defaultdict()
                card = site_cards[i]
                manga_id = card['data-manga-id']
                manga_name = card.find('h5', class_='card-title').text.replace('\n', '')
                artist_name = card.find('h6', class_='card-subtitle').text.replace('\n', '')
                newest_epi = card.find('li', class_='list-group-item').text.replace('\n', '')
                thumbnail_link = card.find('img', class_='card-img-top')['src']
                manga_thumbnail = session.get(thumbnail_link, headers=headers).content
                encoded_thumbnail = (base64.b64encode(manga_thumbnail)).decode('utf-8')

                manga_dict['manga_name'] = manga_name
                manga_dict['manga_id'] = manga_id
                manga_dict['artist_name'] = artist_name
                manga_dict['newest_epi'] = newest_epi
                manga_dict['thumbnail'] = encoded_thumbnail

                results.append(manga_dict)

            return results
        except:
            return 457

    def check_manga_length(self):
        headers = {'User-Agent': ua_producer()}
        target_link = f'https://dogemanga.com/m/{self.manga_id}?l=zh'

        response = requests.get(target_link, headers=headers).text
        soup = BeautifulSoup(response, 'lxml')

        try:
            tab_content = soup.select('.tab-content > #site-manga__tab-pane-all')[0]
            # 它的长度之后对于last epi的计算有作用
            tab_content = tab_content.find_all('a', class_='site-manga-thumbnail__link')

            return len(tab_content)
        except:
            return 501

    def generate_chapters_array(self, start, end, download_root_folder_path, manga_name):
        # todo 传参路径
        manga_name = manga_name.replace('/', '-')
        self.target_folder_path = f'{download_root_folder_path}/{manga_name}${self.manga_id}/{manga_name}'
        path_exists_make(self.target_folder_path)

        session = requests.Session()
        chapters_array = self.comic_main_page(self.manga_id, session)

        if chapters_array == 501:
            return 501

        chapters_array.reverse()
        chapters_array = chapters_array[start - 1:end]

        return chapters_array

    def comic_main_page(self, target, session):
        headers = {'User-Agent': ua_producer()}
        target_link = f'https://dogemanga.com/m/{target}?l=zh'

        response = session.get(target_link, headers=headers).text
        soup = BeautifulSoup(response, 'lxml')

        try:
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
        except:
            return 501

    def scrape_each_chapter(self, chapter, manga_library, Error_dict, his_length, idx, app):
        with app.app_context():
            chapter_title = chapter_title_reformat(chapter[0])
            chapter_link = chapter[1]

            print(f"\n{chapter_title} downloading begin........\n")
            # 找出‘第 # 页’
            # findPage = re.compile('Page\s\d+$')
            findPage = re.compile('第\s\d+\s[页|頁]')

            headers = {'User-Agent': ua_producer()}
            response = requests.get(chapter_link, headers=headers)
            # flag = False

            # if response.status_code == 429:
            if response.status_code == 429:
                Error_dict['g_error_flag'] = True
                # 设定error_count的最大上限为5
                if Error_dict['g_error_count'] < 6:
                    Error_dict['g_error_count'] += 1
                # 计算等待时间
                wait_time = Error_dict['g_wait_time'] * Error_dict['g_error_count'] + int(random.random() * 10)

                print('\n%s: 章节抓取遇到429错误，将开始等待%d s !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' % (
                chapter_title, wait_time))
                gevent.sleep(wait_time)
                Error_dict['g_error_flag'] = False
                print('\n重新开始抓取\n')
                # flag = True
                return self.scrape_each_chapter(chapter, manga_library, Error_dict, his_length, idx, app)
            else:
                soup = BeautifulSoup(response.text, 'lxml')

                try:
                    site_reader = soup.find('div', class_='site-reader')
                    img_array = list()
                    # 匹配具有‘data-page-image-url’属性的图片tag
                    img_collection = site_reader.find_all('img', attrs={'data-page-image-url': True})
                except:
                    return 502

                for img_tag in img_collection:

                    try:
                        img_page = findPage.findall(img_tag['alt'])
                        img_id = img_tag['data-page-image-url'].split('/')
                        img_array.append([img_page[0], img_id[-1]])
                    except:
                        return 502

                session = requests.Session()
                print(f'\nCurrent running chapter task info:\n {chapter_title}: {current_thread().getName()}')
                self.download_img(chapter_title, img_array, session, Error_dict)

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

    def download_single_chapter(self, chapter, Error_dict, app, download_root_folder_path, manga_name):
        self.target_folder_path = f'{download_root_folder_path}/{manga_name}${self.manga_id}/{manga_name}'
        # print(self.target_folder_path)
        path_exists_make(self.target_folder_path)

        with app.app_context():
            chapter_title = chapter_title_reformat(chapter[0])
            chapter_link = chapter[1]

            print(f"\n{chapter_title} downloading begin........\n")
            # 找出‘第 # 页’
            # findPage = re.compile('Page\s\d+$')
            findPage = re.compile('第\s\d+\s[页|頁]')

            headers = {'User-Agent': ua_producer()}
            response = requests.get(chapter_link, headers=headers)
            # flag = False

            # if response.status_code == 429:
            if response.status_code == 429:
                Error_dict['g_error_flag'] = True
                # 设定error_count的最大上限为5
                if Error_dict['g_error_count'] < 6:
                    Error_dict['g_error_count'] += 1
                # 计算等待时间
                wait_time = Error_dict['g_wait_time'] * Error_dict['g_error_count'] + int(random.random() * 10)

                print('\n%s: 章节抓取遇到429错误，将开始等待%d s !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' % (
                    chapter_title, wait_time))
                gevent.sleep(wait_time)
                Error_dict['g_error_flag'] = False
                print('\n重新开始抓取\n')
                # flag = True
                return self.scrape_each_chapter(chapter, Error_dict, app)
            else:
                soup = BeautifulSoup(response.text, 'lxml')

                try:
                    site_reader = soup.find('div', class_='site-reader')
                    img_array = list()
                    # 匹配具有‘data-page-image-url’属性的图片tag
                    img_collection = site_reader.find_all('img', attrs={'data-page-image-url': True})
                except:
                    return 502

                for img_tag in img_collection:

                    try:
                        img_page = findPage.findall(img_tag['alt'])
                        img_id = img_tag['data-page-image-url'].split('/')
                        img_array.append([img_page[0], img_id[-1]])
                    except:
                        return 502

            session = requests.Session()
            print(f'\nCurrent running chapter task info:\n {chapter_title}: {current_thread().getName()}')
            self.download_img(chapter_title, img_array, session, Error_dict)

        return ('temp')

    def download_img(self, chapter_title, img_array, session, Error_dict):

        folder_path = self.target_folder_path + f'/{chapter_title}'
        path_exists_make(folder_path)
        # print(folder_path)
        headers = {'User-Agent': ua_producer()}

        for img in img_array:
            # 如果其他线程上的访问已经遭遇block，则当前线程上的单页抓取暂缓执行
            while Error_dict['g_error_flag']:
                # print('page线程停止中')
                gevent.sleep(0)

            img_title = img[0]
            img_id = img[1]
            target_link = f'https://dogemanga.com/images/pages/{img_id}?l=zh'
            response = session.get(target_link, headers=headers)

            if response.status_code == 429:
                Error_dict['g_error_flag'] = True

                if Error_dict['g_error_count'] < 6:
                    Error_dict['g_error_count'] += 1

                wait_time = Error_dict['g_wait_time'] * Error_dict['g_error_count'] + int(random.random() * 10)
                print('\n%s: 单页抓取遇到429错误，将开始等待%d s !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n' % (
                img_title, wait_time))
                gevent.sleep(wait_time)
                Error_dict['g_error_flag'] = False
                print('\n重新开始抓取\n')

                return self.download_img(chapter_title, img_array, session, Error_dict)
            else:
                target_path = folder_path + ('/%s' % img_title) + '.jpg'

                with open(target_path, 'wb') as f:
                    f.write(response.content)

                print('%s %s downloaded' % (chapter_title, img_title))

                gevent.sleep(1 + int(random.random() * 1))

        print(f"########### {chapter_title} 压缩开始！ ############")
        do_zip_compress(folder_path)
        print(f"########### {chapter_title} 压缩完成！ ############")
