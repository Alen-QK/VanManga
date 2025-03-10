import gevent.monkey

from utils.flaresolverr_bypasser import flaresolverr_bypasser
from utils.kavita_lib_pull import kavita_lib_pull
from utils.kavita_scan_folder import kavita_scan_folder
from utils.lib_pagination import libPagination
from utils.thumbnails_creator import thumbnails_creator

gevent.monkey.patch_all()

import os
import gevent
import random
import json
import ast
import concurrent.futures
import datetime
import copy
import shutil
import requests

from utils.make_manga_object import make_manga_object
from utils.TaskQueue import TaskQueue
from utils.re_zip_downloaded import re_zip_run
from utils.duplicate_check import duplicate_check

from flask import Flask, render_template, send_file
from flask_socketio import SocketIO
from flask_apscheduler import APScheduler
from flask_restful import Api, Resource, reqparse, request
from flask_cors import CORS

from datetime import timezone
from DrissionPage import SessionPage

from modules.DGmanga import DGmanga

app = Flask(
    __name__,
    static_folder="frontend/static",
    template_folder="frontend/static/templates",
)
CORS(app, expose_headers=["Content-Disposition"])
api = Api(app)
socketio = SocketIO(app, cors_allowed_origins="*")
scheduler = APScheduler()

LIB_PATH = "/vanmanga/eng_config/manga_library.json" if os.environ.get("LIB_PATH") is None else os.environ.get(
    "LIB_PATH")
# LIB_PATH = "./eng_config/manga_library.json" # ILLYA
FLARESOLVERR_URL = "" if os.environ.get("FLARESOLVERR_URL") is None else os.environ.get("FLARESOLVERR_URL")
KAVITA_BASE_URL = "" if os.environ.get("KAVITA_BASE_URL") is None else os.environ.get("KAVITA_BASE_URL")
KAVITA_EXPOSE_URL = "" if os.environ.get("KAVITA_EXPOSE_URL") is None else os.environ.get("KAVITA_EXPOSE_URL")
KAVITA_ADMIN_APIKEY = "" if os.environ.get("KAVITA_ADMIN_APIKEY") is None else os.environ.get("KAVITA_ADMIN_APIKEY")
NUMBER_OF_WORKERS = 2 if os.environ.get("NUMBER_OF_WORKERS") is None else int(os.environ.get("NUMBER_OF_WORKERS"))

if os.path.exists(LIB_PATH):
    try:
        manga_library = json.load(open(LIB_PATH, encoding="utf-8"))
    except Exception as e:
        print(e)
else:
    manga_library_content = {}
    os.mknod(LIB_PATH)  # ILLYA

    with open(LIB_PATH, "w", encoding="utf8") as f:
        json_tmp = json.dumps(manga_library_content, indent=4, ensure_ascii=False)
        f.write(json_tmp)

# post format
# 提交漫画API
confirm_post_args = reqparse.RequestParser()
confirm_post_args.add_argument(
    "manga_object",
    type=str,
    help="manga_object of the manga is required",
    required=True,
)
confirm_post_args.add_argument(
    "submit_sign", type=str, help="submit_sign of submission is required", required=True
)
lib_post_args = reqparse.RequestParser()
lib_post_args.add_argument("start", type=str)
lib_post_args.add_argument("limit", type=str)
# 单章下载API
redownload_post_args = reqparse.RequestParser()
redownload_post_args.add_argument(
    "manga_id", type=str, help="manga_id of the manga is required", required=True
)
redownload_post_args.add_argument(
    "selected_array",
    type=str,
    help="redownload chapter array is required",
    required=True,
)
# 改变漫画连载状态API
change_download_args = reqparse.RequestParser()
change_download_args.add_argument(
    "manga_id", type=str, help="manga_id is required", required=True
)
# change_download_args.add_argument(
#     "status", type=str, help="status is required", required=True
# )
delete_manga_args = reqparse.RequestParser()
delete_manga_args.add_argument(
    "manga_id", type=str, help="manga_id is required", required=True
)
kavita_login_args = reqparse.RequestParser()
kavita_login_args.add_argument("username", type=str)
kavita_login_args.add_argument("password", type=str)
token_refresh_args = reqparse.RequestParser()
token_refresh_args.add_argument("jwt", type=str)
token_refresh_args.add_argument("refreshToken", type=str)

