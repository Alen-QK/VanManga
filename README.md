# VanManga: 漫画资源抓取服务

<!-- [中文文档](https://github.com/wzl778633/vanIsLord/blob/master/README_cn.md) -->

<!-- [Server repo is here](https://github.com/star-wyx/drive) -->

A Python web crawler base on Flask + Vue.js, implements searching, crawling manga and progress monitoring functions.

Example scenarios for this project usage are: Crawling and saving manga resources from websites, servering other developed manga viewer front end.

This project has 2 parts currently, Front-End web-client server and Back-End server:
Front-End web-client server is based on Vue 2.x, Element-Ui & Nginx 1.23.0 (Which is the current repo).
Back-End server is based on Flask & Gunicorn 20.1.0.

![UI1](https://user-images.githubusercontent.com/37805183/223309012-1957706d-b734-43f9-8b10-93f6361979b6.png)
![UI2](https://user-images.githubusercontent.com/37805183/223309017-5cd1797f-abaf-4130-b6f5-6b3d0e2f855e.png)



## Table of Contents

- [What this project can do?](#What-this-project-can-do)
- [How To Install?](#How-To-Install)
- [How to use this system?](#How-to-use-this-system)
- [Demo](#demo)
- [Contributing](#contributing)
- [License](#license)

## What this project can do?

This project designed for manga resource collecting. It can extract manga pages from website and transform them to custom format and save loaclly. If you want to develop a manga viewer base on a manga server, you can have a try :)

The reason we build VanManga is we want to build a private manga service for our friends and chat groups, without ads disturbance from other manga websites.

The main features for this repository are:

1. 🔍 **Searching manga from web**. Enter the manga name in search box, you will get top 10 results from source website. Than you can select and download whatever you want.
2. 🛫 **Unique key of each manga**. Same manga will only be allowed to download once in real disk with a unique key. So if backend checks one manga which you select have been downloaded previously, it will inform you.
3. 📋 **Downloading queue**. All dowanloading tasks will be added in a task queue and waiting for executing.
4. 🔄 **Daily check for manga updating** Flask APScheduler will execute a checking tasks everyday for updating downloaded manga if they are updated by website.
5. 🖥️ **Dashboard monitoring downloading**. You can check dashboard tab to view downloading prograss of manga, it will show and update the lastest episode name which have been downloaded and manga status in backend with WebSocket. 
6. 🗃️ **Re zip all manga files**. If you need to re zip your loacl manga files, backend provides a api to check and re zip files in order to reduce storage comsumption.
7. **And maybe More in the future!**

## How To Install?

Currently, This project is specify built for our own server. But we will build a general version which will have config customize. 

We use docker to build this project. So you could try this DockerFile to build your own image of this project:
```
#Boot Ubuntu image
FROM python:3.9.7
#Switch to specify project folder
WORKDIR /vanmanga

#Add project files to container
ADD ./{your Project folder name} /{your Project folder name}

#Install dependences
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

#Expose project port
EXPOSE 5000
#Boot project
ENTRYPOINT gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5000 main:app
```
**Cautions: DO NOT expose your local port outside your server in any kind of situation!**

Then, when you boot your project image, you need to set you local port to connect exposing project port, and connect your local downloaded manga path to '/downloaded' path inside project. Then you will see downloaded manga in your local specify path.  

## How to use this system?

// TODO May need more update in the future.

## Demo

// TODO May need more update in the future.

<!-- ## Demo

nighttown.aijiangsb.com or https://aijiangsb.com:9070

```
user: test
pwd: **Ask me if you want to see the demo**

For Special Demo only. So plz DO NOT submit any files.
``` -->

## Contributing
### Contributors

Currently 2 main contributors are working for this project. 
<a href="https://github.com/Alen-QK/python-vanmanga-crawler/graphs/contributors">
Tom "Van" Wang & Alen "Alen" Qi
</a>

We will welcome any contribution for this project! 


## License

[MIT](LICENSE)

