import re
import requests
from bs4 import BeautifulSoup
from modules.ua_producer import ua_producer


def comic_main_page(target):
    headers = {'User-Agent': ua_producer(), "Accept-Language": "en-US"}
    response = requests.get(target, headers= headers).text
    soup = BeautifulSoup(response, 'lxml')
    tab_content = soup.find_all('a', class_= 'site-manga-thumbnail__link')
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