Current_download = ""
Q = None
manga_library = json.load(open(LIB_PATH, encoding="utf-8"))
Error_dict = {"g_error_flag": False, "g_error_count": 0, "g_wait_time": 40}
CF_dict = {
    "cf_activate": False,
    "cf_clearance_value": "",
    "cf_userAgent": "",
    "updateTime": None,
}
# env_config = json.load(open('eng_config/config.json', encoding='utf-8'))
download_root_folder_path = "/downloaded"


# download_root_folder_path = "./downloaded" # ILLYA

@app.route("/")
def go_to_mainpage():
    return render_template("index.html")


@app.route("/<path:fallback>")
def fallback(fallback):
    if (
            fallback.startswith("css/")
            or fallback.startswith("js/")
            or fallback.startswith("img/")
            or fallback == "favicon.ico"
            or fallback.startswith("fonts/")
    ):
        return app.send_static_file(fallback)
    elif fallback.startswith("mainpage/"):
        return app.send_static_file("templates/index.html")
    else:
        return app.send_static_file("templates/index.html")


def dogemangaTask():
    global manga_library
    print("\n########## Start Daily Update Task ##########\n")
    boot_scanning(manga_library)
    print("\n########## Daily Update Task Over ##########\n")


def kavitaTask():
    global manga_library
    print("\n########## Start Kavita Lib Update Task ##########\n")
    manga_library = kavita_lib_pull(manga_library)
    print("\n########## Kavita Lib Update Task Over ##########\n")


def boot_scanning(manga_library):
    global CF_dict
    print("########## 开始每日任务 ##########")

    # 检查Cloudflare状态
    print("\n########## 检查CloudFlare状态..... ##########")
    cfMonitor()

    if CF_dict["cf_activate"]:
        print("\n########## CloudFlare监察已启动，应用相关处理机制 ##########")

        if scheduler.get_job("CFMonitor"):
            pass
        else:
            scheduler.add_job(
                id="CFMonitor", func=cfMonitor, trigger="interval", seconds=720
            )
    else:
        print("\n########## CloudFlare已关闭 ##########")
        if scheduler.get_job("CFMonitor"):
            scheduler.remove_job("CFMonitor")
        else:
            pass

    if len(manga_library) == 0:
        print("\n########## 漫画库长度为0，跳过初始化 ##########")
        return

    for manga in reversed(manga_library.values()):
        print("\n扫描漫画：" + manga["manga_name"])

        if manga["completed"] == False:
            print(manga["manga_name"] + "/" + manga["manga_id"] + "未完成初次抓取")
            Q.add_task(target=confirm_comic_task, manga_id=manga["manga_id"], dtype="0")
            print(f"\n{manga['manga_id']} add to the queue\n")
        else:
            if manga["download_switch"] == 1:
                print("该漫画已完结，无需检查更新\n")
                continue
            else:
                print(
                    manga["manga_name"]
                    + "/"
                    + manga["manga_id"]
                    + "已完成初次抓取，检查更新..."
                )
                DG = DGmanga(manga["manga_id"])
                current_manga_length, serialization = DG.check_manga_length(CF_dict)

                if current_manga_length == 501:
                    print("该漫画在源暂时不可用，暂时跳过更新\n")
                    continue

                history_length = manga["last_epi"]

                print(
                    manga["manga_name"]
                    + "历史长度是"
                    + str(history_length)
                    + ","
                    + "当前长度是"
                    + str(current_manga_length)
                )

                if history_length < current_manga_length:
                    print("当前长度 > 历史长度，即将加入队列更新...")
                    Q.add_task(
                        target=confirm_comic_task, manga_id=manga["manga_id"], dtype="0"
                    )
                    print(f"\n{manga['manga_id']} add to the queue\n")
        # 因为初始化扫描本来是不限速的，但是如果此时加入了新的下载任务，那么同时访问多个源地址可能就会触发block，安全起见，应该在每扫描完一个后暂停1-3s。
        gevent.sleep(1)

    print("\n########## 每日任务完成 ##########")


