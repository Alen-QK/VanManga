from queue import Queue
from gevent.threading import Thread

doing = []


class TaskQueue(Queue):
    def __init__(self, num_workers=1):
        Queue.__init__(self)
        self.num_workers = num_workers
        self.start_workers()

    def add_task(self, **kwargs):
        kwargs = kwargs or {}
        self.put((kwargs))

    def start_workers(self):
        for i in range(self.num_workers):
            t = Thread(target=self.worker)
            print(t.getName() + '/////////////')
            t.daemon = True
            print('daemon thread on')
            t.start()
            print('Thread on')

    def worker(self):
        while True:
            # tupl = self.get()
            current_task = self.get()
            task = current_task['target']
            dtype = current_task['dtype']
            manga_id = ''
            # 添加执行中
            doing.append(current_task)
            # 执行
            if dtype == '0':
                manga_id = current_task['manga_id']
                print('当前队列中执行的漫画是：' + manga_id)
                task(manga_id)
            elif dtype == '1':
                manga_id = current_task['chapter'][0]
                print('当前队列中执行的漫画是：' + manga_id)
                task(current_task['chapter'])

            self.task_done()
            # 移除执行中
            doing.remove(current_task)
            print(f"\n{manga_id} removed from queue\n")

    # def worker(self):
    #     while True:
    #         # tupl = self.get()
    #         current_task = self.get()
    #         task = current_task['target']
    #         # 添加执行中
    #         doing.append(current_task)
    #         # 执行
    #         print(current_task)
    #         task(current_task['arr'])
    #         self.task_done()
    #         # 移除执行中
    #         doing.remove(current_task)
    #         print(f"\n{current_task['arr']} removed from queue\n")
