import requests
from modules.comic_main_page import comic_main_page
from modules.chapter_comic_page import chapter_comic_page

session = requests.Session()
target = '2X_-40f-'
chapters_array = comic_main_page(target, session)
count = 0
total = len(chapters_array)

for chapter in chapters_array:
    chapter_comic_page(chapter)
    count += 1
    print('Complete %d chapters, %d is pending\n' % (count, total - count))

print('done')