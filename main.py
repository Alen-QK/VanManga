from gevent import monkey
monkey.patch_all()

import os
import threading
import time
import random
import requests
import json
import ast
import concurrent.futures

from modules.make_manga_object import make_manga_object
from modules.TaskQueue import TaskQueue

from flask import Flask, redirect, render_template
from flask_socketio import SocketIO, send, emit
from flask_apscheduler import APScheduler
from flask_restful import Api, Resource, reqparse, request
from flask_cors import CORS

from modules.DGmanga import DGmanga

app = Flask(__name__, static_folder= 'frontend/static', template_folder= 'frontend/static/templates')
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
    for manga in manga_library.values():
        # print(manga)

        if manga['completed'] == False:
            Q.add_task(target=confirm_comic_task, manga_id=manga['manga_id'])
            print(f"\n{manga['manga_id']} add to the queue\n")
        else:
            DG = DGmanga(manga['manga_id'])
            current_manga_length = DG.check_manga_length()

            if current_manga_length == 501:
                return 'Might meet human check, shutdown the task.'

            history_length = manga['last_epi']

            if history_length < current_manga_length:
                Q.add_task(target=confirm_comic_task, manga_id=manga['manga_id'])
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
        return 'Might meet human check, shutdown the task.'

    target_manga = manga_library[manga_id]
    history_length = target_manga['last_epi']
    manga_name = target_manga['manga_name']

    if history_length <= current_manga_length:
        Current_download = manga_id
        print(f'\n{manga_id} 已经开始下载..........\n')

        socketio.emit('downloading_info', manga_id)

        start = 1 if history_length == 1 else history_length + 1
        end = current_manga_length

        chapters_array = DG.generate_chapters_array(start, end, download_root_folder_path, manga_name)

        if chapters_array == 501:
            return 'Might meet human check, shutdown the task.'

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:

            finish = list()

            for idx, chapter in enumerate(chapters_array):
                # 如果其他线程的task已经被bloack，那么当前线程的章节任务暂缓
                while Error_dict['g_error_flag']:
                    print('线程停止中')
                # 这里传递的实际上时manga_library的引用，所以在dogemanga中的任何操作都会直接反应到内存的manga_library对象上，并非副本
                future = executor.submit(DG.scrape_each_chapter, chapter, manga_library, Error_dict, start, idx)
                finish.append(future)
                time.sleep(2 + int(random.random() * 3))

            for f in concurrent.futures.as_completed(finish):
                tmp = dict()
                res = f.result()

                if res == 502:
                    return "Meet unknown scrape error, maybe scrape_each_chapter can't scrape some specific tag from " \
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

        manga_library[manga_id]['completed'] = True

        # print(manga_library)

        with open('/vanmanga/eng_config/manga_library.json', 'w', encoding='utf8') as f:
            json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
            f.write(json_tmp)

    else:
        print('No need to download.')


# call entry function that boot scanning after first self server call
@app.before_first_request
def before_first_request():
    """
    init TaskQueue to make sure Q run under the Flask context, it works for socketio connection maintaining,
    for verify, you can print current thread of this function (won't mainThread)
    """
    global Q
    Q = TaskQueue(num_workers=1)
    Q.join()
    boot_scanning(manga_library)
    # init daily scheduled mission
    scheduler.add_job(id='Dogemanga task', func=dogemangaTask, trigger='cron', hour='1', minute='30')
    scheduler.start()
    print(f"########### Restarted, first request @ ############")


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
        Q.add_task(target=confirm_comic_task, manga_id=manga_id)

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


api.add_resource(DogeSearch, '/api/dogemanga/search')
api.add_resource(DogePost, '/api/dogemanga/confirm')
api.add_resource(DogeLibrary, '/api/dogemanga/lib')
api.add_resource(DogeCurDownloading, '/api/dogemanga/cdl')


# loop of self server call, run on mainThread, if call success, will terminate thread
def start_runner():
    def start_loop():
        print()
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:5000/mainpage/searchpage')
                if r.status_code == 200:
                    print('Server started, quiting start_loop')
                    not_started = False
                print(r.status_code)

            except:
                print('Server not yet started')
            time.sleep(1)

    print('Started runner')
    thread = threading.Thread(target=start_loop)
    thread.start()


if __name__ == '__main__':
    # serve(app, host='127.0.0.1', port= 5000)
    # app.run(host='127.0.0.1', port= 5000, debug= True)
    start_runner()
    '''
    must turn off the use_reloader and make allow_unsafe_werkzeug to true, 
    because if run under werkzeug reload env, werkzeug will run other process for checking modification on code,
    it means server will boot twice, due to the function of crawler, it will break thread safe and bring it to chaos :(
    '''
    socketio.run(app, host='127.0.0.1', port=5000, debug=True, use_reloader=False)
    # socketio.run(app, host='127.0.0.1', port=5000, use_reloader=False, allow_unsafe_werkzeug=True)