# 实际上后台下载选定漫画的task
def confirm_comic_task(manga_id):
    global manga_library
    global Error_dict
    global CF_dict
    global Current_download
    global download_root_folder_path

    DG = DGmanga(manga_id)
    current_manga_length, serialization = DG.check_manga_length(CF_dict)

    if current_manga_length == 501:
        print("\nMight meet human check, shutdown the task.\n")
        return "Might meet human check, shutdown the task."

    target_manga = manga_library[manga_id]
    history_length = target_manga["last_epi"]
    manga_name = target_manga["manga_name"]

    if history_length <= current_manga_length:
        Current_download = manga_id
        print(f"\n{manga_id} 已经开始下载..........\n")

        socketio.emit("downloading_info", manga_id)

        dt = datetime.datetime.now(timezone.utc)
        utc_time = dt.replace(tzinfo=timezone.utc)

        manga_library[manga_id]["add_date"] = utc_time.timestamp()

        start = 1 if history_length == 1 else history_length + 1
        end = current_manga_length

        chapters_array = DG.generate_chapters_array(
            start, end, download_root_folder_path, manga_name, CF_dict
        )

        if chapters_array == 501:
            print("\nMight meet human check, shutdown the task.\n")
            return "Might meet human check, shutdown the task."

        with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_WORKERS) as executor:
            finish = list()

            for idx, chapter in enumerate(chapters_array):
                # 如果其他线程的task已经被block，那么当前线程的章节任务暂缓, 如果不在这里加上gevent.sleep移交协程control，就会出现死锁，
                # 导致实际上DG实例已经在sleep后将control交还main，但是main自己相当于锁了自己，至此导致worker等待超时，被kill
                while Error_dict["g_error_flag"]:
                    gevent.sleep(0)
                # 这里传递的实际上时manga_library的引用，所以在dogemanga中的任何操作都会直接反应到内存的manga_library对象上，并非副本
                future = executor.submit(
                    DG.scrape_each_chapter,
                    chapter,
                    manga_library,
                    Error_dict,
                    start,
                    idx,
                    app,
                    CF_dict,
                )

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
                    print(
                        "Meet unknown scrape error, maybe scrape_each_chapter can't scrape some specific tag from "
                        "page."
                    )

                    return (
                        "Meet unknown scrape error, maybe scrape_each_chapter can't scrape some specific tag from "
                        "page."
                    )

                if res[0] == 503:
                    print(f"单章连续抓取失败超过10次，跳过该章节: {res[1]}")
                    continue

                if res[2]:
                    tmp["manga_id"], tmp["newest_epi"], tmp["newest_epi_name"] = (
                        manga_id,
                        f.result()[0],
                        f.result()[1],
                    )
                    socketio.emit("response", tmp)
                else:
                    continue

        # gevent.sleep(0)

        complete_info = dict()
        complete_info["manga_id"] = manga_id
        complete_info["completed"] = True
        socketio.emit("complete_info", complete_info)
        Current_download = ""

        # 仅在初次抓取时根据抓取到的连载状态设置默认的下载开关值
        if manga_library[manga_id]["completed"] == False:
            manga_library[manga_id]["download_switch"] = serialization

        manga_library[manga_id]["completed"] = True
        manga_library[manga_id]["serialization"] = serialization

        # print(manga_library)
        if kavita_scan_folder(f"{manga_name}${manga_id}"):
            print("########### 已成功提交文件扫描 ###########")
        else:
            print("########### 文件扫描提交失败 ###########")

        with open(LIB_PATH, "w", encoding="utf8") as f:
            json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
            f.write(json_tmp)

        # todo
        # sleep_time = (1 + int(random.random() * 2)) * 60
        #
        # gevent.sleep(sleep_time)

    else:
        print("No need to download.")


