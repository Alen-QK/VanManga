# VanManga  
<div align="center">
  
![VanLogo](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/e4f30d77-a6fe-421a-b411-af73134ffdfa)  

![Brands](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/654e0b06-45e4-4754-8841-51abb64d019e)  

![Preview](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/40b1bfc5-0e74-41e3-9fe0-07ba6882ca12)

VanManga is a lightweight, feature rich, cross-platform manga crawling server. This application is designed to crawl and manage manga resources from manga source, enabling functions such as manga reading and backup.
</div>  
  
  
## What VanManga can do?
1. 🔍 **Searching manga from web**. Enter the manga name in search box, you will get top 10 results from source website. Than you can select and download whatever you want.
2. ⚠️ **Management of manga**. To ensure a diverse yet non-redundant collection of manga resources, when submitting a download request to the server, it will examine locally stored similar resources and, if necessary, provide users with confirmation options.
3. 📋 **Downloading queue**. All downloading tasks will be added in a task queue and waiting for executing.
4. 🔄 **Daily check for manga updating** Manga server will execute a checking task every day for updating downloaded manga if they are updated by source website.
5. 🖥️ **Dashboard monitoring downloading**. You can check dashboard tab to view downloading progress of manga, it will show and update the latest episode name dynamically which have been downloaded and manga status in server with WebSocket. 
6. 🗃️ **Re-zip all manga files**. If you need to re-zip your local manga files, server provides a function to check and re-zip local files in order to reduce storage consumption.
7. 🔧 **Re-downloading single chapter**. Sometimes due to the unstable web connection, some chapters will download failed. Now you can use re-downloading function to fix broken image in single chapter of mangas
8. **And maybe more in the future!**
  
  

## How to Install?
Currently, this project is available for local deployment through Docker Hub. So you can run your local VanManga server with customized HTTP port.
1. Please ensure you have installed [Docker](https://www.docker.com/) in your system. On Windows or MacOS, we recommend you to install [Docker Desktop](https://www.docker.com/products/docker-desktop/) to experience easier deployment. If you use Linux, feel free to use command line to do it.
2. After installing Docker, please use this following command to get the latest version of VanManga in Docker:
    ```
   docker pull wzl778633/vanislord_manga:latest
   ```
3. To run your Docker container correctly, you need to set up environment variables \  volumes \ port:
    - Environment variables
        >**PYTHONUNBUFFERED**: used for printing server log in Docker container, default is 1  
        **MANGA_BASE_URL**: URL which you use to connect backend, default is http://localhost:5000. If you are using bridge in your Docker, you should change 'localhost' to your bridge internal IP.  
        **MANGA_BASE_WEBSOCKET_URL**: URL which you expose to external, this is used for WebSocket services, default is http://localhost:5000.
    - Volumes
        > { local path to manga lib } <==> /downloaded    
        { local path to config files } <==> /vanmanga/eng_config
    - Port
        > 5000:5000 /* or any port you want */
    
   You can use following command directly, or set up above variables in Docker Desktop GUI:  
    ```
   docker run --name /*Your container name*/ \
    -e PYTHONUNBUFFERED=1 \
    -e MANGA_BASE_URL=http://localhost:5000  \
    -e MANGA_BASE_WEBSOCKET_URL=http://localhost:5000  \
    --mount type=bind,source=/*local machine address to manga lib*/,target=/downloaded \
    --mount type=bind,source=/*local machine address to config file*/,target=/vanmanga/eng_config \
    -p 5000:5000
    wzl778633/vanislord_manga:latest
   ```
4. Once container is running, you need to open the website with the URL you have settled(E.g. http://localhost:5000) to start initialization. Currently, the website will be blocked during the initialization, but you can see the process of initialization inside Docker container's logs.
    - The purpose of this initialization is to scan your existing `manga_library.json` and add all your existing manga information to the server and check the update.
  
  
## How to use?
1. **Searching Manga**  
    We are using [DogeManga](https://dogemanga.com/) as source.  
    Enter manga name which you want to download in search box. It will show the top 10 related result in the browser. **Caution:** We will warn you if we detected you are adding mangas which may exist in the library based on name.  
    ![s1](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/b0daddd5-faa3-41e6-aaba-2b18c8ea43a7)     
    ![s2](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/1b7ab286-64c6-4069-83dc-bae342fdc49a)
2. **Downloading Manga**  
    Select any mangas in searching results, after a short confirmation it will initiate downloading task. Currently, we will download all the chapters inside this manga(including volumes, specials, extras ...). 
    ![s3](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/b27b1631-0faa-46a2-96f9-645b3929907e)  
    ![s4](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/2b0d9c7a-e343-4ad6-8a0a-57493a87460e)
3. **Manga Lib Dashboard**  
    All the mangas you downloaded can be found in this dashboard. You can see the current status for each manga(E.g. Downloading / Queuing / Completed ...).  
    Currently, dashboard only shows the latest chapter name which have been downloaded for you to track the status from each manga. 
    ![s4 5](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/9246f8ff-01a6-44cd-a360-10d401eafb25) 
    ![s5](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/3a1d2837-fad0-46bc-a953-d3d1c080eec3)
4. **Re-downloading**  
    For each manga if you found any (chapter / volume / ... etc.). is broken during you reading. You can simply request re-download to that specific (chapter / volume / ... etc.).
    ![s6](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/4b0cbb19-fb58-40ab-9e68-3e73175efa78) 
    ![s7](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/0b2aca2f-1a40-4d66-9671-0992f1b9ac61)
    ![s8](https://github.com/Alen-QK/python-vanmanga-crawler/assets/37805183/d19194c8-e273-4dbe-9439-53e54b0a4a3d)
5. **Reading**  
    Currently, our file structure is built to support [Kavita](https://github.com/Kareadita/Kavita). We highly recommend you to use it as your manga server. You can easily manage your manga files with its Web GUI and read with its reader. It also provides support to [Paperback](https://paperback.moe/) for IOS devices and [Tachiyomi](https://tachiyomi.org/) for Android. You can find useful guides for setup below.  
    - Kavita: https://wiki.kavitareader.com/en
    - Paperback: https://wiki.kavitareader.com/en/guides/misc/paperback
    - Tachiyomi: https://wiki.kavitareader.com/en/guides/misc/tachiyomi
   
    But feel free to use any manga server you prefer if you don't like Kavita!
  
  
## Demo

//ToDo
  
  
## Contributing
### Contributors

Currently, 2 main contributors are working for this project. 
<a href="https://github.com/Alen-QK/python-vanmanga-crawler/graphs/contributors">
Tom "Van" Wang & Kun "Alen" Qi
</a>

We will welcome any contribution for this project! 
  
  
## License

[MIT](LICENSE)
