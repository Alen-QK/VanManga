def libPagination(lib, url, start, limit):

    start = int(start)
    limit = int(limit)
    count = len(lib)

    if count < start or limit < 0:
        return "起始索引不能大于漫画库总长，limit不能小于0"

    object = {}
    object["start"] = start
    object["limit"] = limit
    object["count"] = count

    if start == 1:
        object["previous"] = ""
    else:
        previousStart = max(1, start - limit)
        previousLimit = start - 1
        object["previous"] = {"start": previousStart, "limit": previousLimit}

    if start + limit > count:
        object["next"] = ""
    else:
        nextStart = start + limit
        object["next"] = {"start": nextStart, "limit": limit}

    object["lib_paginate"] = lib[(start - 1) : (start - 1 + limit)]

    return object