import time
import requests
import base64
import json
import ast

from collections import defaultdict
from threading import Thread
from modules.ua_producer import ua_producer

from flask import Flask
from flask_apscheduler import APScheduler
from flask_restful import Api, Resource, reqparse, abort, request
from bs4 import BeautifulSoup
from dogemanga import entry
from dogemanga import search_comic_progress

app = Flask(__name__)
api = Api(app)
scheduler = APScheduler()

# post format
confirm_post_args = reqparse.RequestParser()
confirm_post_args.add_argument('manga_object', type= str, help= 'thumbnail of the manga is required', required= True)
def dogemangaTask():
    entry('UsprF-z2')

def confirm_comic_task(manga_object):
    manga_name = manga_object['manga_name']
    manga_id = manga_object['manga_id']
    artist_name = manga_object['artist_name']
    thumbnail = manga_object['thumbnail']

    current_manga_length = search_comic_progress(manga_id)

    manga_library = json.load(open('./manga_library.json', encoding= 'utf-8'))

    if manga_id not in manga_library:
        manga_info = dict()
        manga_info['manga_name'] = manga_name
        manga_info['artist_name'] = artist_name
        manga_info['last_epi'] = current_manga_length
        manga_info['thumbnail'] = thumbnail

        manga_library[manga_id] = manga_info

        with open('./manga_library.json', 'w') as f:
            json.dump(manga_library, f)

        entry(manga_id, 0, current_manga_length)
    else:
        cur_manga_info = manga_library[manga_id]

        if current_manga_length > cur_manga_info['last_epi']:
            start = cur_manga_info['last_epi'] + 1
            cur_manga_info['manga_name'] = manga_name
            cur_manga_info['artist_name'] = artist_name
            cur_manga_info['last_epi'] = current_manga_length
            cur_manga_info['thumbnail'] = thumbnail

            manga_library[manga_id] = cur_manga_info

            with open('./manga_library.json', 'w') as f:
                json.dump(manga_library, f)

            entry(manga_id, start, current_manga_length)
        else:
            pass




class DogeSearch(Resource):
    def get(self):
        args = request.args
        search_name = args['manga_name']
        headers = {'User-Agent': ua_producer()}
        url = f'https://dogemanga.com/?q={search_name}&l=zh'
        response = requests.get(url, headers= headers)
        soup = BeautifulSoup(response.text, 'lxml')

        site_scroll_row = soup.find('div', class_= 'site-scroll__row')

        try:
            site_cards = site_scroll_row.find_all('div', class_= 'site-card')
            # 限制只返回前十个结果
            max_amount = min(10, len(site_cards))
            results = list()
            session = requests.Session()

            for i in range(max_amount):
                manga_dict = defaultdict()
                card = site_cards[i]
                manga_id = card['data-manga-id']
                manga_name = card.find('h5', class_= 'card-title').text.replace('\n', '')
                artist_name = card.find('h6', class_= 'card-subtitle').text.replace('\n', '')
                newest_epi = card.find('li', class_= 'list-group-item').text.replace('\n', '')
                thumbnail_link = card.find('img', class_= 'card-img-top')['src']
                manga_thumbnail = session.get(thumbnail_link, headers= headers).content
                encoded_thumbnail = (base64.b64encode(manga_thumbnail)).decode('utf-8')

                manga_dict['manga_name'] = manga_name
                manga_dict['manga_id'] = manga_id
                manga_dict['artist_name'] = artist_name
                manga_dict['newest_epi'] = newest_epi
                manga_dict['thumbnail'] = encoded_thumbnail

                results.append(manga_dict)

            return results

        except:
            abort(404, message= 'No manga searched.')


class DogePost(Resource):

    def post(self):
        args = confirm_post_args.parse_args()
        manga_object = ast.literal_eval(args['manga_object'])
        # 后台工作交由多线程执行，先返回200
        Thread(target= confirm_comic_task, args= [manga_object]).start()

        return 'submitted', 200



api.add_resource(DogeSearch, '/api/dogemanga/search')
api.add_resource(DogePost, '/api/dogemanga/confirm')


if __name__ == '__main__':
    # scheduler.add_job(id= 'Dogemanga task', func= dogemangaTask, trigger= 'interval', seconds= 10)
    # scheduler.start()
    app.run(host='127.0.0.1', port= 5000, debug= True)
