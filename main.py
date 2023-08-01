import gevent.monkey

gevent.monkey.patch_all()

import os
import threading
import gevent
import random
import requests
import json
import ast
import concurrent.futures
import datetime

from gevent.threadpool import ThreadPool

from modules.make_manga_object import make_manga_object
from modules.TaskQueue import TaskQueue
from modules.re_zip_downloaded import re_zip_run

from flask import Flask, redirect, render_template
from flask_socketio import SocketIO, send, emit
from flask_apscheduler import APScheduler
from flask_restful import Api, Resource, reqparse, request
from flask_cors import CORS

from datetime import timezone

from modules.DGmanga import DGmanga

app = Flask(__name__, static_folder='frontend/static', template_folder='frontend/static/templates')
CORS(app, expose_headers=['Content-Disposition'])
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins='*')
scheduler = APScheduler()

if not os.path.exists('/vanmanga/eng_config/manga_library.json'):
    manga_library_content = {}
    os.mknod('/vanmanga/eng_config/manga_library.json')

    with open('/vanmanga/eng_config/manga_library.json', 'w', encoding='utf8') as f:
        json_tmp = json.dumps(manga_library_content, indent=4, ensure_ascii=False)
        f.write(json_tmp)

# post format
confirm_post_args = reqparse.RequestParser()
confirm_post_args.add_argument('manga_object', type=str, help='manga_object of the manga is required', required=True)
redownload_post_args = reqparse.RequestParser()
redownload_post_args.add_argument('manga_id', type=str, help='manga_id of the manga is required', required= True)
redownload_post_args.add_argument('selected_array', type=str, help='redownload chapter array is required', required= True)

Current_download = ''
Q = None
manga_library = json.load(open('/vanmanga/eng_config/manga_library.json', encoding='utf-8'))
Error_dict = {'g_error_flag': False, 'g_error_count': 0, 'g_wait_time': 40}
# env_config = json.load(open('eng_config/config.json', encoding='utf-8'))
download_root_folder_path = '/downloaded'


# print(manga_library)


# @app.route("/init")
# def hello():
#     return redirect('http://localhost:5000/init')

@app.route('/')
def go_to_mainpage():
    return render_template('index.html')


@app.route('/<path:fallback>')
def fallback(fallback):
    if fallback.startswith('css/') or fallback.startswith('js/') or fallback.startswith('img/') \
            or fallback == 'favicon.ico' or fallback.startswith('fonts/'):
        return app.send_static_file(fallback)
    elif fallback.startswith('mainpage/'):
        return app.send_static_file('templates/index.html')
    else:
        return app.send_static_file('templates/index.html')


def dogemangaTask():
    global manga_library
    print('\n########## Start Daily Update Task ##########\n')
    boot_scanning(manga_library)
    print('\n########## Daily Update Task Over ##########\n')


def boot_scanning(manga_library):
    print('开始bootScanning')
    for manga in manga_library.values():
        print('扫描漫画：' + manga['manga_name'])

        if manga['completed'] == False:
            print(manga['manga_name'] + '/' + manga['manga_id'] + '没有完成')
            Q.add_task(target=confirm_comic_task, manga_id=manga['manga_id'], dtype= '0')
            print(f"\n{manga['manga_id']} add to the queue\n")
        else:
            print(manga['manga_name'] + '/' + manga['manga_id'] + '已完成，但是需要检查是否更新')
            DG = DGmanga(manga['manga_id'])
            current_manga_length = DG.check_manga_length()

            if current_manga_length == 501:
                print('\nMight meet human check, shutdown the task.\n')
                return 'Might meet human check, shutdown the task.'

            history_length = manga['last_epi']

            print(manga['manga_name'] + '历史长度是' + str(history_length) + ',' + '当前长度是' + str(
                current_manga_length))

            if history_length < current_manga_length:
                print('因为当前长度大于历史长度，所以需要加入队列更新')
                Q.add_task(target=confirm_comic_task, manga_id=manga['manga_id'], dtype= '0')
                print(f"\n{manga['manga_id']} add to the queue\n")


