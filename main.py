import requests
from modules.comic_main_page import comic_main_page
from modules.chapter_comic_page import chapter_comic_page

session = requests.Session()
target = 'TbCLIzv0'
chapters_array = comic_main_page(target, session)

for chapter in chapters_array:
    chapter_comic_page(chapter)

print('done')