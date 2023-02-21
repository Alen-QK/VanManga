from flask import Flask
from flask_apscheduler import APScheduler
from dogemanga import entry

app = Flask(__name__)
scheduler = APScheduler()

@app.route('/')
def index():
    return 'Hello world!'

def dogemangaTask():
    entry('UsprF-z2')

if __name__ == '__main__':
    scheduler.add_job(id= 'DogeManga task', func= dogemangaTask, trigger= 'interval', seconds= 10)
    scheduler.start()
    app.run(host= '127.0.0.1', port= 5000)