# 实际上后台下载选定漫画的task
def confirm_comic_task(manga_id):
    global manga_library
    global Error_dict
    global Current_download
    global download_root_folder_path

    DG = DGmanga(manga_id)
    current_manga_length = DG.check_manga_length()

    if current_manga_length == 501:
        print('\nMight meet human check, shutdown the task.\n')
        return 'Might meet human check, shutdown the task.'

    target_manga = manga_library[manga_id]
    history_length = target_manga['last_epi']
    manga_name = target_manga['manga_name']

    if history_length <= current_manga_length:
        Current_download = manga_id
        print(f'\n{manga_id} 已经开始下载..........\n')

        socketio.emit('downloading_info', manga_id)

        dt = datetime.datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc)

        manga_library[manga_id]['add_date'] = utc_time.timestamp()

        start = 1 if history_length == 1 else history_length + 1
        end = current_manga_length

        chapters_array = DG.generate_chapters_array(start, end, download_root_folder_path, manga_name)

        if chapters_array == 501:
            print('\nMight meet human check, shutdown the task.\n')
            return 'Might meet human check, shutdown the task.'

        # pool = ThreadPool(2)
        #
        # for idx, chapter in enumerate(chapters_array):
        #     pool.spawn(DG.scrape_each_chapter, chapter, manga_library, Error_dict, start, idx, app)
        #     gevent.sleep(0)

        # if gevent.getcurrent() is not gevent.hub.get_hub().parent:
        #     pass
        # else:
        #     gevent.wait()

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

            finish = list()

            for idx, chapter in enumerate(chapters_array):
                # 如果其他线程的task已经被bloack，那么当前线程的章节任务暂缓, 如果不在这里加上gevent.sleep移交协程control，就会出现死锁，
                # 导致实际上DG实例已经在sleep后将control交还main，但是main自己相当于锁了自己，至此导致worker等待超时，被kill
                while Error_dict['g_error_flag']:
                    gevent.sleep(0)
                # 这里传递的实际上时manga_library的引用，所以在dogemanga中的任何操作都会直接反应到内存的manga_library对象上，并非副本
                future = executor.submit(DG.scrape_each_chapter, chapter, manga_library, Error_dict, start, idx, app)

                finish.append(future)
                gevent.sleep(2 + int(random.random() * 3))

            if gevent.getcurrent() is not gevent.hub.get_hub().parent:
                pass
            else:
                gevent.wait()

            for f in concurrent.futures.as_completed(finish):
                tmp = dict()
                # gevent.wait([f], timeout=0)
                res = f.result()

                if res == 502:
                    print("Meet unknown scrape error, maybe scrape_each_chapter can't scrape some specific tag from " \
                          "page.")

                    return "Meet unknown scrape error, maybe scrape_each_chapter can't scrape some specific tag from " \
                           "page."

                if res[2]:
                    tmp['manga_id'], tmp['newest_epi'], tmp['newest_epi_name'] = manga_id, f.result()[0], f.result()[1]
                    socketio.emit('response', tmp)
                else:
                    continue

        # gevent.sleep(0)

        complete_info = dict()
        complete_info['manga_id'] = manga_id
        complete_info['completed'] = True
        socketio.emit('complete_info', complete_info)
        Current_download = ''

        manga_library[manga_id]['completed'] = True

        # print(manga_library)

        with open('/vanmanga/eng_config/manga_library.json', 'w', encoding='utf8') as f:
            json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
            f.write(json_tmp)

        # todo
        # sleep_time = (1 + int(random.random() * 2)) * 60
        #
        # gevent.sleep(sleep_time)

    else:
        print('No need to download.')