def download_chapter_task(chapter):
    global manga_library
    global Error_dict
    global Current_download
    global download_root_folder_path
    global CF_dict

    manga_id = chapter[0]
    manga_name = manga_library[manga_id]["manga_name"]
    DG = DGmanga(manga_id)
    selected_array = chapter[1]

    Current_download = manga_id
    print(f"\n{manga_id} 已经开始下载..........\n")

    dt = datetime.datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)

    manga_library[manga_id]["add_date"] = utc_time.timestamp()

    socketio.emit("downloading_info", manga_id)

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_WORKERS) as executor:
        finish = list()

        for chp in selected_array:
            print(chp)
            # 如果其他线程的task已经被bloack，那么当前线程的章节任务暂缓, 如果不在这里加上gevent.sleep移交协程control，就会出现死锁，
            # 导致实际上DG实例已经在sleep后将control交还main，但是main自己相当于锁了自己，至此导致worker等待超时，被kill
            while Error_dict["g_error_flag"]:
                gevent.sleep(0)
            # 这里传递的实际上时manga_library的引用，所以在dogemanga中的任何操作都会直接反应到内存的manga_library对象上，并非副本
            future = executor.submit(
                DG.download_single_chapter,
                chp,
                Error_dict,
                app,
                download_root_folder_path,
                manga_name,
                CF_dict,
            )

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
                print(
                    "Meet unknown scrape error, maybe download_single_chapter can't scrape some specific tag from "
                    "page."
                )

                return (
                    "Meet unknown scrape error, maybe download_single_chapter can't scrape some specific tag from "
                    "page."
                )

            if res[2]:
                tmp["manga_id"], tmp["newest_epi"], tmp["newest_epi_name"] = (
                    manga_id,
                    f.result()[0],
                    f.result()[1],
                )
                socketio.emit("response", tmp)
            else:
                continue

    complete_info = dict()
    complete_info["manga_id"] = manga_id
    complete_info["completed"] = True
    socketio.emit("complete_info", complete_info)
    Current_download = ""

    if kavita_scan_folder(f"{manga_name}${manga_id}"):
        print("########### 已成功提交文件扫描 ###########")
    else:
        print("########### 文件扫描提交失败 ###########")


def re_zip_task():
    print(f"########### 扫描开始！ ############")
    re_zip_run()
    print(f"########### 扫描完成 ############")
    socketio.emit("scan_completed")


def cfMonitor():
    global CF_dict

    if FLARESOLVERR_URL == "":
        print("\n########### 未配置FlareSolverr，关闭cfMonitor功能 ############")
        (
            CF_dict["cf_activate"],
            CF_dict["cf_clearance_value"],
            CF_dict["cf_userAgent"],
            CF_dict["updateTime"],
        ) = (False, "", "", None)
        return

    url = "https://dogemanga.com"
    drissionSession = SessionPage()
    drissionSession.get(url)
    response = drissionSession.response

    # # 防止网络波动，导致response为None
    # if not response:
    #     cfMonitor()

    # 说明CF启动了人机交互检查，需要通过flaresovlerr来通过验证，并获取cookie
    if response.status_code == 403 or "?__cf_chl_rt_tk" in response.text:
        CF_dict = flaresolverr_bypasser(CF_dict, url)
        print(f"\n########### 已经更新CF的验证信息 ############")

    # 否则说明dogemanga关闭了CF的检测，关闭CF_dict和绕过的所有相关机制
    else:
        print("\n########### CF的验证机制暂时关闭，重置验证信息 ############")
        (
            CF_dict["cf_activate"],
            CF_dict["cf_clearance_value"],
            CF_dict["cf_userAgent"],
            CF_dict["updateTime"],
        ) = (False, "", "", None)


class DogeSearch(Resource):
    global CF_dict

    def get(self):
        args = request.args
        search_name = args["manga_name"]

        print(f"\nSearching API is working, search name is {search_name}")

        r = dict()

        if search_name == "":
            r["code"] = 456
            r["data"] = "manga_name should not be empty!"

            return r

        DG = DGmanga("tmp")

        results = DG.search_manga(search_name, CF_dict)

        if results == 457:
            r["code"] = 457
            r["data"] = "No manga searched."

            return r

        else:
            r["code"] = 200
            r["data"] = results

            return r


