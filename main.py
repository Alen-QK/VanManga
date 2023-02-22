import requests
import base64
import json
from collections import defaultdict
from modules.ua_producer import ua_producer
from flask import Flask
from flask_apscheduler import APScheduler
from flask_restful import Api, Resource, reqparse
from bs4 import BeautifulSoup
from dogemanga import entry

app = Flask(__name__)
api = Api(app)
scheduler = APScheduler()


def dogemangaTask():
    entry('UsprF-z2')


class DogeManga(Resource):
    def get(self, search_name):
        headers = {'User-Agent': ua_producer()}
        url = f'https://dogemanga.com/?q={search_name}&l=zh'
        response = requests.get(url, headers= headers)
        soup = BeautifulSoup(response.text, 'lxml')

        site_scroll_row = soup.find('div', class_= 'site-scroll__row')
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
            thumbnail_link = card.find('img', class_= 'card-img-top')['src']
            manga_thumbnail = session.get(thumbnail_link, headers= headers).content
            encoded_thumbnail = str(base64.b64encode(manga_thumbnail))[1:]

            manga_dict['manga_name'] = manga_name
            manga_dict['manga_id'] = manga_id
            manga_dict['artist_name'] = artist_name
            manga_dict['thumbnail'] = encoded_thumbnail

            results.append(manga_dict)

        return json.dumps(results)


api.add_resource(DogeManga, '/dogemanga/<string:search_name>')

if __name__ == '__main__':
    # scheduler.add_job(id= 'DogeManga task', func= dogemangaTask, trigger= 'interval', seconds= 10)
    # scheduler.start()
    app.run(host='127.0.0.1', port= 5000, debug=True)
