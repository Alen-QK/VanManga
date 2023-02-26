import concurrent.futures
import random
import time
import requests
import threading
from modules.TaskQueue import TaskQueue
from threading import current_thread
from flask import Flask, g, current_app



app = Flask(__name__)

Q = None

arr_library = {'a': [i for i in range(10)], 'b': [i for i in range(11, 20)], 'c': [i for i in range(21, 30)]}
Error_dict = {'g_error_flag': False, 'g_error_count': 0, 'g_wait_time': 40}

counter = 0

def boot_scanning(manga_library):
        global Q
        global counter
        

        for manga in manga_library.values():
                Q.add_task(target= confirm_comic_task, arr= manga)
                print(f"\n add to the queue {counter}\n")
                counter += 1
                # confirm_comic_task(manga['manga_id'])


def scrape_each_chapter(chapter):
    chapter['g_error_count'] += 1

    print(threading.current_thread().getName(), chapter['g_error_count'])


def confirm_comic_task(arr):
    print(f'\n已经开始下载..........\n')

    global Error_dict

    # for i in chapters_array:
    #     print(i)
    #     print(f'DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD\n')
    #     time.sleep(1)

    with concurrent.futures.ThreadPoolExecutor(max_workers= 3) as executor:
        # executor.map(chapter_comic_page, chapters_array)
        for i in range(10):
            # 这里传递的实际上时manga_library的引用，所以在dogemanga中的任何操作都会直接反应到内存的manga_library对象上，并非副本
            executor.submit(scrape_each_chapter, Error_dict)

    print(Error_dict)


@app.before_first_request
def before_first_request(): 
    global Q 
    Q = TaskQueue(num_workers=1)
    Q.join()
    boot_scanning(arr_library)
    print(f"########### Restarted, first request @ ############")

@app.route("/")
def hello():
    return "Hello World!"

def start_runner():
    def start_loop():
        not_started = True
        while not_started:
            print('In start loop')
            try:
                r = requests.get('http://127.0.0.1:5000/')
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
    # scheduler.add_job(id= 'Dogemanga task', func= dogemangaTask, trigger= 'cron', hour='1', minute='30')
    # scheduler.start()

    # serve(app, host='127.0.0.1', port= 5000)
    start_runner()
    app.run(host='127.0.0.1', port= 5000, debug= True, use_reloader= False)