class DogePost(Resource):
    def post(self):
        global manga_library
        global Q
        args = confirm_post_args.parse_args()
        manga_object = ast.literal_eval(args["manga_object"])

        print(f"\nManga submitting API is working, manga_object is:\n{manga_object}")

        submit_sign = args["submit_sign"]
        manga_id = manga_object["manga_id"]

        if submit_sign == "0":
            if manga_id not in manga_library:
                manga_name = manga_object["manga_name"]

                potential_matches = duplicate_check(manga_name, manga_library)

                if potential_matches:
                    return {"data": potential_matches, "code": 411}
                else:
                    manga_library[manga_id] = make_manga_object(manga_object)
            else:
                return {"data": "same id in library, no need to submit", "code": 410}
        else:
            if manga_id not in manga_library:
                manga_library[manga_id] = make_manga_object(manga_object)
            else:
                return {"data": "same id in library, no need to submit", "code": 410}

        # 后台工作交由多线程执行，先返回200
        # Thread(target= confirm_comic_task, args= [manga_id]).start()

        Q.add_task(target=confirm_comic_task, manga_id=manga_id, dtype="0")

        # For thumbnails
        result = thumbnails_creator(manga_library[manga_id])
        manga_library[manga_id] = result

        with open(LIB_PATH, "w", encoding="utf8") as f:
            json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
            f.write(json_tmp)

        return {"data": "submitted", "code": 200}


class DogeLibrary(Resource):
    def post(self):
        global manga_library

        r = [item for item in manga_library.values()]

        return {"data": r, "code": 200}

class Pagination(Resource):
    def post(self):
        global manga_library
        args = lib_post_args.parse_args()
        start = args["start"]
        limit = args["limit"]

        r = [item for item in manga_library.values()]

        pagination = libPagination(
            r,
            "",
            start if start != "" else "1",
            limit if limit else "10",
        )

        return {"data": pagination, "code": 200}


class DogeCurDownloading(Resource):
    def get(self):
        global Current_download

        return {"data": Current_download, "code": 200}


class DogeReZip(Resource):
    def get(self):
        gevent.threading.Thread(target=re_zip_task).start()

        gevent.sleep(0)

        return {"data": "Re zip downloaded document begin", "code": 200}


class DogeShortLib(Resource):
    global manga_library

    def post(self):
        payload = [
            {"manga_id": key, "manga_name": value["manga_name"]}
            for key, value in manga_library.items()
        ]

        return {"data": payload, "code": 200}


class DogeGetManga(Resource):
    def get(self):
        args = request.args
        mangaId = args["manga_id"]

        tempDG = DGmanga(mangaId)
        # session = requests.session()
        chapter_array = tempDG.comic_main_page(mangaId, CF_dict)

        if chapter_array == 501:
            print("查询失败，无法访问指定漫画主页面，返回501")

            return {"data": "error", "code": 501}

        chapter_array = [
            {"chapter_title": item[0], "chapter_link": item[1]}
            for item in chapter_array
        ]

        return {"data": chapter_array, "code": 200}


class DogeReDownload(Resource):
    def post(self):
        args = redownload_post_args.parse_args()
        manga_id = args["manga_id"]
        selected_array = ast.literal_eval(args["selected_array"])
        selected_array = [
            [item["chapter_title"], item["chapter_link"]] for item in selected_array
        ]

        Q.add_task(
            target=download_chapter_task, chapter=[manga_id, selected_array], dtype="1"
        )

        return {"data": "submitted", "code": 200}


class DogeChangeDownload(Resource):
    global manga_library

    def post(self):
        args = change_download_args.parse_args()
        manga_id = args["manga_id"]
        # switch = args["switch"]  # switch = 0: 未完结， switch = 1: 已完结
        print(f"\nDownload switch API is working, manga_id:{manga_id}")

        try:
            switch = manga_library[manga_id]["download_switch"]
            manga_library[manga_id]["download_switch"] = 0 if switch == 1 else 1

            with open(LIB_PATH, "w", encoding="utf8") as f:
                json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
                f.write(json_tmp)

            return {
                "data": {
                    "currentDownloadStatus": manga_library[manga_id]["download_switch"]
                },
                "code": 200,
            }
        except Exception as e:
            print(e)
            return {"data": "May not include this manga id", "code": 404}


