import datetime
from datetime import timezone


def make_manga_object(manga_object):
    object_dict = manga_object
    object_dict["last_epi"] = 1
    object_dict["last_epi_name"] = ""
    object_dict["completed"] = False  # 初次下载是否完成
    object_dict["serialization"] = 0  # 源中真实的连载状态
    object_dict["download_switch"] = 0  # 受控于用户的真实抓取状态

    dt = datetime.datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)

    object_dict["add_date"] = utc_time.timestamp()

    return object_dict
