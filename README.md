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
ADD {your local project folder path}

#Install dependences
RUN pip3 install -r requirements.txt
RUN pip3 install gunicorn

#Expose project port
EXPOSE 5000
#Boot project
ENTRYPOINT gunicorn -k geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 -b 0.0.0.0:5000 main:app
```

**Cautions: DO NOT expose your local port outside your server in any kind of situation!**

Then, when you boot your project image, you should map your port and specific local path which server needs. Here is example of docker setting:

```
Ports: 5500:5000/tcp  

Volumes:  
{local server config path} => /vanmanga/eng_config
{local server manga download path} => /downloaded  

Environment variables(if using OS X):  
PYTHONUNBUFFERED => 1
```

## How to use this system?

1. **Server Boosting**  
For boosting your manga server, you need to call server path in browser. Eg: *localhost:5500*
  

2. **Searching Manga**  
Enter manga name which you want to download in search box.    
![s1](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/b0daddd5-faa3-41e6-aaba-2b18c8ea43a7)    
Click search button, server will return the top 10 related results.      
![s2](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/1b7ab286-64c6-4069-83dc-bae342fdc49a)    
  

3. **Downloading Manga**  
Choose one mange which you want to download in searching result, click the card.    
![s3](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/b27b1631-0faa-46a2-96f9-645b3929907e)  
Check manga information, if they are correct, click yes button to submit downloading task.     
![s4](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/2b0d9c7a-e343-4ad6-8a0a-57493a87460e)    
  

4. **Tracking Downloading Status**  
Click this tab to open downloading management window.    
![s4 5](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/9246f8ff-01a6-44cd-a360-10d401eafb25)    
There are two information of downloading status: **1. the newest chapter name in library 2. completed**    
![s5](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/3a1d2837-fad0-46bc-a953-d3d1c080eec3)    
**The newest chapter name in library**    
Due to multi-threaded downloads, the script cannot download all chapters in order due to the different download progress during the actual download process, so only the latest chapter names that have been downloaded by the current script are listed here.    
**Completed**    
It will display whether the current comic is being downloaded for the first time. The status is divided into downloading, queuing, and completed.
  

5. **Re-downloading Specific Chapters**  
Click re-downloading button of manga which you want to repair.  
![s6](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/4b0cbb19-fb58-40ab-9e68-3e73175efa78)  
Server will show all available chapter in a modal window.
![s7](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/0b2aca2f-1a40-4d66-9671-0992f1b9ac61)
Select chapters which you want to re-download and click yes button to submit tasks to server.
![s8](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/d19194c8-e273-4dbe-9439-53e54b0a4a3d)

## Demo

[VanManga](https://aijiangsb.com:7777/mainpage/mangaku)

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
Tom "Van" Wang & Kun "Alen" Qi
</a>

We will welcome any contribution for this project! 


## License

[MIT](LICENSE)

