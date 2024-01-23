import datetime
from datetime import timezone


def make_manga_object(manga_object):
    object_dict = manga_object
    object_dict["last_epi"] = 1
    object_dict["last_epi_name"] = ""
    object_dict["completed"] = False
    object_dict["serialization"] = 0

    dt = datetime.datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)

    object_dict["add_date"] = utc_time.timestamp()

    return object_dict