class DogeDeleteManga(Resource):
    global manga_library
    global Current_download
    global download_root_folder_path

    def delete(self):
        args = delete_manga_args.parse_args()
        manga_id = args["manga_id"]
        print(f"\nDelete API is working, manga_id:{manga_id}")

        queue_ids = [task["manga_id"] for task in Q.get_all_tasks()]

        if Current_download == manga_id or manga_id in queue_ids:
            return {
                "data": False,
                "code": 434,
            }  # 434: 删除的漫画是当前下载中的或者在队列中，无法删除

        manga_name = manga_library[manga_id]["manga_name"]
        delete_path = f"{download_root_folder_path}/{manga_name}${manga_id}"

        try:
            shutil.rmtree(delete_path)
            del manga_library[manga_id]

            with open(LIB_PATH, "w", encoding="utf8") as f:
                json_tmp = json.dumps(manga_library, indent=4, ensure_ascii=False)
                f.write(json_tmp)

            return {"data": True, "code": 200}
        except Exception as e:
            print(e)
            return {"data": False, "code": 424}


class ThumbnailGetter(Resource):
    def get(self):
        mid = request.args.get("mid")

        try:
            return send_file(f'/vanmanga/thumbnails/{mid}.jpg', mimetype='image/jpeg')
        except Exception as e:
            print(e)
            return {"data": False, "code": 404}


class KavitaStatus(Resource):
    def get(self):
        return {"data": True, "code": 200} if KAVITA_BASE_URL and KAVITA_EXPOSE_URL and KAVITA_ADMIN_APIKEY else {"data": False, "code": 404}


class KavitaLogin(Resource):
    def post(self):
        args = kavita_login_args.parse_args()
        username = args["username"]
        password = args["password"]
        body = {
            "username": username,
            "password": password,
            "apiKey": "",
        }

        print(f"\nKavita Login API is working, username:{username}")

        if KAVITA_BASE_URL == "" or KAVITA_EXPOSE_URL == "":
            return {"data": "No Kavita Configuration, doesn't support login", "code": 434}

        kavitaLoginAPI = "/api/Account/login"
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(f"{KAVITA_BASE_URL}{kavitaLoginAPI}", json=body, headers=headers)
            apiKey = response.json()["apiKey"]
            jwt = response.json()["token"]
            refreshToken = response.json()["refreshToken"]

            loginUrl = f"{KAVITA_EXPOSE_URL}/login?apiKey={apiKey}"

            return {
                "data": {
                    "apiKey": apiKey,
                    "jwt": jwt,
                    "refreshToken": refreshToken,
                    "loginUrl": loginUrl,
                },
                "code": 200,
            }
        except Exception as e:
            print(e)
            return {"data": "Login Failed", "code": 500}


class KavitaRefreshToken(Resource):
    def post(self):
        args = token_refresh_args.parse_args()
        jwt = args["jwt"]
        refreshToken = args["refreshToken"]
        body = {
            "token": jwt,
            "refreshToken": refreshToken,
        }

        if KAVITA_EXPOSE_URL == "":
            return {"data": "No Kavita Configuration, doesn't support refresh token", "code": 434}

        kavitaRefreshTokenAPI = "/api/Account/refresh-token"
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                f"{KAVITA_EXPOSE_URL}{kavitaRefreshTokenAPI}",
                headers=headers,
                json=body,
            )

            jwt = response.json()["token"]
            refreshToken = response.json()["refreshToken"]

            return {
                "data": {
                    "jwt": jwt,
                    "refreshToken": refreshToken,
                },
                "code": 200
            }
        except Exception as e:
            print(e)
            return {"data": "Refresh Token Failed", "code": 500}


def api_loader(api_instance):
    print("########### 初始化API ############")
    api_instance.add_resource(DogeSearch, "/api/dogemanga/search")
    api_instance.add_resource(DogePost, "/api/dogemanga/confirm")
    api_instance.add_resource(DogeLibrary, "/api/dogemanga/lib")
    api_instance.add_resource(DogeCurDownloading, "/api/dogemanga/cdl")
    api_instance.add_resource(DogeReZip, "/api/dogemanga/rezip")
    api_instance.add_resource(DogeShortLib, "/api/dogemanga/shortlib")
    api_instance.add_resource(DogeGetManga, "/api/dogemanga/confirmmanga")
    api_instance.add_resource(DogeReDownload, "/api/dogemanga/redownload")
    api_instance.add_resource(DogeChangeDownload, "/api/dogemanga/downloadswitch")
    api_instance.add_resource(DogeDeleteManga, "/api/dogemanga/deletemanga")
    api_instance.add_resource(ThumbnailGetter, "/api/dogemanga/thumbnail")
    api_instance.add_resource(KavitaStatus, "/api/kavita/status")
    api_instance.add_resource(KavitaLogin, "/api/kavita/login")
    api_instance.add_resource(KavitaRefreshToken, "/api/kavita/refreshtoken")
    api_instance.add_resource(Pagination, "/api/dogemanga/libpagination")
    print("########### API初始化完成 ############")