def download_chapter_task(chapter):
    global manga_library
    global Error_dict
    global Current_download
    global download_root_folder_path

    manga_id = chapter[0]
    manga_name = manga_library[manga_id]['manga_name']
    DG = DGmanga(manga_id)
    selected_array = chapter[1]

    Current_download = manga_id
    print(f'\n{manga_id} 已经开始下载..........\n')

    dt = datetime.datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)

    manga_library[manga_id]['add_date'] = utc_time.timestamp()

    socketio.emit('downloading_info', manga_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

        finish = list()

        for chp in selected_array:
            print(chp)
            # 如果其他线程的task已经被bloack，那么当前线程的章节任务暂缓, 如果不在这里加上gevent.sleep移交协程control，就会出现死锁，
            # 导致实际上DG实例已经在sleep后将control交还main，但是main自己相当于锁了自己，至此导致worker等待超时，被kill
            while Error_dict['g_error_flag']:
                gevent.sleep(0)
            # 这里传递的实际上时manga_library的引用，所以在dogemanga中的任何操作都会直接反应到内存的manga_library对象上，并非副本
            future = executor.submit(DG.download_single_chapter, chp, Error_dict, app, download_root_folder_path, manga_name)

            finish.append(future)
            gevent.sleep(2 + int(random.random() * 3))

        if gevent.getcurrent() is not gevent.hub.get_hub().parent:
            pass
        else:
            gevent.wait()

        for f in concurrent.futures.as_completed(finish):
            tmp = dict()
            # gevent.wait([f], timeout=0)
            res = f.result()

            if res == 502:
                print("Meet unknown scrape error, maybe download_single_chapter can't scrape some specific tag from " \
                      "page.")

                return "Meet unknown scrape error, maybe download_single_chapter can't scrape some specific tag from " \
                       "page."

            if res[2]:
                tmp['manga_id'], tmp['newest_epi'], tmp['newest_epi_name'] = manga_id, f.result()[0], f.result()[1]
                socketio.emit('response', tmp)
            else:
                continue

    complete_info = dict()
    complete_info['manga_id'] = manga_id
    complete_info['completed'] = True
    socketio.emit('complete_info', complete_info)
    Current_download = ''


def re_zip_task():
    print(f"########### 扫描开始！ ############")
    re_zip_run()
    print(f"########### 扫描完成 ############")
    socketio.emit('scan_completed')


# call entry function that boot scanning after first self server call
@app.before_first_request
def before_first_request():
    """
    init TaskQueue to make sure Q run under the Flask context, it works for socketio connection maintaining,
    for verify, you can print current thread of this function (won't mainThread)
    """
    print('########### 初始化开始 ############')
    global Q
    Q = TaskQueue(num_workers=1)
    Q.join()
    print('队列已经创建')
    # boot_scanning(manga_library)
    # init daily scheduled mission
    print('bootScanning完成，即将开始安排计划任务上线')
    scheduler.add_job(id='Dogemanga task', func=dogemangaTask, trigger='cron', hour='1', minute='30')
    scheduler.start()
    print('计划任务挂载')
    print(f"########### 初始化完成 ############")


class DogeSearch(Resource):
    def get(self):
        args = request.args
        search_name = args['manga_name']
        r = dict()

        if search_name == '':
            r['code'] = 456
            r['data'] = 'manga_name should not be empty!'

            return r

        DG = DGmanga('tmp')

        results = DG.search_manga(search_name)

        if results == 457:
            r['code'] = 457
            r['data'] = 'No manga searched.'

            return r

        else:
            r['code'] = 200
            r['data'] = results

            return r


class DogePost(Resource):

    def post(self):
        global manga_library
        global Q
        args = confirm_post_args.parse_args()
        manga_object = ast.literal_eval(args['manga_object'])
        manga_id = manga_object['manga_id']

        if manga_id not in manga_library:
            manga_library[manga_id] = make_manga_object(manga_object)
        else:
            return {'data': 'same id in library, no need to submit', 'code': 410}

        # 后台工作交由多线程执行，先返回200
        # Thread(target= confirm_comic_task, args= [manga_id]).start()
        Q.add_task(target=confirm_comic_task, manga_id=manga_id, dtype= '0')

        with open('/vanmanga/eng_config/manga_library.json', 'w', encoding='utf8') as f:
            json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
            f.write(json_tmp)

        return {'data': 'submitted', 'code': 200}


class DogeLibrary(Resource):
    def post(self):
        global manga_library

        r = [item for item in manga_library.values()]

        return {'data': r, 'code': 200}


class DogeCurDownloading(Resource):

    def get(self):
        global Current_download

        return {'data': Current_download, 'code': 200}


class DogeReZip(Resource):

    def get(self):
        gevent.threading.Thread(target=re_zip_task).start()

        gevent.sleep(0)

        return {'data': 'Re zip downloaded document begin', 'code': 200}


class DogeShortLib(Resource):
    global manga_library

    def post(self):
        payload = [{
            'manga_id': key,
            'manga_name': value['manga_name']
        } for key, value in manga_library.items()]

        return {'data': payload, 'code': 200}


class DogeGetManga(Resource):

    def get(self):
        args = request.args
        mangaId = args['manga_id']

        tempDG = DGmanga(mangaId)
        session = requests.session()
        chapter_array = tempDG.comic_main_page(mangaId, session)

        if chapter_array == 501:
            print('查询失败，无法访问指定漫画主页面，返回501')

            return {'data': 'error', 'code': 501}

        chapter_array = [{
            'chapter_title': item[0],
            'chapter_link': item[1]
        } for item in chapter_array]

        return {'data': chapter_array, 'code': 200}


class DogeReDownload(Resource):

    def post(self):
        args = redownload_post_args.parse_args()
        manga_id = args['manga_id']
        selected_array = ast.literal_eval(args['selected_array'])
        selected_array = [[item['chapter_title'], item['chapter_link']] for item in selected_array]

        Q.add_task(target=download_chapter_task, chapter=[manga_id, selected_array], dtype= '1')

        return {'data': 'submitted', 'code': 200}


api.add_resource(DogeSearch, '/api/dogemanga/search')
api.add_resource(DogePost, '/api/dogemanga/confirm')
api.add_resource(DogeLibrary, '/api/dogemanga/lib')
api.add_resource(DogeCurDownloading, '/api/dogemanga/cdl')
api.add_resource(DogeReZip, '/api/dogemanga/rezip')
api.add_resource(DogeShortLib, '/api/dogemanga/shortlib')
api.add_resource(DogeGetManga, '/api/dogemanga/confirmmanga')
api.add_resource(DogeReDownload, '/api/dogemanga/redownload')


# loop of self server call, run on mainThread, if call success, will terminate thread
def start_runner():
    def start_loop():
        print()
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://0.0.0.0:5000/mainpage/searchpage')
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)

            except:
                print('Server not yet started')
            gevent.sleep(1)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()

# socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)

# if __name__ == '__main__':
# serve(app, host='127.0.0.1', port= 5000)
# app.run(host='127.0.0.1', port= 5000, debug= True)
# start_runner()
# '''
# must turn off the use_reloader and make allow_unsafe_werkzeug to true,
# because if run under werkzeug reload env, werkzeug will run other process for checking modification on code,
# it means server will boot twice, due to the function of crawler, it will break thread safe and bring it to chaos :(
# '''
# socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
# socketio.run(app, host='127.0.0.1', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