print("########### 初始化开始 ############")
"""
init TaskQueue to make sure Q run under the Flask context, it works for socketio connection maintaining,
for verify, you can print current thread of this function (won't mainThread)
"""
Q = TaskQueue(num_workers=1)
Q.join()
print("队列已经创建")

gevent.threading.Thread(target=api_loader, args=[api]).start()
gevent.sleep(0)
"""
制作一份manga_library的浅拷贝给初始化扫描使用，因为如果使用多协程上线API的同时进行初始化扫描，用户可能会访问漫画搜索页面并提交任务。
而提交任务时，必然会改变原始manga_library的size，而此时如果初始化扫描正在进行，就会发生错误，因为初始化扫描不能依赖一个已经变化的dict，Python会报错dict的size已经改变。
所以此时生成一份对于manga_library的浅拷贝就是相当于一个初始化扫描前开始的快照，所有在扫描期间加入的新任务自然也不在扫描的范畴内。
初始化扫描只会把它开始的时点前library中所有的manga扫描一遍。这样就做到了既支持搜索和提交的API，同时初始化任务也不会报错。
"""
boot_manga_lib = copy.copy(manga_library)
gevent.threading.Thread(target=boot_scanning, args=[boot_manga_lib]).start()
gevent.sleep(0)

if KAVITA_BASE_URL is not None and KAVITA_EXPOSE_URL is not None and KAVITA_ADMIN_APIKEY is not None:
    kavitaTask()

print("\nbootScanning完成，开始设置计划任务......")
scheduler.add_job(
    id="Dogemanga task", func=dogemangaTask, trigger="cron", hour="1", minute="30"
)
scheduler.add_job(
    id="Kavita_pull", func=kavitaTask, trigger="interval", hours=6
)
scheduler.start()
print("\n计划任务挂载")
print(f"########### 初始化完成 ############")

##ILLYA
# if __name__ == "__main__":
#     print("########### 初始化开始 ############")
#     Q = TaskQueue(num_workers=1)
#     Q.join()
#     print("队列已经创建")

#     gevent.threading.Thread(target=api_loader, args=[api]).start()
#     gevent.sleep(0)
#     boot_manga_lib = copy.copy(manga_library)
#     gevent.threading.Thread(target=boot_scanning, args=[boot_manga_lib]).start()
#     gevent.sleep(0)

#     print("\nbootScanning完成，即将开始安排计划任务上线")
#     scheduler.add_job(
#         id="Dogemanga task", func=dogemangaTask, trigger="cron", hour="1", minute="30"
#     )
#     scheduler.start()
#     print("\n计划任务挂载")
#     print(f"########### 初始化完成 ############")
#     app.run(host="127.0.0.1", port=5000, debug=False)


# call entry function that boot scanning after first self server call
# @app.before_first_request
# def before_first_request():
# print('########### 初始化开始 ############')
# global Q
# Q = TaskQueue(num_workers=1)
# Q.join()
# print('队列已经创建')
# api_loader(api)
# boot_scanning(manga_library)
# # init daily scheduled mission
# print('\nbootScanning完成，即将开始安排计划任务上线')
# scheduler.add_job(id='Dogemanga task', func=dogemangaTask, trigger='cron', hour='1', minute='30')
# scheduler.start()
# print('\n计划任务挂载')
# print(f"########### 初始化完成 ############")


# loop of self server call, run on mainThread, if call success, will terminate thread
# def start_runner():
#     def start_loop():
#         print()
#         not_started = True
#         while not_started:
#             print('In start loop')
#             try:
#                 r = requests.get('http://0.0.0.0:5000/mainpage/searchpage')
#                 if r.status_code == 200:
#                     print('Server started, quiting start_loop')
#                     not_started = False
#                 print(r.status_code)

#             except:
#                 print('Server not yet started')
#             gevent.sleep(1)

#     print('Started runner')
#     thread = threading.Thread(target=start_loop)
#     thread.start()

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
